#! /usr/bin/env python3
import langs
import xml.etree.ElementTree as ET

import argparse
from pathlib import Path
import os
import locale
import itertools

parser = argparse.ArgumentParser(description='Example argparse script.')
parser.add_argument('--trg-lang', required=True, type=str, help='target language')
parser.add_argument('--lang-dir', type=Path, help='Dir contains language, default is pwd')
parser.add_argument('--out-dir', default='icures', help='Dir contains output txt')
args = parser.parse_args()

_project_dir = Path(__file__).parent.parent

TXT_TEMPLATE = '''// Automatically generated file, do not edit directly!
{lang}:table {{
  DiagInfoDescriptionStringTable:array {{
    {strings}
  }}
}}
'''

EMPTY_TEMPLATE = '''// Automatically generated file, do not edit directly!
{lang}:table {{}}
'''

def to_icu_bin(txt):
  if txt is None:
    return ':bin { 00 }'
  return f':bin {{ {txt.encode("utf-8").hex()}00 }}'

class Converter:
  def __init__(self, lang):
    self.lang = lang
    input_dir = f'{_project_dir}/xliff'/Path(lang.replace('-', '/'))
    self.input_dir = input_dir
    self.xlfs = []
    if not input_dir.exists():
      return

    ET.register_namespace('', 'urn:oasis:names:tc:xliff:document:2.0')
    xlfs = input_dir.glob('*.xlf')
    for xlf in xlfs:
      self.xlfs.append(ET.parse(xlf))

  def generate(self):
    under_score_lang = self.lang.replace('-', '_')
    if len(self.xlfs) == 0:
      out_file = Path(f'{args.out_dir}/{under_score_lang}.txt')
      with open(out_file, 'w+', encoding='utf-8-sig') as f:
        f.write(EMPTY_TEMPLATE.format(lang=under_score_lang))
      return
    ns = {
      'xliff': 'urn:oasis:names:tc:xliff:document:2.0'
    }
    string_list = []
    for xlf in self.xlfs:
      units = xlf.findall('./xliff:file/xliff:group/xliff:unit', ns)
      for unit in units:
        tgt = unit.find('./xliff:segment/xliff:target', ns)
        string_list.append(to_icu_bin(tgt.text))

    strings = ',\n    '.join(string_list)
    out_txt = TXT_TEMPLATE.format(lang=under_score_lang, strings=strings)
    # With BOM so genrb can recognize it.
    out_file = Path(f'{args.out_dir}/{under_score_lang}.txt')
    with open(out_file, 'w+', encoding='utf-8-sig') as f:
      f.write(out_txt)

def gen_for_lang(lang:str):
  lang.split('-')
  lang_list = itertools.accumulate(lang.split('-'), lambda a, b: a + '-' + b )
  for lang in lang_list:
    converter = Converter(lang)
    converter.generate()


def main():
  langs = args.trg_lang.split(',')
  if args.trg_lang.upper() == 'ALL':
    langs = langs.ALL_LANGS

  Path(args.out_dir).mkdir(exist_ok=True)
  for lang in langs:
    gen_for_lang(lang)

if __name__ == "__main__":
  main()
