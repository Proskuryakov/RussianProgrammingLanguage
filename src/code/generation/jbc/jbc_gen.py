import inspect
import sys

from src.code.generation.common.code_generator import RussianLanguageCodeGenerator, NodeCodeGenerator
from src.semantic.scopes import IdentScope
from src.semantic.scopes_include import ScopeType
from src.semantic.types import TypeDesc
from src.syntax.ast_tree import VariableDefinitionNode, AssignNode, LiteralNode, StatementListNode, StatementNode, \
    ExpressionNode, BinaryOperationNode, RusIdentifierNode, CallNode, ParamNode, ExpressionListNode, \
    FunctionDefinitionNode, ReturnNode
from src.syntax.types import BinOp

jbc_types_init = {TypeDesc.INT.string: 'I', TypeDesc.VOID.string: "V"}

jbc_stloc_types = {TypeDesc.INT.string: 'i'}

jbc_operators = {
    BinOp.ADD: {
        TypeDesc.INT.string: 'add'
    }
}

jbc_built_in_fuctions = {"вывод_целый": "invokevirtual java/io/PrintStream/println(I)V"}
jbc_built_in_load_func = {"вывод_целый": "getstatic java/lang/System/out Ljava/io/PrintStream;"}

class StatementListNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(StatementListNodeCodeGen, self).__init__(StatementListNode)

    def gen_code(self, node: StatementListNode, scope: IdentScope, *args, **kwargs):
        str_code = ""
        for stmt in node.exprs:
            str_code += self.code_generator.gen_code_for_node(stmt, scope)
            str_code += "\n"
        return str_code


class ExpressionListNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(ExpressionListNodeCodeGen, self).__init__(ExpressionListNode)

    def gen_code(self, node: ExpressionListNode, scope: IdentScope, *args, **kwargs):
        str_code = ""

        for expr in node.exprs:
            str_code += self.code_generator.gen_code_for_node(expr, scope) + "\n"

        return str_code[:-1]


class CallNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(CallNodeCodeGen, self).__init__(CallNode)

    def gen_code(self, node: CallNode, scope: IdentScope, *args, **kwargs):

        str_code = ""

        if node.func.node_ident.built_in:
            str_code += f"\t{jbc_built_in_load_func[node.func.node_ident.name]}\n"

        str_code += self.code_generator.gen_code_for_node(node.params, scope) + "\n"

        params_types = []
        for p in node.params.exprs:
            params_types.append(jbc_types_init[p.node_type.string])

        if node.func.node_ident.built_in:
            str_code += f"{jbc_built_in_fuctions[node.func.node_ident.name]}"
        else:
            ident = scope.get_ident(node.func.name)
            str_code += f"\tinvokestatic\t\t\t\t" \
                        f"Main/func_{ident.index}({''.join(params_types)}){jbc_types_init[node.node_type.string]}"
        return str_code


class RusIdentifierNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(RusIdentifierNodeCodeGen, self).__init__(RusIdentifierNode)

    def gen_code(self, node: RusIdentifierNode, scope: IdentScope, *args, **kwargs):

        locals_offset = 0
        if 'locals_offset' in kwargs:
            locals_offset = kwargs['locals_offset']
        if node.node_ident.scope != ScopeType.PARAM:
            str_code = f"\t{jbc_stloc_types[node.node_type.string]}load\t\t\t\t{node.node_ident.index}"
        else:
            str_code = f"\t{jbc_stloc_types[node.node_type.string]}load\t\t\t\t{node.node_ident.index + locals_offset}"
        return str_code


class LiteralNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(LiteralNodeCodeGen, self).__init__(LiteralNode)

    def gen_code(self, node: LiteralNode, scope: IdentScope, *args, **kwargs):

        if not node.literal:
            return ""

        if node.node_type == TypeDesc.INT:
            str_code = f"\tbipush\t\t\t\t{node.value}"
            return str_code


class VarNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(VarNodeCodeGen, self).__init__(VariableDefinitionNode)

    def gen_code(self, node: VariableDefinitionNode, scope: IdentScope, *args, **kwargs):

        str_code = ""

        for var in node._vars:
            if isinstance(var, AssignNode):
                str_code += self.code_generator.gen_code_for_node(var.val, scope, *args, **kwargs) + "\n"
                str_code += f"\t{jbc_stloc_types[node._type.type.string]}store\t\t\t\t{var.node_ident.index}\n"
        return str_code[:-1]


class BinOpNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(BinOpNodeCodeGen, self).__init__(BinaryOperationNode)

    def gen_code(self, node: BinaryOperationNode, scope: IdentScope, *args, **kwargs):
        str_code = ""

        str_code += self.code_generator.gen_code_for_node(node.arg1, scope, *args, **kwargs) + "\n"
        str_code += self.code_generator.gen_code_for_node(node.arg2, scope, *args, **kwargs) + "\n"

        op = jbc_operators[node.op][node.node_type.string]

        str_code += f"\t{jbc_stloc_types[node.node_type.string]}{op}"

        return str_code


class ReturnNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(ReturnNodeCodeGen, self).__init__(ReturnNode)

    def gen_code(self, node: ReturnNode, scope: IdentScope, *args, **kwargs):
        str_code = ""

        str_code += self.code_generator.gen_code_for_node(node.expr, scope, *args, **kwargs) + "\n"
        if not node.expr.node_type:
            str_code += "return"
        else:
            str_code += f"\t{jbc_stloc_types[node.expr.node_type.string]}return"

        return str_code


class FunctionDefinitionNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(FunctionDefinitionNodeCodeGen, self).__init__(FunctionDefinitionNode)

    def gen_code(self, node: FunctionDefinitionNode, scope: IdentScope, *args, **kwargs):
        params = []

        for p in node.params.params:
            params.append(f"{jbc_types_init[p.name.node_type.string]}")

        if node.name.name == 'главный':
            func_name = "main"
            params = ["[Ljava/lang/String;"]
        else:
            func_name = f"func_{node.name.node_ident.index}"
            kwargs['locals_offset'] = len(params)
        body_code = self.code_generator.gen_code_for_node(node.body, node.body.inner_scope, *args, **kwargs)
        str_code = \
            f""".method public static {func_name}({"".join(params)}){jbc_types_init[node.name.node_type.return_type.string]}
    .limit stack 8
    .limit locals 8

{body_code}
.end method
"""
        return str_code


code_gens = []

for name, obj in inspect.getmembers(sys.modules[__name__]):
    if inspect.isclass(obj) and issubclass(obj, NodeCodeGenerator) and obj != NodeCodeGenerator:
        code_gens.append(obj)


class RussianLanguageJBCGenerator(RussianLanguageCodeGenerator):
    def __init__(self):
        super().__init__()
        for n in code_gens:
            self.register_code_generator(n())

    def get_static_func_locals(self, vars: IdentScope):
        locals_vars_str = []
        for name, desc in vars.idents.items():
            if not desc.type.func and desc.scope in [ScopeType.GLOBAL, ScopeType.LOCAL]:
                locals_vars_str.append(f"\t[{desc.index}] {jbc_types_init[desc.type.string]} val_{desc.index}")
        return ",\n".join(locals_vars_str)

    def gen_main_class(self, name, main_scope: IdentScope, main_code, before_main_code):
        return \
            f"""
.class                   public {name.capitalize()}
.super                   java/lang/Object

.method                  public <init>()V
   .limit stack          1
   .limit locals         1
   .line                 2
   aload_0               
   invokespecial         java/lang/Object/<init>()V
   return                
.end method     
  {before_main_code}

  {main_code}

"""