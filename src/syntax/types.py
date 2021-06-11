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


inverse = {BinOp.MORE: BinOp.LESS_E, BinOp.MORE_E: BinOp.LESS, BinOp.LESS_E: BinOp.MORE, BinOp.LESS: BinOp.MORE_E,
           BinOp.EQ: BinOp.NOT_EQ, BinOp.NOT_EQ: BinOp.EQ}


def inverse_op(op: BinOp):
    return inverse[op]
