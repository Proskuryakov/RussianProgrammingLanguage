from src.semantic.scopes import IdentScope


class NodeCodeGenerator:
    def __init__(self, node_type: type):
        self.node_type = node_type
        self.code_generator: RussianLanguageCodeGenerator = None

    def gen_code(self, node, scope: IdentScope, label_provider: 'LabelProvider', *args, **kwargs):
        pass


class DefaultCodeGen(NodeCodeGenerator):
    def __init__(self):
        super().__init__(type(None))

    def gen_code(self, node, scope: IdentScope, label_provider: 'LabelProvider',  *args, **kwargs):
        raise TypeError(f"Not found code gen for {type(node)}")


class LabelProvider:
    def get_usual_label(self):
        pass

    def get_jump_label(self):
        pass


class RussianLanguageCodeGenerator:

    def __init__(self):
        self.handlers = dict()

    def register_code_generator(self, gen: NodeCodeGenerator):
        self.handlers[gen.node_type] = gen
        gen.code_generator = self

    def gen_code_for_node(self, node, scope: IdentScope, label_provider: LabelProvider, *args, **kwargs):
        return self.handlers.get(type(node), DefaultCodeGen()).gen_code(node, scope, label_provider, args, kwargs)
