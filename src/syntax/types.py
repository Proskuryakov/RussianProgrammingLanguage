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

    _inverse = {MORE: LESS_E, MORE_E: LESS, LESS_E: MORE, LESS: MORE_E, EQ: NOT_EQ, NOT_EQ: EQ}

    @staticmethod
    def inverse_op(op: 'BinOp'):
        return BinOp._inverse[op]
