import xml.etree.ElementTree as ET
from pathlib import Path

# Sync order with clang/lib/Basic/DiagnosticIDs.cpp: StaticDiagInfo[].
_COMPONENT_LIST = [
  'Comment',
  'Driver',
  'Frontend',
  'Serialization',
  'Lex',
  'Parse',
  'AST',
  'Common',
  'CrossTU',
  'Sema',
  'Analysis',
  'Refactoring',
  'InstallAPI',
]

_enums = {}
for c in _COMPONENT_LIST:
  _enums[c] = []

class DiagInfo:
  def __init__(self, value, spelling, desc):
    self.value = value
    self.spelling = spelling
    self.desc = desc
  def __repr__(self):
    return f'{self.spelling}: {self.value}: {self.desc}'

class Extractor:
  _extracted = False
  def __init__(self):
    self._enum_idx = 0

  def _extract(self, cursor):
    return

  def _process_desc(self, s):
    return bytes(s[1:-1], "utf-8").decode("unicode_escape")
  
  def _extract_component(self):
    xlf = Path(f'template/Diagnostic{self._component}Kinds.xlf')
    
    self._extract()

  def extract(self):
    if not Extractor._extracted:
      for c in _COMPONENT_LIST:
        print(f'Extract for component: {c}...')
        self._enums = []
        self._enum_idx = 0
        self._component = c
        self._extract_component()
        _enums[c] = self._enums
      Extractor._extracted = True
  
  def get_result(self):
    return _enums
