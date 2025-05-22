#! /usr/bin/env python3

from extractor import Extractor
import argparse
from pathlib import Path
import os
import time
import xml.etree.ElementTree as ET
import pathlib
import common
import copy

parser = argparse.ArgumentParser(description='Example argparse script.')
parser.add_argument('-I', type=pathlib.Path, action='append', help='clang source prefix directory')
parser.add_argument('--trg-lang', required=True, type=str, nargs='+', help='target language')
parser.add_argument('--inreplace', '-i', action='store_true', help='Inreplace mode, without backup.')
args = parser.parse_args()

class Updater:
  def __init__(self, extractor:Extractor, trg_lang:str):
    self._extractor = extractor
    self._extract_result = self._extractor.get_result()
    input_dir = Path(trg_lang.replace('_', '/'))
    self._file_names = {}
    self.trg_lang = trg_lang
    self._xlfs = {}
    if not ('xliff'/input_dir).exists():
      return
    elif not list(('xliff'/input_dir).glob('*.xlf')):
      return
    ET.register_namespace('', 'urn:oasis:names:tc:xliff:document:2.2')
    for c in self._extract_result:
      file_name = 'xliff'/input_dir/f'Diagnostic{c}Kinds.xlf'
      self._file_names[c] = file_name
      self._xlfs[c] = ET.parse(file_name)
  
  def _update_for_component(self, component):
    if len(self._xlfs) == 0:
      return
    xlf_copy = copy.deepcopy(self._xlfs[component])
    ns = {
      'xliff': 'urn:oasis:names:tc:xliff:document:2.2'
    }
    group = xlf_copy.find('./xliff:file/xliff:group', ns)
    units = group.findall('./xliff:unit', ns)
    for unit in units:
      group.remove(unit)
    for e in self._extract_result[component]:
      tu = [u for u in units if u.attrib['name'] == e.spelling]
      if len(tu) == 1:
        unit = tu[0]
        unit.attrib['id'] = str(e.value)
        source = unit.find('./xliff:segment/xliff:source', ns)
        if source.text != e.desc:
          source.text = e.desc
          source.attrib['state'] = 'initial'
        group.append(unit)
      elif len(tu) == 0:
        unit_attr = {
          'id': str(e.value),
          'name': e.spelling
        }
        unit = ET.SubElement(group, 'unit', **unit_attr)
        segment = ET.SubElement(unit, 'segment')
        source = ET.SubElement(segment, 'source')
        source.text = e.desc
        ET.SubElement(segment, 'target')
    file_name = self._file_names[component]
    if not args.inreplace:
      os.rename(file_name, f'{file_name}-{int(time.time())}.bak')
    with open(file_name, "wb") as xml_file:
        ET.indent(xlf_copy)
        xlf_copy.write(xml_file, encoding="UTF-8", xml_declaration=True, short_empty_elements=False)
        print(f'update done for {self.trg_lang}')
    return
  
  def update(self):
    for c in self._extract_result:
      self._update_for_component(c)
      
  

def main():
  clang_args = ['-std=c++17']
  if args.I:
    for i in args.I:
      clang_args.append(f'-I{i}')
  extractor = Extractor()
  extractor.extract(clang_args)
  all_langs = args.trg_lang
  if args.trg_lang[0].upper() == 'ALL':
    all_langs = common.ICU_LOCALES

  for l in all_langs:
    print(f'update for language {l}')
    updater = Updater(extractor, l)
    updater.update()
  

if __name__ == "__main__":
  main()

