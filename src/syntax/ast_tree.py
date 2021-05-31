from abc import ABC, abstractmethod
from contextlib import suppress
from typing import Callable, Tuple, Optional, Union
from enum import Enum

from src.semantic.exception import SemanticException
from src.semantic.types import TypeDesc, UNDEFINED_TYPE, TYPE_CONVERTIBILITY
from src.syntax.types import BinOp


class AstNode(ABC):
    init_action: Callable[['AstNode'], None] = None

    def __init__(self, **props) -> None:
        super().__init__()
        self.row = None
        self.col = None
        for k, v in props.items():
            setattr(self, k, v)
        if AstNode.init_action is not None:
            AstNode.init_action(self)
        self.node_type = None
        self.node_ident = None

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


class _GroupNode(AstNode):

    def __init__(self, name: str, *childs: AstNode, **props) -> None:
        super().__init__(**props)
        self.name = name
        self._childs = childs

    def __str__(self) -> str:
        return self.name

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return self._childs


class ExpressionNode(AstNode, ABC):
    pass


class ExpressionListNode(AstNode):
    def __init__(self, *exprs: ExpressionNode, **props) -> None:
        super().__init__(**props)
        self.exprs = exprs
        self.count = len(exprs)

    @property
    def childs(self) -> Tuple[ExpressionNode]:
        return self.exprs

    def __str__(self) -> str:
        return 'Expressions'

    def __len__(self):
        return len(self.exprs)


class StatementNode(ExpressionNode, ABC):

    def to_str_full(self):
        return self.to_str()


class StatementListNode(AstNode):
    def __init__(self, *exprs: StatementNode, **props) -> None:
        super().__init__(**props)
        self.exprs = exprs
        self.program = False

    @property
    def childs(self) -> Tuple[StatementNode]:
        return self.exprs

    def __str__(self) -> str:
        return '...'


class LiteralNode(ExpressionNode):

    def __init__(self, literal: str, **props) -> None:
        super().__init__(**props)
        self.literal = literal

        if not literal:
            self.value = None
            self.literal = None
        elif literal in ('ЛОЖЬ', 'ИСТИНА'):
            self.value = literal == 'ИСТИНА'
        else:
            self.value = literal
            try:
                self.value = eval(literal)
            except TypeError:
                pass

    def __str__(self) -> str:
        return f"LiteralNode: {self.literal}"


class RusIdentifierNode(ExpressionNode):
    def __init__(self, name: str, **props) -> None:
        super().__init__(**props)
        self.name = str(name)

    def __str__(self) -> str:
        return str(self.name)


class ArrayIdentifierNode(ExpressionNode):
    def __init__(self, ident: RusIdentifierNode, index: ExpressionNode, **props) -> None:
        super().__init__(**props)
        self.indent = ident
        self.index = index

    def __str__(self) -> str:
        return "Array element"

    @property
    def childs(self) -> Tuple[RusIdentifierNode, ExpressionNode]:
        return self.indent, self.index


class TypeNode(RusIdentifierNode):
    def __init__(self, name: str, **props) -> None:
        super().__init__(name, **props)
        self.type = UNDEFINED_TYPE
        with suppress(SemanticException):
            self.type = TypeDesc.from_str(name)


class AssignNode(ExpressionNode):
    def __init__(self, var: RusIdentifierNode, val: ExpressionNode, **props) -> None:
        super().__init__(**props)
        self.var = var
        self.val = val

    @property
    def childs(self) -> Tuple[RusIdentifierNode, ExpressionNode]:
        return self.var, self.val

    def __str__(self) -> str:
        return 'Assign Node (=)'


class CallNode(ExpressionNode):
    def __init__(self, func: Union[RusIdentifierNode, ArrayIdentifierNode], params: ExpressionListNode,
                 **props) -> None:
        super().__init__(**props)
        self.func = func
        self.params = params

    def __str__(self) -> str:
        return 'call'

    @property
    def childs(self) -> Tuple[ExpressionNode, ExpressionListNode]:
        return self.func, self.params


class VariableDefinitionNode(StatementNode):
    def __init__(self, type_: TypeNode, *vars_: Union[RusIdentifierNode, 'AssignNode', 'ArrayDefinitionNode',
                                                      'ArrayDefinitionInPlaceNode'], **props):
        super(VariableDefinitionNode, self).__init__(**props)
        self._type = type_
        self._vars = vars_

    def __str__(self) -> str:
        return str(self._type)

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return self._vars


class ArrayDefinitionInPlaceNode(StatementNode):
    def __init__(self, ident: RusIdentifierNode, size: ExpressionNode = None, values: ExpressionListNode = None,
                 **props):
        super(ArrayDefinitionInPlaceNode, self).__init__(**props)
        self._ident = ident
        self._size = size if size else LiteralNode(str(len(values)))
        self._vals = values if values else EMPTY_EXPRS

    def __str__(self) -> str:
        return f"Array {'' if  not isinstance(self._size, LiteralNode) else self._size.value}"

    @property
    def name(self):
        return self._ident.name

    @property
    def childs(self) -> Tuple[RusIdentifierNode, ExpressionNode, ExpressionListNode]:
        return self._ident, self._size, self._vals


