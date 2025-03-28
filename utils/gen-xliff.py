#! /usr/bin/env python3

import pathlib
from extractor import DiagInfo, Extractor
import os
from pathlib import Path
import argparse
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser(description='Example argparse script.')
parser.add_argument('--clang-prefix', type=pathlib.Path, help='clang prefix directory.')
parser.add_argument('--llvm-prefix', type=pathlib.Path, help='LLVM prefix directory')
parser.add_argument('--trg-lang', type=str, required=True, help='target language')
args = parser.parse_args()

class XmlGenerator:
  def __init__(self, trg_lang, component):
    self.trg_lang = trg_lang
    self.component = component
  
  def generate(self, enums:list[DiagInfo]):
    xliff_attr = {
      'xmlns': 'urn:oasis:names:tc:xliff:document:2.2',
      'xmlns:xsi': 'http://www.w3.org/2001/XMLSchema-instance',
      'version': '2.2',
      'srcLang': 'en-US',
      'trgLang': args.trg_lang,
      'xsi:schemaLocation': 'https://docs.oasis-open.org/xliff/xliff-core/v2.2/schemas/xliff_core_2.2.xsd'
    }
    
    xliff = ET.Element("xliff", **xliff_attr)

    file_attr = {
      'id': f'Diagnostic{self.component}',
      'original': f'clang/Basic/Diagnostic{self.component}Kinds.inc'
    }
    file = ET.SubElement(xliff, 'file', **file_attr)
    notes = ET.SubElement(file, 'notes')
    note = ET.SubElement(notes, 'note', appliesTo='source')
    note.text = '''Automatically generated file, do not edit directly!'''
    group = ET.SubElement(file, 'group', id=self.component)
    for e in enums:
      unit_attr = {
        'id': str(e.value),
        'name': e.spelling
      }
      unit = ET.SubElement(group, 'unit', **unit_attr)
      segment_attr = {
        'state': 'initial'
      }
      segment = ET.SubElement(unit, 'segment', segment_attr)
      source = ET.SubElement(segment, 'source')
      source.text = e.desc
      ET.SubElement(segment, 'target')
    xml_tree = ET.ElementTree(xliff)
    ET.indent(xml_tree)

    output_dir = 'xliff'/Path(args.trg_lang.replace('-', '/'))
    os.makedirs(output_dir, exist_ok=True)
    with open(output_dir/f"Diagnostic{self.component}Kinds.xlf", "wb") as xml_file:
        xml_tree.write(xml_file, encoding="UTF-8", xml_declaration=True, short_empty_elements=False)
    return

def main():
  clang_args = ['-std=c++17']
  if args.clang_prefix:
    clang_args.append(f'-I{args.clang_prefix/'include'}')
  if args.llvm_prefix:
    clang_args.append(f'-I{args.llvm_prefix/'include'}')
  extractor = Extractor()
  extractor.extract(clang_args)
  result = extractor.get_result()
  for k, v in result.items():
    generator = XmlGenerator(args.trg_lang, k)
    generator.generate(v)

if __name__ == "__main__":
  main()
