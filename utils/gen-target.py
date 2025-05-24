#! /usr/bin/env python3
import xml.etree.ElementTree as ET
import pathlib
import re


def split_selection_choices(s:str):
    bra = 0
    result = []
    start = 0
    for i, c in enumerate(s):
        if c == '{':
            bra+=1
        elif c == '}':
            bra -= 1
        if bra == 0 and c == '|':
            result.append(s[start:i])
            start = i + 1
    result.append(s[start:])
    return result


def translate_select(s:str):
    select_pattern = r"%select{"
    m = re.search(select_pattern, s)
    while m:
        interest = s[m.end():]

        bra = 1
        end = 0
        for i, c in enumerate(interest):
            if c == '{':
                bra += 1
            elif c == '}':
                bra -= 1
            if bra == 0:
                end = i
                break
        choices_s = interest[:end]
        p = r"(?<!%)%(?!%)"
        # contain format string?
        if re.search(p, choices_s):
            s = ''
            break
            
        choices = split_selection_choices(choices_s)
        arg_num =  interest[end + 1]
        opts = ''
        for i, c in enumerate(choices):
            opts += f' s{i}=|{c}|'
        s = s.replace(f'%select{{{choices_s}}}{arg_num}', f'{{$arg{arg_num} :select{opts}}}')
        m = re.search(select_pattern, s)
    return s


def translate_var(s):
    return re.sub(r"%(\d+)", r"{$arg\1}", s)


def translate_quoted(s):
    return re.sub(r"%quoted(\d+)", r"{$arg\1 :quote}", s)


def translate_q(s):
    return re.sub(r"%q(\d+)", r"{$arg\1 :q}", s)


def translate_percent(s: str):
    return s.replace(r"%%", "%")

def translate_human(s:str):
    return re.sub(r'%human(\d+)', r'{$arg\1 :number compactDisplay=short notation=compact}', s)

def translate_backslash(s:str):
    return s.replace('\\', '\\\\')

def translate_brackets(s:str):
    result = s.replace("'{'", "'\\{'")
    return result.replace("'}'", "'\\}'")

def translate(s):
    result = translate_backslash(s)
    result = translate_brackets(result)
    result = translate_select(result)
    result = translate_var(result)
    result = translate_q(result)
    result = translate_percent(result)
    result = translate_human(result)
    return result


def handle_xliff(f):
    ET.register_namespace("", "urn:oasis:names:tc:xliff:document:2.1")
    xlf = ET.parse(f)
    ns = {"xliff": "urn:oasis:names:tc:xliff:document:2.1"}
    group = xlf.find("./xliff:file/xliff:group", ns)
    units = group.findall("./xliff:unit", ns)
    for unit in units:
        source = unit.find("./xliff:segment/xliff:source", ns)
        target = unit.find("./xliff:segment/xliff:target", ns)
        target.text = translate(source.text)

    xlf.write(
        f"{f}", encoding="UTF-8", xml_declaration=True, short_empty_elements=False
    )


xliffs = pathlib.Path("xliff/en/US").glob("*.xlf")
for f in xliffs:
    handle_xliff(f)
