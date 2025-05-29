#! /usr/bin/env python3
import xml.etree.ElementTree as ET

import argparse
from pathlib import Path
from common import *
import itertools

parser = argparse.ArgumentParser(description="Example argparse script.")
parser.add_argument(
    "--trg-lang", required=True, type=str, nargs="+", help="target language"
)
parser.add_argument(
    "--lang-dir", type=Path, help="Dir contains language, default is pwd"
)
parser.add_argument("--out-dir", default="icures", help="Dir contains output txt")
args = parser.parse_args()

_project_dir = Path(__file__).parent.parent

TXT_TEMPLATE = """// Automatically generated file, do not edit directly!
{lang}:table {{
  Basic:table {{
    SubstString:table {{
      {subst_strings}
    }}
    DiagString:table {{
      {diag_strings}
    }}
  }}
}}
"""

EMPTY_TEMPLATE = """// Automatically generated file, do not edit directly!
{lang}:table {{}}
"""


def to_icu_bin(name, txt):
    return f'{name}:bin {{ {txt.encode("utf-8").hex()}00 }}'


class Converter:
    def __init__(self, lang: str):
        self.lang = lang
        self.xlfs = (PROJECT_ROOT / f"xliff/{lang.replace('-', '/')}").glob("*.xlf")

    def generate(self):
        under_score_lang = get_icu_locale(self.lang)
        if not self.xlfs:
            out_file = Path(f"{args.out_dir}/{under_score_lang}.txt")
            with open(out_file, "w+", encoding="utf-8-sig") as f:
                f.write(EMPTY_TEMPLATE.format(lang=under_score_lang))
            return
        ns = {"": "urn:oasis:names:tc:xliff:document:2.0"}
        subst_string_list = []
        diag_string_list = []
        for xlf_file in self.xlfs:
            xlf = ET.parse(xlf_file)
            for unit in xlf.findall('./file/group[@id="TextSubstitution"]/unit', ns):
                tgt = unit.find("./segment/target", ns)
                name = unit.get("id")
                if tgt.text:
                    subst_string_list.append(to_icu_bin(name, tgt.text))
            for unit in xlf.findall('./file/group[@id="Diagnostic"]/unit', ns):
                tgt = unit.find("./segment/target", ns)
                name = unit.get("id")
                if tgt.text:
                    diag_string_list.append(to_icu_bin(name, tgt.text))

        subst_strings = "\n      ".join(subst_string_list)
        diag_strings = "\n      ".join(diag_string_list)
        out_txt = TXT_TEMPLATE.format(
            lang=under_score_lang,
            subst_strings=subst_strings,
            diag_strings=diag_strings,
        )
        # With BOM so genrb can recognize it.
        out_file = Path(f"{args.out_dir}/{under_score_lang}.txt")
        with open(out_file, "w+", encoding="utf-8-sig") as f:
            f.write(out_txt)


def gen_for_lang(lang: str):
    lang_list = itertools.accumulate(lang.split("-"), lambda a, b: a + "-" + b)
    for lang in lang_list:
        converter = Converter(lang)
        converter.generate()


def main():
    if args.trg_lang[0] == "all":
        langs = BCP47_LOCALES
    else:
        langs = map(get_bcp47_locale, args.trg_lang)

    Path(args.out_dir).mkdir(exist_ok=True)
    for lang in langs:
        gen_for_lang(lang)


if __name__ == "__main__":
    main()
