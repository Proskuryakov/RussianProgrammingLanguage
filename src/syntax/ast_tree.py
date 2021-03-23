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
    LESS_E = '<='


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

    def __getitem__(self, index):
        return self.childs[index] if index < len(self.childs) else None


class StatementNode(AstNode):
    pass


class StatementListNode(AstNode):
    def __init__(self, *exprs: AstNode):
        super().__init__()
        self.exprs = exprs

    @property
    def childs(self) -> Tuple[AstNode]:
        return self.exprs

    def __str__(self) -> str:
        return '...'


class ExpressionNode(AstNode):
    pass


class NumberNode(ExpressionNode):
    def __init__(self, num: float):
        super().__init__()
        self.num = float(num)

    def __str__(self) -> str:
        return str(self.num)


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
        return '='


class TypeNode(RusIdentifierNode):
    def __init__(self, name: str):
        super().__init__(name)

    def __str__(self) -> str:
        return self.name


class VariableDefenition(StatementNode):
    def __init__(self, type: TypeNode, assign: AssignNode):
        super(VariableDefenition, self).__init__()
        self.type = type
        self.assign = assign

    @property
    def childs(self) -> Tuple[TypeNode, AssignNode]:
        return self.type, self.assign

    def __str__(self) -> str:
        return 'var'
