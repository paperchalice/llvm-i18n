#! /usr/bin/env python3
import xml.etree.ElementTree as ET

from extractor import COMPONENT_LIST
import argparse
from pathlib import Path
import os

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

def process_str(s):
  s = s.replace('"', '\\"').replace('\\', '\\\\').replace('\n', '"\n    "')
  return f'"{s}"'

class Converter:
  def __init__(self, component):
    self.component = component
    input_dir = 'root'/Path(args.trg_lang.replace('-', '/'))
    file_name = input_dir/f'Diagnostic{component}Kinds.xlf'
    self.file_name = file_name
    ET.register_namespace('', 'urn:oasis:names:tc:xliff:document:2.0')
    self.xlf = ET.parse(file_name)

  def generate(self):
    ns = {
      'xliff': 'urn:oasis:names:tc:xliff:document:2.0'
    }
    units = self.xlf.findall('./xliff:file/xliff:group/xliff:unit', ns)
    string_list = []
    for unit in units:
      tgt = unit.find('./xliff:segment/xliff:target', ns)
      if tgt.text:
        string_list.append(process_str(tgt.text))
      else:
        string_list.append("")
    return string_list

def handle_component(component):
  converter = Converter(component)
  return converter.generate()

def main():
  string_list = []
  for c in COMPONENT_LIST:
    string_list += handle_component(c)
  lang = args.trg_lang.replace('-', '_')
  if lang == 'en_US':
    lang = 'root'
  strings = ',\n    '.join(string_list)
  out_txt = TXT_TEMPLATE.format(lang=lang, strings=strings)

  Path('build').mkdir(exist_ok=True)
  out_file = Path(f'build/{lang}.txt')
  # With BOM so genrb can recognize it.
  with open(out_file, 'w+', encoding='utf-8-sig') as f:
    f.write(out_txt)
  

if __name__ == "__main__":
  main()
