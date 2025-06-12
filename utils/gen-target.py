#! /usr/bin/env python3
import xml.etree.ElementTree as ET
import pathlib
import re
# from common import *
import sys
from typing import List
from dataclasses import dataclass
import functools
import operator

from lark import Lark, ast_utils, Transformer, v_args
from lark.tree import Meta
from lark import Lark, tree, Transformer, Visitor

this_module = sys.modules[__name__]

class _Ast(ast_utils.Ast):
    def is_trivial(self):
        return True
    pass

@dataclass
class Literal(_Ast):
    s:str
@dataclass
class Placeholder(_Ast):
    n:int
@dataclass
class OrdinalFormat(_Ast):
    n:int
@dataclass
class OjbcinstanceFormat(_Ast):
    n:int
@dataclass
class ObjcclassFormat(_Ast):
    n:int
@dataclass
class ObjcinstanceFormat(_Ast):
    n:int
@dataclass
class QFormat(_Ast):
    n:int
@dataclass
class HumanFormat(_Ast):
    n:int
@dataclass
class QuotedFormat(_Ast):
    n:int
@dataclass
class SFormat(_Ast):
    n:int
@dataclass
class SubFormat(_Ast):
    target:str
    args:list[int]
    def __init__(self, t, *args):
        self.target = t
        self.args = list(args)
@dataclass(init=False)
class SelectFormat(_Ast):
    n:int
    choices:list[object]
    def __init__(self, *args):
        arg_list = list(args)
        self.n = arg_list.pop()
        self.choices = arg_list
    def is_trivial(self) -> bool:
        return all(map(lambda n:isinstance(n, Literal) or isinstance(Placeholder), self.choices))
@dataclass(init=False)
class EnumSelectFormat(_Ast):
    n:int
    enum:str
    choices:dict
    def __init__(self, enum, *args):
        arg_list = list(args)
        self.n = arg_list.pop()
        self.enum = enum
        self.choices = functools.reduce(operator.or_, arg_list, {})
@dataclass
class DiffFormat(_Ast):
    msg:object
    tree_msg:object
    a:int
    b:int
@dataclass(init=False)
class PluralFormat(_Ast):
    table:dict
    n:int
    def __init__(self, *args):
        arg_list = list(args)
        self.n = arg_list.pop()
        self.table = functools.reduce(operator.or_, arg_list, {})
    def is_trivial(self):
        for v in self.table.values():
            if not v.is_trivial():
                return False
        return True

def is_trivial(t) -> bool:
    if isinstance(t, list):
        return all(map(lambda n:n.is_trivial(), t))
    return t.is_trivial()
        

class ToAst(Transformer):
    def ARG_NO(self, n):
        return int(n)
    def NUM(self, n):
        return int(n)
    def LITERAL(self, s):
        return str(s)
    def ID(self, s):
        return str(s)
    def range(self, items):
        return range(items[0], items[1]+1)
    def BRA(self, n):
        return str(n)
    def CES(self, n):
        return str(n)
    def VBAR(self, n):
        return str(n)
    def PERCENT(self, n):
        return '%'
    
    def select_format(self, items):
        print(items)
    def enum_selection(self, items):
        return {str(items[0]) : items[1]}
    def message(self, m):
        if isinstance(m, list) and len(m) == 0:
            return ''
        return m
    def plural_choice(self, items):
        if len(items) == 1:
            return {'*' : items[0]}
        return {items[0] : items[1]}
    def plural_cond(self, items):
        if len(items) == 1:
            return items[0]
        if len(items) == 2:
            return (items[0], items[1])
        return items

