#! /usr/bin/env python3

from extractor import Extractor, COMPONENT_LIST
import argparse
from pathlib import Path
import os
import time
import xml.etree.ElementTree as ET
import warnings
import copy

parser = argparse.ArgumentParser(description='Example argparse script.')
parser.add_argument('--clang-prefix', type=Path, help='clang prefix directory.')
parser.add_argument('--llvm-prefix', type=Path, help='LLVM prefix directory')
parser.add_argument('--trg-lang', required=True, type=str, help='target language')
parser.add_argument('--inreplace', '-i', help='Inreplace mode, without backup.')
args = parser.parse_args()

class Updater:
  def __init__(self, component: str):
    self.component = component
    input_dir = Path(args.trg_lang.replace('-', '/'))

    file_name = 'root'/input_dir/f'Diagnostic{component}Kinds.xlf'
    self.file_name = file_name
    ET.register_namespace('', 'urn:oasis:names:tc:xliff:document:2.0')
    self.xlf = ET.parse(file_name)
  
  def extract(self):
    extractor = Extractor(self.component)
    clang_args = ['-std=c++17']
    if args.clang_prefix:
      clang_args.append(f'-I{args.clang_prefix/'include'}')
    if args.llvm_prefix:
      clang_args.append(f'-I{args.llvm_prefix/'include'}')
    extractor.extract(clang_args)
    self.enums = extractor.enums
  
  def update(self):
    self.extract()
    xlf_copy = copy.deepcopy(self.xlf)
    ns = {
      'xliff': 'urn:oasis:names:tc:xliff:document:2.0'
    }
    group = xlf_copy.find('./xliff:file/xliff:group', ns)
    units = group.findall('./xliff:unit', ns)
    for unit in units:
      group.remove(unit)
    for e in self.enums:
      units = [u for u in units if u.attrib['name'] == e.spelling]
      if len(units) == 1:
        unit = units[0]
        unit.attrib['id'] = str(e.value)
        source = unit.find('./xliff:segment/xliff:source', ns)
        if source.text != e.desc:
          source.text = e.desc
          source.attrib['state'] = 'initial'
        group.append(unit)
      elif len(units) == 0:
        unit_attr = {
          'id': str(e.value),
          'name': e.spelling
        }
        unit = ET.SubElement(group, 'unit', **unit_attr)
        segment = ET.SubElement(unit, 'segment')
        source = ET.SubElement(segment, 'source')
        source.text = e.desc
        ET.SubElement(segment, 'target')
    os.rename(self.file_name, f'{self.file_name}-{int(time.time())}.bak')
    with open(self.file_name, "wb") as xml_file:
        ET.indent(xlf_copy)
        xlf_copy.write(xml_file, encoding="UTF-8", xml_declaration=True, short_empty_elements=False)
    return
      



def handle_component(component):
  try:
    updater = Updater(component)
    updater.update()
  except FileNotFoundError:
    warnings(f'xlf for component "{component}" not found!')
  

def main():
  for c in COMPONENT_LIST:
    handle_component(c)

if __name__ == "__main__":
  main()

