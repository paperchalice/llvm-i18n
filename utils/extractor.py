import clang.cindex

SRC_TEMPLATE = '''
#include "clang/Basic/Diagnostic{component}.h"

enum Diagnostic{component}Kinds {{

#define DIAG(ENUM, FLAGS, DEFAULT_MAPPING, DESC, GROUP, SFINAE, NOWERROR,      \\
             SHOWINSYSHEADER, SHOWINSYSMACRO, DEFERRABLE, CATEGORY)            \\
  ENUM = clang::diag::ENUM,
#include "clang/Basic/Diagnostic{component}Kinds.inc"
#undef DIAG
}};

namespace Desc {{
const char *descs[] = {{
#define DIAG(ENUM, FLAGS, DEFAULT_MAPPING, DESC, GROUP, SFINAE, NOWERROR,      \\
             SHOWINSYSHEADER, SHOWINSYSMACRO, DEFERRABLE, CATEGORY)            \\
  DESC,
#include "clang/Basic/Diagnostic{component}Kinds.inc"
#undef DIAG
}};
}}
'''

class DiagInfo:
  def __init__(self, value, spelling, desc):
    self.value = value
    self.spelling = spelling
    self.desc = desc
  def __repr__(self):
    return f'{self.spelling}: {self.value}: {self.desc}'

class Extractor:
  enums_map = {}
  def __init__(self, component):
    self._component = component
    self.enums: list[DiagInfo] = []
    self._should_add = False
    self._enum_idx = 0

  def extract_enums(self, cursor):
    match cursor.kind:
      case clang.cindex.CursorKind.TRANSLATION_UNIT:
        for child in cursor.get_children():
          self.extract_enums(child)
      case clang.cindex.CursorKind.ENUM_DECL:
        if cursor.spelling == f'Diagnostic{self._component}Kinds':
          self._should_add = True
          for child in cursor.get_children():
            self.extract_enums(child)
      case clang.cindex.CursorKind.ENUM_CONSTANT_DECL:
        if self._should_add:
          self.enums.append(DiagInfo(cursor.enum_value, cursor.spelling, ''))
      case _:
        if self._should_add:
          for child in cursor.get_children():
            self.extract_enums(child)


  def process_desc(self, s):
    return bytes(s[1:-1], "utf-8").decode("unicode_escape")

  # Call after extract_enums
  def extract_descs(self, cursor):
    match cursor.kind:
      case clang.cindex.CursorKind.STRING_LITERAL:
        if self._should_add:
          self.enums[self._enum_idx].desc = self.process_desc(cursor.spelling)
          self._enum_idx += 1
      case clang.cindex.CursorKind.NAMESPACE:
        if cursor.spelling == 'Desc':
          self._should_add = True
          for child in cursor.get_children():
            self.extract_descs(child)
      case _:
        for child in cursor.get_children():
          self.extract_descs(child)

  def extract(self, clang_args):
    if self._component in Extractor.enums_map:
      self.enums =  Extractor.enums_map[self._component]
      return
    src = SRC_TEMPLATE.format(component=self._component)
    index = clang.cindex.Index.create()
    translation_unit = index.parse(f'src.cpp', args=clang_args,
                                    unsaved_files=[('src.cpp', src)])
    cursor = translation_unit.cursor
    self.extract_enums(cursor)
    self._should_add = False
    self.extract_descs(cursor)
    Extractor.enums_map[self._component] = self.enums

# Sync order with clang/lib/Basic/DiagnosticIDs.cpp: StaticDiagInfo[].
COMPONENT_LIST = [
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