class ToMF2:
    def __init__(self, nl = 0):
        self.result = ''
        self.vars = set()
        self.nest_level = nl
        def cnt(n):
            if n == 0:
                return 0
            return 2*cnt(n-1) + 1
        self.vbar = '\\' * cnt(nl) + '|'
    def visit_ast(self, t):
        if isinstance(t, list):
            for n in t:
                self.visit_node(n)
        else:
            self.visit_node(t)
    def visit_node(self, n):
        try:
            self.vars.add(n.n)
        except:
            pass
        if isinstance(n, Literal):
            self.result += self.visit_literal(n)
        elif isinstance(n, QFormat):
            self.result += self.visit_q(n)
        elif isinstance(n, Placeholder):
            self.result += self.visit_ph(n)
        elif isinstance(n, ObjcclassFormat):
            self.result += self.visit_objcclass(n)
        elif isinstance(n, ObjcinstanceFormat):
            self.result += self.visit_objcinstance(n)
        elif isinstance(n, QuotedFormat):
            self.result += self.visit_quoted(n)
        elif isinstance(n, OrdinalFormat):
            self.result += self.visit_ordinal(n)
        elif isinstance(n, HumanFormat):
            self.result += self.visit_human(n)
        elif isinstance(n, SFormat):
            self.result += self.visit_s(n)
        elif isinstance(n, SubFormat):
            self.result += self.visit_sub(n)
        elif isinstance(n, PluralFormat):
            self.result += self.visit_plural(n)
        elif isinstance(n, SelectFormat):
            self.result += self.visit_select(n)
        elif isinstance(n, EnumSelectFormat):
            self.result += self.visit_es(n)
        elif isinstance(n, DiffFormat):
            self.result += self.visit_diff(n)

    def visit_literal(self, n:Literal):
        return n.s
    def visit_ph(self, n:Placeholder):
        self.vars.add(n.n)
        return f'{{$arg{n.n}}}'
    def visit_q(self, n:QFormat):
        self.vars.add(n.n)
        return f'{{$arg{n.n} :q}}'
    def visit_objcclass(self, n:ObjcclassFormat):
        self.vars.add(n.n)
        return f'{{$arg{n.n} :objcclass}}'
    def visit_objcinstance(self, n:ObjcinstanceFormat):
        return f'{{$arg{n.n} :objcinstance}}'
    def visit_human(self, n:HumanFormat):
        self.vars.add(n.n)
        # In fact human is not good, use matcher with unit.
        return f'{{$arg{n.n} :human}}'
    def visit_ordinal(self, n:OrdinalFormat):
        self.vars.add(n.n)
        return f'''{{{self.vbar}.match {{$arg{n.n} :integer select=ordinal}}
one {{{{{{$arg{n.n}}}st}}}}
two {{{{{{$arg{n.n}}}nd}}}}
few {{{{{{$arg{n.n}}}rd}}}}
other {{{{{{$arg{n.n}}}th}}}}{self.vbar} :format arg{n.n}=$arg{n.n}}}'''
    def visit_s(self, n:SFormat):
        self.vars.add(n.n)
        return f'''{{{self.vbar}.match {{$arg{n.n} :integer}}
1 {{{{}}}}
* {{{{s}}}}{self.vbar} :format arg{n.n}=$arg{n.n}}}'''
    def visit_quoted(self, n:QuotedFormat):
        self.vars.add(n.n)
        return f'{{$arg{n.n} :quote}}'
    def visit_sub(self, n:SubFormat):
        self.vars.update(set(n.args))
        s = f'{{:format id={n.target}'
        for i, arg in enumerate(n.args):
            s += f' arg{i}=$arg{arg}'
        return s + '}'
    def visit_plural(self, n:PluralFormat):
        self.vars.add(n.n)
        s = f'{{{self.vbar}.match {{$arg{n.n} :range}}'
        vars = [n.n]
        for k, v in n.table.items():
            converter = ToMF2(self.nest_level + 1)
            converter.visit_ast(v)
            vars += converter.vars
            key = ''
            if isinstance(k, int) or k == '*':
                key = k
            elif isinstance(k, range):
                key = f'{k.start}...{k.stop - 1}'
            elif isinstance(k, tuple):
                raise Exception("to be done...")
            s += f'\n{key} '
            s+= '{{' f'{converter.result}' + '}}'
        s += f'{self.vbar} :format'
        for i in vars:
            s+=f' arg{i}=$arg{i}'
        s+='}'
        return s
    def visit_select(self, n:SelectFormat):
        self.vars.add(n.n)
        match_str = '{' + self.vbar + f'.match {{$arg{n.n} :integer}}'
        vars = [n.n]
        for i, c in enumerate(n.choices):
            converter = ToMF2(self.nest_level+1)
            converter.visit_ast(c)
            vars += converter.vars
            match_str += f'\n{i} ' '{{'
            match_str += f'{converter.result}' + '}}'
        match_str += self.vbar + ' :format'
        for i in vars:
            match_str +=f' arg{i}=$arg{i}'
        match_str += '}'
        return match_str
    def visit_es(self, n:EnumSelectFormat):
        self.vars.add(n.n)
        match_str = '{' + self.vbar + f'.match {{$arg{n.n} :{n.enum}}}'
        vars = [n.n]
        for i, c in n.choices.items():
            converter = ToMF2(self.nest_level+1)
            converter.visit_ast(c)
            vars += converter.vars
            match_str += f'\n{i} ' '{{' + converter.result + '}}'
        match_str += self.vbar + ' :format'
        for i in vars:
            match_str +=f' arg{i}=$arg{i}'
        match_str += '}'
        return match_str
    # {|{:diff tree=\|\| normal=\|\| from=$arg0 to=$arg1}| :format arg0=$arg0}
    def visit_diff(self, n:DiffFormat):
        self.vars.update({n.a, n.b})
        vars = {n.a, n.b}
        s = '{' f'{self.vbar}' '{:diff from=$arg' f'{n.a}' f' to=$arg{n.b}'
        
        for k, v in {'normal' : n.msg, 'tree' : n.tree_msg}.items():
            cvt = ToMF2(self.nest_level+1)
            cvt.visit_ast(v)
            vars.update(cvt.vars)
            p = r'\$(?!arg|from|to)'
            r = re.sub(p, f'{{$from}}', cvt.result, count=1)
            r = re.sub(p, f'{{$to}}', r, count=2)
            s+= f' {k}={cvt.vbar}{r}{cvt.vbar}'
        s += '}' f'{self.vbar} :format'
        for i in vars:
            s+=f' arg{i}=$arg{i}'
        s+='}'
        return s

