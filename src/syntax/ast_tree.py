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


class ExpressionNode(AstNode, ABC):
    pass


class ExpressionListNode(AstNode):
    def __init__(self, *exprs: ExpressionNode):
        super().__init__()
        self.exprs = exprs
        self.count = len(exprs)

    @property
    def childs(self) -> Tuple[ExpressionNode]:
        return self.exprs

    def __str__(self) -> str:
        return 'Expressions'


class StatementNode(ExpressionNode, ABC):

    def to_str_full(self):
        return self.to_str()


class StatementListNode(AstNode):
    def __init__(self, *exprs: StatementNode):
        super().__init__()
        self.exprs = exprs

    @property
    def childs(self) -> Tuple[StatementNode]:
        return self.exprs

    def __str__(self) -> str:
        return '...'


class LiteralNode(ExpressionNode):

    def __init__(self, literal: str, **props) -> None:
        super().__init__(**props)
        self.literal = literal

        if not str:
            self.value = None
            self.literal = None
        elif literal in ('ЛОЖЬ', 'ИСТИНА'):
            self.value = literal == 'ИСТИНА'
        else:
            self.value = eval(str(literal))

    def __str__(self) -> str:
        return f"LiteralNode: {self.literal}"


class RusIdentifierNode(ExpressionNode):
    def __init__(self, name: str):
        super().__init__()
        self.name = str(name)

    def __str__(self) -> str:
        return str(self.name)


class ArrayIdentifierNode(ExpressionNode):
    def __init__(self, ident: RusIdentifierNode, index: ExpressionNode):
        super(ArrayIdentifierNode, self).__init__()
        self.indent = ident
        self.index = index

    def __str__(self) -> str:
        return "Array element"

    @property
    def childs(self) -> Tuple[RusIdentifierNode, ExpressionNode]:
        return self.indent, self.index


class TypeNode(RusIdentifierNode):
    def __init__(self, name: str):
        super().__init__(name)


class AssignNode(ExpressionNode):
    def __init__(self, var: RusIdentifierNode, val: ExpressionNode):
        super().__init__()
        self.var = var
        self.val = val

    @property
    def childs(self) -> Tuple[RusIdentifierNode, ExpressionNode]:
        return self.var, self.val

    def __str__(self) -> str:
        return 'Assign Node (=)'


class VariableDefinitionNode(StatementNode):
    def __init__(self, type_: TypeNode, *vars_: Union[RusIdentifierNode, 'AssignNode'], **props):
        super(VariableDefinitionNode, self).__init__(**props)
        self._type = type_
        self._vars = vars_

    def __str__(self) -> str:
        return str(self._type)

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return self._vars


class ArrayIdentAllocateNode(AstNode):
    def __init__(self, type_: TypeNode, size: Optional[LiteralNode], **props):
        super(ArrayIdentAllocateNode, self).__init__(**props)
        self.type = type_
        self.size = size if size.value else EMPTY_LITERAL

    def __str__(self) -> str:
        return 'Array allocate info'

    @property
    def childs(self) -> Tuple[TypeNode, LiteralNode]:
        return self.type, self.size


class ArrayDefinitionInPlaceNode(StatementNode):
    def __init__(self, type_: TypeNode, ident: ArrayIdentAllocateNode, values: ExpressionListNode, **props):
        super(ArrayDefinitionInPlaceNode, self).__init__(**props)
        self._type = type_
        self._ident = ident
        if not self._ident.size.value:
            self._ident.size = LiteralNode(str(values.count))
        self._vals = values

    def __str__(self) -> str:
        return f"Array of {self._type}"

    @property
    def childs(self) -> Tuple[TypeNode, ArrayIdentAllocateNode, ExpressionListNode]:
        return self._type, self._ident, self._vals


class ArrayDefinitionNode(StatementNode):
    def __init__(self, type_: TypeNode, ident: ArrayIdentifierNode, **props):
        super(ArrayDefinitionNode, self).__init__(**props)
        self._type = type_
        self._ident = ident

    def __str__(self) -> str:
        return f"Array of {self._type}"

    @property
    def childs(self) -> Tuple[TypeNode, ArrayIdentifierNode]:
        return self._type, self._ident


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


class IfNode(StatementNode):
    def __init__(self, cond: ExpressionNode, if_stmt: StatementNode, else_stmt: Optional[StatementNode] = None, **props):
        super(IfNode, self).__init__(**props)
        self.cond = cond
        self.if_stmt = if_stmt
        self.else_stmt = else_stmt if else_stmt else EMPTY_NODE

    def __str__(self) -> str:
        return str("If-Else Node")

    @property
    def childs(self) -> Tuple[ExpressionNode, StatementNode, StatementNode]:
        return self.cond, self.if_stmt, self.else_stmt


EMPTY_LITERAL = LiteralNode(None)
EMPTY_NODE = StatementListNode()
