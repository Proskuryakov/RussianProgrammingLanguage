import inspect
import sys

from src.semantic.scopes import IdentScope
from src.syntax.ast_tree import LiteralNode, BinaryOperationNode
from src.syntax.types import BinOp


class NodeCalc:
    def __init__(self, node_type: type):
        self.node_type = node_type
        self.node_calculator: 'RussianLanguageNodeCalculator' = None

    def check_node_type(self, node):
        return self.node_type == type(node)

    def try_calc(self, node, scope: IdentScope, *vals, **props):
        pass


class DefaultCalc(NodeCalc):
    def __init__(self):
        super().__init__(type(None))

    def try_calc(self, node, scope: IdentScope, *vals, **props):
        raise Exception(f"No founded calc for node type {type(node)}")


class LiteralNodeCalc(NodeCalc):
    def __init__(self):
        super().__init__(LiteralNode)

    def try_calc(self, node: LiteralNode, scope: IdentScope, *vals, **props):
        return node.value


class BinOpNodeCalc(NodeCalc):
    def __init__(self):
        super().__init__(BinaryOperationNode)

    def try_calc(self, node: BinaryOperationNode, scope: IdentScope, *vals, **props):

        if node.op == BinOp.ADD:
            return (self.node_calculator.process_node(node.arg1, scope, vals, props) +
                    self.node_calculator.process_node(node.arg2, scope, vals, props))
        if node.op == BinOp.SUB:
            return (self.node_calculator.process_node(node.arg1, scope, vals, props) -
                    self.node_calculator.process_node(node.arg2, scope, vals, props))
        if node.op == BinOp.MUL:
            return (self.node_calculator.process_node(node.arg1, scope, vals, props) *
                    self.node_calculator.process_node(node.arg2, scope, vals, props))
        if node.op == BinOp.DIV:
            return (self.node_calculator.process_node(node.arg1, scope, vals, props) +
                    self.node_calculator.process_node(node.arg2, scope, vals, props))


node_calcs = []

for name, obj in inspect.getmembers(sys.modules[__name__]):
    if inspect.isclass(obj) and issubclass(obj, NodeCalc) and obj != NodeCalc:
        node_calcs.append(obj)


class RussianLanguageNodeCalculator:
    def __init__(self):
        self.handlers_dict = dict()
        self.init_analyser()

    def init_analyser(self):
        for cls in node_calcs:
            self.register_handler(cls())

    def register_handler(self, handler: NodeCalc):
        self.handlers_dict[handler.node_type] = handler
        handler.node_calculator = self

    def process_node(self, node, scope: IdentScope, *vals, **props):
        return self.handlers_dict.get(type(node), DefaultCalc()).try_calc(node, scope, *vals, **props)


GLOBAL_NODE_CALC = RussianLanguageNodeCalculator()
