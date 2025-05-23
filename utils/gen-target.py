#! /usr/bin/env python
import xml.etree.ElementTree as ET
import pathlib
import re


def translate_select(s):
    select_pattern = r"%select{([^{]+)}(\d+)"

    def handle_choice(m: re.Match):
        g1:str = m.group(1)
        choices = g1.split('|')
        choices_str = ""
        for i, c in enumerate(choices):
            choices_str += f' s{i}=|{c}|'
        return f"{{$arg{m.group(2)} :select{choices_str}}}"

    result = re.sub(select_pattern, handle_choice, s)
    return result


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
    ET.register_namespace("", "urn:oasis:names:tc:xliff:document:2.2")
    xlf = ET.parse(f)
    ns = {"xliff": "urn:oasis:names:tc:xliff:document:2.2"}
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
