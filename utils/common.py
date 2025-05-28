from icu import Locale
from langcodes import standardize_tag
import pathlib
import xml.etree.ElementTree as ET


ICU_LOCALES = list(Locale.getAvailableLocales().keys())
BCP47_LOCALES = [standardize_tag(l) for l in ICU_LOCALES]
ICU_LOCALES.append("root")
BCP47_LOCALES.append("root")

# Sync order with clang/lib/Basic/DiagnosticIDs.cpp: StaticDiagInfo[].
COMPONENT_LIST = [
    "Common",
    "Driver",
    "Frontend",
    "Serialization",
    "Lex",
    "Parse",
    "AST",
    "Comment",
    "CrossTU",
    "Sema",
    "Analysis",
    "Refactoring",
    "InstallAPI",
]


def get_icu_locale(l):
    if l == "root":
        return l
    return Locale(l).getName()


def get_bcp47_locale(l):
    if l == "root":
        return l
    return standardize_tag(l)


PROJECT_ROOT = pathlib.Path(__file__).parent.parent.resolve()
TEMPLATE_XLIFF_LIST = (PROJECT_ROOT / "template").glob("*.xlf")

ET.register_namespace('', 'urn:oasis:names:tc:xliff:document:2.0')
