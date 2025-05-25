# LLVM i18n

# Utilities

## WARNING

**All utilities are buggy! Project directory should be the only working directory!**

## gen-xliff.py

Requires: libclang python binding

Generate empty xliff from clang headers.

- `-I` add additional include path
- `--trg-lang` target language, with format IETF language tag, e.g. en-US.
  Will generate xlf files in `root/&lt;language&gt;/*.xlf`, in which `lt;language&gt;`
  is the value of `--trg-lang` replace `-` by directory separator.

## update-xliff.py
Update pre-exist xlf files.
Requires: libclang python binding
- `--inreplace` overwrite the file, without backup. By default, it will generate backup file.
- `--trg-lang` target language.

## xliff2icu.py
Generate ICU resource file.

It generates strings as an icu [array](https://unicode-org.github.io/icu/userguide/locale/resources.html#resources-syntax). Because ICU uses UTF-16 and LLVM uses UTF-8, we should
embed strings as raw binary values... So we can use [`getBinary`](https://unicode-org.github.io/icu-docs/apidoc/dev/icu4c/classicu_1_1ResourceBundle.html#aaae2b651bb12140df26afedcc841592a)
without generate `UnicodeString` and compatible with llvm's `StringRef`, all strings are terminated with null byte (0x00).

# Translations
All string in the target field should be valid text in DSL defined by message format 2.0.

# Custom functions as replacement

- %select{pattern0|pattern1|...}
  `message {$arg0 :select s0=|seleciton 1| s1=|selection 1| ...}`
- %objcclass
  `method {$arg0 :objcclass} not found`
- %objcinstance
  `method {$arg0 :objcinstance} not found`
- %q
  `candidate found by name lookup is {$arg0 :q}`
- %human, depends on context, use :unit or :integer with options
  `need extra {$arg0 :unit unit=byte}`
- %diff
  `{$arg0 :diff with=$arg1}`

Extra helper functions:
- :format
  `{|a literal with MF2 format string| :format arg0=$arg0 ...}`
  This is a hack!
