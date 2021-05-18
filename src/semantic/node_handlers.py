from src.semantic.exception import SemanticException
from src.semantic.scopes import IdentScope
from src.semantic.scopes_include import IdentDesc
from src.semantic.types import TypeDesc, is_correct_type
from src.syntax.ast_tree import *


class AstNodeSemanticHandler:
    def __init__(self, node_type: type):
        self.node_type = node_type
        self.semantic_checker = None

    def check_node_type(self, node):
        return self.node_type == type(node)

    def check_semantic(self, node, scope: IdentScope, *vals, **props):
        pass


class DefaultHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(type(None))

    def check_semantic(self, node, scope: IdentScope, *vals, **props):
        raise Exception(f"No founded handler for node type {type(node)}")


class AssignNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(AssignNode)

    def check_semantic(self, node, scope: IdentScope, *vals, **props):
        self.semantic_checker.process_node(node.var, scope)
        self.semantic_checker.process_node(node.val, scope)
        node.val = type_convert(node.val, node.var.node_type, 'присваиваемое значение')
        self.node_type = node.var.node_type


class StatementListNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(StatementListNode)

    def check_semantic(self, node, scope: IdentScope, *vals, **props):
        if not node.program:
            scope = IdentScope(scope)
        for expr in node.exprs:
            get_global_semantic_analyser().process_node(expr, scope)
        self.node_type = TypeDesc.VOID


class RusIdentifierNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(RusIdentifierNode)

    def check_semantic(self, node: RusIdentifierNode, scope: IdentScope, *vals, **props):
        ident = scope.get_ident(node.name)
        if ident is None:
            raise SemanticException(f'Идентификатор \'{node.name}\' не найден', node.row, node.col)
        node.node_type = ident.type
        node.node_ident = ident


class TypeNodeNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(TypeNode)

    def check_semantic(self, node: TypeNode, scope: IdentScope, *vals, **props):
        if node.name is None or not is_correct_type(node.name):
            raise SemanticException('Неизвестный тип {}'.format(node.name), node.row, node.col)


class LiteralNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(LiteralNode)

    def check_semantic(self, node: LiteralNode, scope: IdentScope, *vals, **props):
        if isinstance(node.value, bool):
            node.node_type = TypeDesc.BOOL
        # проверка должна быть позже bool, т.к. bool наследник от int
        elif isinstance(node.value, int):
            node.node_type = TypeDesc.INT
        elif isinstance(node.value, float):
            node.node_type = TypeDesc.FLOAT
        elif isinstance(node.value, str):
            node.node_type = TypeDesc.STR
        else:
            raise SemanticException(f'Неизвестный тип {type(node.value)} для {node.value}', node.row, node.col)


class VariableDefinitionNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(VariableDefinitionNode)

    def check_semantic(self, node: VariableDefinitionNode, scope: IdentScope, *vals, **props):
        self.semantic_checker.process_node(node._type, scope)
        for var in node._vars:
            var_node: RusIdentifierNode = var.var if isinstance(var, AssignNode) else var
            try:
                scope.add_ident(IdentDesc(var_node.name, node._type.type))
            except SemanticException as e:
                raise SemanticException(e.message, var_node.row, var_node.col)
            self.semantic_checker.process_node(var, scope)
        node.node_type = TypeDesc.VOID


class RussianLanguageSemanticAnalyser:
    def __init__(self):
        self.handlers_dict = dict()
        self.init_analyser()

    def init_analyser(self):
        self.register_handler(AssignNodeHandler())
        self.register_handler(StatementListNodeHandler())
        self.register_handler(RusIdentifierNodeHandler())
        self.register_handler(TypeNodeNodeHandler())
        self.register_handler(LiteralNodeHandler())
        self.register_handler(VariableDefinitionNodeHandler())

    def register_handler(self, handler: AstNodeSemanticHandler):
        self.handlers_dict[handler.node_type] = handler
        handler.semantic_checker = self

    def process_node(self, node, scope: IdentScope):
        self.handlers_dict.get(type(node), DefaultHandler()).check_semantic(node, scope)


GLOBAL_ANALYSER = RussianLanguageSemanticAnalyser()


def get_global_semantic_analyser():
    return GLOBAL_ANALYSER
