#! /usr/bin/env python3
import xml.etree.ElementTree as ET

from extractor import COMPONENT_LIST
import argparse
from pathlib import Path
import locale
import binascii

parser = argparse.ArgumentParser(description='Example argparse script.')
parser.add_argument('--trg-lang', required=True, type=str, help='target language')
parser.add_argument('--lang-dir', type=Path, help='Dir contains language, default is pwd')
args = parser.parse_args()

TXT_TEMPLATE = '''// Automatically generated file, do not edit directly!
{lang}:table {{
  DiagInfoDescriptionStringTable:array {{
    {strings}
  }}
}}
'''

def to_icu_bin(txt):
  if txt is None:
    return ':bin { 00 }'
  return f':bin {{ {txt.encode("utf-8").hex()}00 }}'

class Converter:
  def __init__(self, lang):
    self.lang = lang
    input_dir = 'root'/Path(lang.replace('-', '/'))
    self.xlfs = []
    if not input_dir.is_dir():
      return
    for c in COMPONENT_LIST:
      file_name = input_dir/f'Diagnostic{c}Kinds.xlf'
      self.xlfs.append(ET.parse(file_name))
    ET.register_namespace('', 'urn:oasis:names:tc:xliff:document:2.0')

  def generate(self):
    if len(self.xlfs) == 0:
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

    lang = self.lang.replace('-', '_')
    if lang == 'en_US':
      lang = 'root'
    strings = ',\n    '.join(string_list)
    out_txt = TXT_TEMPLATE.format(lang=lang, strings=strings)
    # With BOM so genrb can recognize it.
    Path('icures').mkdir(exist_ok=True)
    out_file = Path(f'icures/{lang}.txt')
    with open(out_file, 'w+', encoding='utf-8-sig') as f:
      f.write(out_txt)


def main():
  if args.trg_lang.upper() == 'ALL':
    for win_locale in locale.windows_locale.values():
      win_locale = win_locale.replace('_', '-')
      converter = Converter(win_locale)
      converter.generate()
    return
  converter = Converter(args.trg_lang)
  converter.generate()

if __name__ == "__main__":
  main()
