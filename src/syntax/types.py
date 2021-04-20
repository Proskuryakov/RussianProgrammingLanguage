from enum import Enum


class BinOp(Enum):
    ADD = '+'
    SUB = '-'
    MUL = '*'
    DIV = '/'
    MORE = '>'
    MORE_E = '>='
    LESS = '<'
    LOGICAL_AND = 'И'
    LOGICAL_OR = 'ИЛИ'
    LESS_E = '<='
    NOT_EQ = '!='
    EQ = '=='