class ArrayDefinitionNode(StatementNode):
    def __init__(self, ident: RusIdentifierNode, size: ExpressionNode, **props):
        super(ArrayDefinitionNode, self).__init__(**props)
        self._size = size
        self._ident = ident

    def __str__(self) -> str:
        return f"Array size {self._size}"

    @property
    def name(self):
        return self._ident.name

    @property
    def childs(self) -> Tuple[RusIdentifierNode, ExpressionNode]:
        return self._ident, self._size


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
    def __init__(self, cond: ExpressionNode, if_stmt: StatementNode, else_stmt: Optional[StatementNode] = None,
                 **props):
        super(IfNode, self).__init__(**props)
        self.cond = cond
        self.if_stmt = if_stmt
        self.else_stmt = else_stmt if else_stmt else EMPTY_STATEMENT

    def __str__(self) -> str:
        return str("If-Else Node")

    @property
    def childs(self) -> Tuple[ExpressionNode, StatementNode, StatementNode]:
        return self.cond, self.if_stmt, self.else_stmt


class WhileNode(StatementNode):
    def __init__(self, cond: ExpressionNode, stmt: StatementNode, **props):
        super(WhileNode, self).__init__(**props)
        self.cond = cond
        self.stmt = stmt

    def __str__(self) -> str:
        return str("While Node")

    @property
    def childs(self) -> Tuple[ExpressionNode, StatementNode]:
        return self.cond, self.stmt


class DoWhileNode(StatementNode):
    def __init__(self, stmt: StatementNode, cond: ExpressionNode, **props):
        super(DoWhileNode, self).__init__(**props)
        self.cond = cond
        self.stmt = stmt

    def __str__(self) -> str:
        return str("Do-While Node")

    @property
    def childs(self) -> Tuple[StatementNode, ExpressionNode]:
        return self.stmt, self.cond


class ForNode(StatementNode):
    """Класс для представления в AST-дереве цикла for
    """

    def __init__(self, init: Optional[StatementNode], cond: Optional[StatementNode],
                 step: Optional[StatementNode], body: Optional[StatementNode], **props) -> None:
        super().__init__(**props)
        self.init = init if init else EMPTY_STATEMENT
        self.cond = cond if cond else EMPTY_STATEMENT
        self.step = step if step else EMPTY_STATEMENT
        self.body = body if body else EMPTY_STATEMENT

    def __str__(self) -> str:
        return 'for'

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return self.init, self.cond, self.step, self.body


class ParamNode(StatementNode):
    """Класс для представления в AST-дереве объявления параметра функции
    """

    def __init__(self, type_: TypeNode, name: Union[RusIdentifierNode, ArrayIdentifierNode], **props) -> None:
        super().__init__(**props)
        self.type = type_
        self.name = name

    def __str__(self) -> str:
        return str(self.type)

    @property
    def childs(self) -> Tuple[AstNode]:
        return self.name,


class ParamListNode(StatementNode):
    def __init__(self, *params: ParamNode, **props):
        super(ParamListNode, self).__init__(**props)
        self.params = params

    def __str__(self) -> str:
        return "Params"

    def __len__(self):
        return len(self.params)

    @property
    def childs(self) -> Tuple[ParamNode, ...]:
        return self.params


class FunctionDefinitionNode(StatementNode):
    def __init__(self, type_: TypeNode, name: RusIdentifierNode, params: ParamListNode,
                 body: StatementNode, **props):
        super(FunctionDefinitionNode, self).__init__(**props)
        self.type_ = type_
        self.name = name
        self.params = params
        self.body = body

    def __str__(self) -> str:
        return 'Define func'

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return _GroupNode(str(self.type_), self.name), self.params, self.body


class FunctionDeclarationNode(StatementNode):
    def __init__(self, type_: TypeNode, name: RusIdentifierNode, params: ParamListNode, **props):
        super(FunctionDeclarationNode, self).__init__(**props)
        self.type_ = type_
        self.name = name
        self.params = params

    def __str__(self) -> str:
        return 'Declare func'

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return _GroupNode(str(self.type_), self.name), self.params


class ReturnNode(StatementNode):
    def __init__(self, expr: ExpressionNode, **props):
        super(ReturnNode, self).__init__(**props)
        self.expr = expr

    def __str__(self) -> str:
        return 'Return'

    @property
    def childs(self) -> Tuple[ExpressionNode]:
        return self.expr,


class TypeConvertNode(ExpressionNode):
    """Класс для представления в AST-дереве операций конвертации типов данных
       (в языке программирования может быть как expression, так и statement)
    """

    def __init__(self, expr: ExpressionNode, type_: TypeDesc, **props) -> None:
        super().__init__(**props)
        self.expr = expr
        self.type = type_
        self.node_type = type_

    def __str__(self) -> str:
        return 'convert'

    @property
    def childs(self) -> Tuple[AstNode, ...]:
        return (_GroupNode(str(self.type), self.expr),)


def type_convert(expr: ExpressionNode, type_: TypeDesc, comment: Optional[str] = None) -> ExpressionNode:
    if expr.node_type is None:
        raise SemanticException('type of expression can\'t be resolved')
    if expr.node_type == type_:
        return expr
    if (expr.node_type.is_simple and type_.is_simple and
            expr.node_type.base_type in TYPE_CONVERTIBILITY and type_.base_type in TYPE_CONVERTIBILITY[
                expr.node_type.base_type]):
        return TypeConvertNode(expr, type_)
    else:
        raise SemanticException('Тип {0}{2} не конвертируется в {1}'.format(
            expr.node_type, type_, ' ({})'.format(comment) if comment else ''))


EMPTY_LITERAL = LiteralNode(None)
EMPTY_STATEMENT = StatementListNode()
EMPTY_EXPRS = ExpressionListNode()
