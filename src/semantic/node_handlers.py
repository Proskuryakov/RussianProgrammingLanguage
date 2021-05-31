import inspect
import sys

from src.semantic.exception import SemanticException
from src.semantic.node_calc import GLOBAL_NODE_CALC
from src.semantic.scopes import IdentScope
from src.semantic.scopes_include import IdentDesc, EMPTY_IDENT, ScopeType
from src.semantic.types import TypeDesc, is_correct_type, BIN_OP_TYPE_COMPATIBILITY
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
        try:
            node.val = LiteralNode(str(self.semantic_checker.try_calc_node(node.val, scope)))
        except Exception:
            pass
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


class ArrayIdentifierNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(ArrayIdentifierNode)

    def check_semantic(self, node: ArrayIdentifierNode, scope: IdentScope, *vals, **props):
        ident = scope.get_ident(node.indent.name)
        if ident is None:
            raise SemanticException(f'Идентификатор \'{node.indent.name}\' не найден', node.row, node.col)
        if not ident.is_array:
            raise SemanticException(f'Идентификатор \'{node.indent.name}\' не является массивом', node.row, node.col)

        if isinstance(node.index, ExpressionNode):
            try:
                value = self.semantic_checker.try_calc_node(node.index, scope)
                node.index = LiteralNode(str(value))
            except Exception:
                pass
        self.semantic_checker.process_node(node.index, scope)

        if isinstance(node.index, LiteralNode) and node.index.value < 0:
            raise SemanticException(f'Взятие по отрицательному индексу', node.row, node.col)

        node.node_type = ident.type
        node.index = type_convert(node.index, TypeDesc.INT, 'индекс')
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


class ArrayDefinitionInPlaceNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(ArrayDefinitionInPlaceNode)

    def check_semantic(self, node: ArrayDefinitionInPlaceNode, scope: IdentScope, *vals, **props):
        ident = scope.get_ident(node._ident.name)
        if ident is None:
            raise SemanticException(f'Идентификатор \'{node._ident.name}\' не найден', node.row, node.col)

        if isinstance(node._size, ExpressionNode):
            try:
                value = self.semantic_checker.try_calc_node(node._size, scope)
                node._size = LiteralNode(str(value))
            except Exception:
                raise SemanticException("Не удалось вычислить значение выражения", node.row, node.col)

        self.semantic_checker.process_node(node._size, scope)
        if node._size.node_type != TypeDesc.INT or node._size.value < 0:
            raise SemanticException(f'Размер массива должен быть целым неотрицательным числом', node.row, node.col)
        self.semantic_checker.process_node(node._vals, scope)

        if node._size.value < len(node._vals):
            raise SemanticException(f'Размер массива [{node._size.value}] '
                                    f'меньше, чем количество элементов в инициализаторе '
                                    f'[{len(node._vals)}]', node.row, node.col)

        node.node_type = ident.type
        ident.is_array = True
        node.node_ident = ident


class ArrayDefinitionNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(ArrayDefinitionNode)

    def check_semantic(self, node: ArrayDefinitionNode, scope: IdentScope, *vals, **props):
        ident = scope.get_ident(node._ident.name)
        if ident is None:
            raise SemanticException(f'Идентификатор \'{node._ident.name}\' не найден', node.row, node.col)

        if isinstance(node._size, ExpressionNode):
            try:
                value = self.semantic_checker.try_calc_node(node._size, scope)
                node._size = LiteralNode(str(value))
            except Exception:
                raise SemanticException("Не удалось вычислить значение выражения", node.row, node.col)

        self.semantic_checker.process_node(node._size, scope)
        node.node_type = ident.type
        ident.is_array = True
        node.node_ident = ident


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


class BinaryOperationNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(BinaryOperationNode)

    def check_semantic(self, node: BinaryOperationNode, scope: IdentScope, *vals, **props):
        self.semantic_checker.process_node(node.arg1, scope)
        self.semantic_checker.process_node(node.arg2, scope)

        if node.arg1.node_type.is_simple or node.arg2.node_type.is_simple:
            compatibility = BIN_OP_TYPE_COMPATIBILITY[node.op]
            args_types = (node.arg1.node_type.base_type, node.arg2.node_type.base_type)
            if args_types in compatibility:
                node.node_type = TypeDesc.from_base_type(compatibility[args_types])
                return

            if node.arg2.node_type.base_type in TYPE_CONVERTIBILITY:
                for arg2_type in TYPE_CONVERTIBILITY[node.arg2.node_type.base_type]:
                    args_types = (node.arg1.node_type.base_type, arg2_type)
                    if args_types in compatibility:
                        node.arg2 = type_convert(node.arg2, TypeDesc.from_base_type(arg2_type))
                        node.node_type = TypeDesc.from_base_type(compatibility[args_types])
                        return
            if node.arg1.node_type.base_type in TYPE_CONVERTIBILITY:
                for arg1_type in TYPE_CONVERTIBILITY[node.arg1.node_type.base_type]:
                    args_types = (arg1_type, node.arg2.node_type.base_type)
                    if args_types in compatibility:
                        node.arg1 = type_convert(node.arg1, TypeDesc.from_base_type(arg1_type))
                        node.node_type = TypeDesc.from_base_type(compatibility[args_types])
                        return

        raise SemanticException("Оператор {} не применим к типам ({}, {})".format(
            node.op, node.arg1.node_type, node.arg2.node_type, node.row, node.col))


class IfNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(IfNode)

    def check_semantic(self, node: IfNode, scope: IdentScope, *vals, **props):
        self.semantic_checker.process_node(node.cond, scope)
        node.cond = type_convert(node.cond, TypeDesc.BOOL, 'условие')
        self.semantic_checker.process_node(node.if_stmt, IdentScope(scope))
        if node.else_stmt:
            self.semantic_checker.process_node(node.else_stmt, IdentScope(scope))
        node.node_type = TypeDesc.VOID


class CallNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(CallNode)

    def check_semantic(self, node: CallNode, scope: IdentScope, *vals, **props):
        func = scope.get_ident(node.func.name)
        if func is None:
            raise SemanticException('Функция {} не найдена'.format(node.func.name), node.row, node.col)
        if not func.type.func:
            raise SemanticException('Идентификатор {} не является функцией'.format(func.name), node.row, node.col)
        if len(func.type.params) != len(node.params):
            raise SemanticException('Кол-во аргументов {} не совпадает (ожидалось {}, передано {})'.format(
                func.name, len(func.type.params), len(node.params)
            ), node.row, node.col)
        params = []
        error = False
        decl_params_str = fact_params_str = ''
        for i in range(len(node.params)):
            param: ParamNode = node.params[i]
            self.semantic_checker.process_node(param, scope)
            if len(decl_params_str) > 0:
                decl_params_str += ', '
            decl_params_str += str(func.type.params[i])
            if len(fact_params_str) > 0:
                fact_params_str += ', '
            fact_params_str += str(param.node_type)
            try:
                params.append(type_convert(param, func.type.params[i]))
            except:
                error = True
        if error:
            raise SemanticException('Фактические типы ({1}) аргументов функции {0} не совпадают с формальными ({2})\
                                            и не приводимы'.format(
                func.name, fact_params_str, decl_params_str
            ), node.row, node.col)
        else:
            node.params = ExpressionListNode(*params)
            node.func.node_type = func.type
            node.func.node_ident = func
            node.node_type = func.type.return_type


class ExpressionNodeListHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(ExpressionListNode)

    def check_semantic(self, node: ExpressionListNode, scope: IdentScope, *vals, **props):
        for item in node.exprs:
            self.semantic_checker.process_node(item, scope)


class FunctionDefinitionNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(FunctionDefinitionNode)

    def check_semantic(self, node: FunctionDefinitionNode, scope: IdentScope, *vals, **props):
        if scope.curr_func:
            raise SemanticException(
                "Объявление функции ({}) внутри другой функции не поддерживается".format(node.name.name),
                node.row, node.col)
        parent_scope = scope
        self.semantic_checker.process_node(node.type_, scope)
        scope = IdentScope(scope)

        # временно хоть какое-то значение, чтобы при добавлении параметров находить scope функции
        scope.func = EMPTY_IDENT
        params = []
        for param in node.params.params:
            # при проверке параметров происходит их добавление в scope
            self.semantic_checker.process_node(param, scope)
            params.append(param.type.type)

        type_ = TypeDesc(None, node.type_.type, tuple(params))
        func_ident = IdentDesc(node.name.name, type_)
        scope.func = func_ident
        node.name.node_type = type_
        try:
            node.name.node_ident = parent_scope.curr_global.add_ident(func_ident)
        except SemanticException as e:
            raise SemanticException("Повторное объявление функции {}".format(node.name.name), node.row, node.col)
        self.semantic_checker.process_node(node.body, scope)
        node.node_type = TypeDesc.VOID


class ParamNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(ParamNode)

    def check_semantic(self, node, scope: IdentScope, *vals, **props):
        self.semantic_checker.process_node(node.type, scope)
        node.name.node_type = node.type.type
        try:
            node.name.node_ident = scope.add_ident(IdentDesc(node.name.name, node.type.type, ScopeType.PARAM))
        except SemanticException:
            raise SemanticException('Параметр {} уже объявлен'.format(node.name.name), node.row, node.col)
        node.node_type = TypeDesc.VOID


class ParamListNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(ParamListNode)

    def check_semantic(self, node: ParamListNode, scope: IdentScope, *vals, **props):
        for param in node.params:
            self.semantic_checker.process_node(param, scope)


class ForNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(ForNode)

    def check_semantic(self, node, scope: IdentScope, *vals, **props):
        scope = IdentScope(scope)
        self.semantic_checker.process_node(node.init, scope)
        if node.cond == EMPTY_STATEMENT:
            node.cond = LiteralNode('ИСТИНА')
        self.semantic_checker.process_node(node.cond, scope)
        node.cond = type_convert(node.cond, TypeDesc.BOOL, 'условие')
        self.semantic_checker.process_node(node.step, scope)
        self.semantic_checker.process_node(node.body, scope)
        node.node_type = TypeDesc.VOID


class WhileNodeHandler(AstNodeSemanticHandler):
    def __init__(self):
        super().__init__(WhileNode)

    def check_semantic(self, node: WhileNode, scope: IdentScope, *vals, **props):
        self.semantic_checker.process_node(node.cond, scope)
        node.cond = type_convert(node.cond, TypeDesc.BOOL, 'условие')
        self.semantic_checker.process_node(node.stmt, IdentScope(scope))
        node.node_type = TypeDesc.VOID


###############################################################################################################

classes = []

for name, obj in inspect.getmembers(sys.modules[__name__]):
    if inspect.isclass(obj) and issubclass(obj, AstNodeSemanticHandler) and obj != AstNodeSemanticHandler:
        classes.append(obj)


class RussianLanguageSemanticAnalyser:
    def __init__(self):
        self.handlers_dict = dict()
        self.init_analyser()
        self.node_calc = GLOBAL_NODE_CALC

    def init_analyser(self):
        for cls in classes:
            self.register_handler(cls())

    def register_handler(self, handler: AstNodeSemanticHandler):
        self.handlers_dict[handler.node_type] = handler
        handler.semantic_checker = self

    def process_node(self, node, scope: IdentScope, *vals, **props):
        self.handlers_dict.get(type(node), DefaultHandler()).check_semantic(node, scope, *vals, **props)

    def try_calc_node(self, node, scope: IdentScope, *vals, **props):
        try:
            return self.node_calc.process_node(node, scope, vals, props)
        except Exception as e:
            raise e


GLOBAL_ANALYSER = RussianLanguageSemanticAnalyser()


def get_global_semantic_analyser():
    return GLOBAL_ANALYSER
