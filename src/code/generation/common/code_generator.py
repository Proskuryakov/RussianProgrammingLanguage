from src.semantic.scopes import IdentScope


class NodeCodeGenerator:
    def __init__(self, node_type: type):
        self.node_type = node_type
        self.code_generator: RussianLanguageCodeGenerator = None

    def gen_code(self, node, scope: IdentScope, *args, **kwargs):
        pass


class DefaultCodeGen(NodeCodeGenerator):
    def __init__(self):
        super().__init__(type(None))

    def gen_code(self, node, scope: IdentScope, *args, **kwargs):
        raise TypeError(f"Not found code gen for {type(node)}")


class RussianLanguageCodeGenerator:

    def __init__(self):
        self.handlers = dict()

    def register_code_generator(self, gen: NodeCodeGenerator):
        self.handlers[gen.node_type] = gen
        gen.code_generator = self

    def gen_code_for_node(self, node, scope: IdentScope, *args, **kwargs):
        return self.handlers.get(type(node), DefaultCodeGen()).gen_code(node, scope, args, kwargs)
