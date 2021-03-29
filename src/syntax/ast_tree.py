from abc import ABC, abstractmethod
from typing import Callable, Tuple, Optional, Union
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


class AstNode(ABC):
    @property
    def childs(self) -> Tuple['AstNode', ...]:
        return ()

    @abstractmethod
    def __str__(self) -> str:
        pass

    @property
    def tree(self) -> [str, ...]:
        res = [str(self)]
        childs = self.childs
        for i, child in enumerate(childs):
            ch0, ch = '├', '│'
            if i == len(childs) - 1:
                ch0, ch = '└', ' '
            res.extend(((ch0 if j == 0 else ch) + ' ' + s for j, s in enumerate(child.tree)))
        return res

    def visit(self, func: Callable[['AstNode'], None]) -> None:
        func(self)
        map(func, self.childs)

    def to_str(self):
        return str(self)

    def __getitem__(self, index):
        return self.childs[index] if index < len(self.childs) else None


class ExpressionNode(AstNode):
    pass


class StatementNode(ExpressionNode, ABC):

    def to_str_full(self):
        return self.to_str()


class StatementListNode(AstNode):
    def __init__(self, *exprs: AstNode):
        super().__init__()
        self.exprs = exprs

    @property
    def childs(self) -> Tuple[AstNode]:
        return self.exprs

    def __str__(self) -> str:
        return '...'


class LiteralNode(ExpressionNode):

    def __init__(self, literal: str, **props) -> None:
        super().__init__(**props)
        self.literal = literal
        if literal in ('ЛОЖЬ', 'ИСТИНА'):
            self.value = bool(literal)
        else:
            self.value = eval(literal)

    def __str__(self) -> str:
        return f"LiteralNode: {self.literal}"


class RusIdentifierNode(ExpressionNode):
    def __init__(self, name: str):
        super().__init__()
        self.name = str(name)

    def __str__(self) -> str:
        return str(self.name)


class AssignNode(StatementNode):
    def __init__(self, var: RusIdentifierNode, val: ExpressionNode):
        super().__init__()
        self.var = var
        self.val = val

    @property
    def childs(self) -> Tuple[RusIdentifierNode, ExpressionNode]:
        return self.var, self.val

    def __str__(self) -> str:
        return 'Assign Node (=)'


class BinaryOperationNode(ExpressionNode):
    def __init__(self, op: BinOp, arg1: ExpressionNode, arg2: ExpressionNode, **props) -> None:
        super().__init__(**props)
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2

    def __str__(self) -> str:
        return str(self.op.value)

    @property
    def childs(self) -> Tuple[ExpressionNode, ExpressionNode]:
        return self.arg1, self.arg2
