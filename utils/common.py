from icu import Locale
from langcodes import standardize_tag


ICU_LOCALES = list(Locale.getAvailableLocales().keys())
BCP47_LOCALES = [standardize_tag(l) for l in ICU_LOCALES]
ICU_LOCALES.append('root')
BCP47_LOCALES.append('root')

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

def get_icu_locale(l):
    if l == 'root':
        return l
    return Locale(l).getName()

def get_bcp47_locale(l):
    if l == 'root':
        return l
    return standardize_tag(l)
