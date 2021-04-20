class AstNodeSemanticHandler:
    def __init__(self, node_type: type):
        self.node_type = node_type

    def check_node_type(self, node):
        return self.node_type == type(node)

    def check_semantic(self, node, *vals, **props):
        pass