f = open('fmt.lark')
parser = Lark(f.read(), start='message')
# msg = '''{|} { %select{a|b}1'''
# tree = parser.parse(msg)
# print(tree)
transformer = ast_utils.create_transformer(this_module, ToAst())
# fmt_ast = transformer.transform(tree)
# print(fmt_ast)
# cvt = ToMF2()
# cvt.visit_ast(fmt_ast)
# mf2 = cvt.result
# print(mf2)

def handle_xliff(f):
    ET.register_namespace("", "urn:oasis:names:tc:xliff:document:2.0")
    xlf = ET.parse(f)
    ns = {"": "urn:oasis:names:tc:xliff:document:2.0"}
    for group in ["TextSubstitution", 'Diagnostic']:
        group_node = xlf.find(f'./file/group[@id="{group}"]', ns)
        for unit in group_node.findall(f'./unit', ns):
            source = unit.find("./segment/source", ns)
            tree = parser.parse(source.text)
            target = unit.find("./segment/target", ns)
            fmt_ast = transformer.transform(tree)
            cvt = ToMF2()
            cvt.visit_ast(fmt_ast)
            target.text = cvt.result

    xlf.getroot().insert(
        0,
        ET.Comment(
            "This file is automatically generated. Do not update this file directly by hand! Use `update-xliff.py`."
        ),
    )
    ET.indent(xlf)
    xlf.write(
        f"{f}", encoding="UTF-8", xml_declaration=True, short_empty_elements=False
    )


xliffs = (pathlib.Path("../xliff/en/US")).glob("*.xlf")
for f in xliffs:
    handle_xliff(f)
