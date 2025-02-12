import clang.cindex

_SRC_TEMPLATE = '''
#include "clang/Basic/Diagnostic{component}.h"

namespace Desc {{

enum Diagnostic{component}Kinds {{

#define DIAG(ENUM, FLAGS, DEFAULT_MAPPING, DESC, GROUP, SFINAE, NOWERROR,      \\
             SHOWINSYSHEADER, SHOWINSYSMACRO, DEFERRABLE, CATEGORY)            \\
  ENUM = clang::diag::ENUM,
#include "clang/Basic/Diagnostic{component}Kinds.inc"
#undef DIAG
}};

const char *descs[] = {{
#define DIAG(ENUM, FLAGS, DEFAULT_MAPPING, DESC, GROUP, SFINAE, NOWERROR,      \\
             SHOWINSYSHEADER, SHOWINSYSMACRO, DEFERRABLE, CATEGORY)            \\
  DESC,
#include "clang/Basic/Diagnostic{component}Kinds.inc"
#undef DIAG
}};

}} // namespace Desc
'''

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
    match cursor.kind:
      case clang.cindex.CursorKind.TRANSLATION_UNIT:
        for child in cursor.get_children():
          self._extract(child)
      case clang.cindex.CursorKind.NAMESPACE:
        if cursor.spelling != 'Desc':
          return
        for child in cursor.get_children():
          self._extract(child)
      case clang.cindex.CursorKind.ENUM_DECL:
        if cursor.spelling == f'Diagnostic{self._component}Kinds':
          for child in cursor.get_children():
            self._extract(child)
      case clang.cindex.CursorKind.ENUM_CONSTANT_DECL:
        self._enums.append(DiagInfo(cursor.enum_value, cursor.spelling, ''))
      case clang.cindex.CursorKind.VAR_DECL:
        if cursor.spelling != 'descs':
          return
        for child in cursor.get_children():
          self._extract(child)
      case clang.cindex.CursorKind.INIT_LIST_EXPR:
        for child in cursor.get_children():
          self._extract(child)
      case clang.cindex.CursorKind.STRING_LITERAL:
        self._enums[self._enum_idx].desc = self._process_desc(cursor.spelling)
        self._enum_idx += 1
      case _:
        return

  def _process_desc(self, s):
    return bytes(s[1:-1], "utf-8").decode("unicode_escape")
  
  def _extract_component(self, clang_args):
    src = _SRC_TEMPLATE.format(component=self._component)
    index = clang.cindex.Index.create()
    translation_unit = index.parse(f'src.cpp', args=clang_args,
                                    unsaved_files=[('src.cpp', src)])
    cursor = translation_unit.cursor
    self._extract(cursor)

  def extract(self, clang_args):
    if not Extractor._extracted:
      for c in _COMPONENT_LIST:
        print(f'Extract for component: {c}...')
        self._enums = []
        self._enum_idx = 0
        self._component = c
        self._extract_component(clang_args)
        _enums[c] = self._enums
      Extractor._extracted = True
  
  def get_result(self):
    return _enums
