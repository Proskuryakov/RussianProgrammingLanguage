import inspect
import sys

from src.code.generation.common.code_generator import RussianLanguageCodeGenerator, NodeCodeGenerator
from src.semantic.scopes import IdentScope
from src.semantic.scopes_include import ScopeType
from src.semantic.types import TypeDesc
from src.syntax.ast_tree import VariableDefinitionNode, AssignNode, LiteralNode, StatementListNode, StatementNode, \
    ExpressionNode, BinaryOperationNode, RusIdentifierNode, CallNode, ParamNode, ExpressionListNode, \
    FunctionDefinitionNode, ReturnNode, TypeConvertNode
from src.syntax.types import BinOp

msil_types_init = {TypeDesc.INT.string: 'int32', TypeDesc.VOID.string: "void", TypeDesc.FLOAT.string: "float64"}

msil_stloc_types = {TypeDesc.INT.string: 'i4', TypeDesc.FLOAT.string: 'r8'}

msil_operators = {
    BinOp.ADD: {
        TypeDesc.INT.string: 'add',
        TypeDesc.FLOAT.string: 'add'
    },
    BinOp.SUB: {
        TypeDesc.INT.string: 'sub',
        TypeDesc.FLOAT.string: 'sub',
    },
    BinOp.MUL: {
        TypeDesc.INT.string: 'mul',
        TypeDesc.FLOAT.string: 'mul'
    },
    BinOp.DIV: {
        TypeDesc.INT.string: 'div',
        TypeDesc.FLOAT.string: 'div'
    }

}

msil_built_in_fuctions = {"вывод": "[mscorlib]System.Console::WriteLine",
                          "вывод_целый": "[mscorlib]System.Console::WriteLine",
                          "вывод_вещ": "[mscorlib]System.Console::WriteLine"}


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

        str_code += self.code_generator.gen_code_for_node(node.params, scope) + "\n"

        params_types = []
        for p in node.params.exprs:
            params_types.append(msil_types_init[p.node_type.string])

        if node.func.node_ident.built_in:
            str_code += f"\tIL_%0.4X: call {msil_types_init[node.node_type.string]} " \
                        f"{msil_built_in_fuctions[node.func.node_ident.name]}({','.join(params_types)})" % scope.byte_op_index
            scope.byte_op_index += 4 + len(params_types)
        else:
            ident = scope.get_ident(node.func.name)
            str_code += f"\tIL_%0.4X: call {msil_types_init[node.node_type.string]} " \
                        f"Main::func_{ident.index}({','.join(params_types)})" % scope.byte_op_index
            scope.byte_op_index += 4 + len(params_types)
        return str_code


class RusIdentifierNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(RusIdentifierNodeCodeGen, self).__init__(RusIdentifierNode)

    def gen_code(self, node: RusIdentifierNode, scope: IdentScope, *args, **kwargs):
        str_code = ""
        if 'stloc' in kwargs and kwargs['stloc']:
            if node.node_ident.scope != ScopeType.PARAM:
                if node.node_type == TypeDesc.INT:
                    str_code = f"\tIL_%0.4X: stloc.s {node.node_ident.index}" % scope.byte_op_index
                elif node.node_type == TypeDesc.FLOAT:
                    str_code = f"\tIL_%0.4X: stloc.s val_{node.node_ident.index}" % scope.byte_op_index
                scope.byte_op_index += 2
            else:
                if node.node_type == TypeDesc.INT:
                    str_code = f"\tIL_%0.4X: ldarg.s {node.node_ident.index}" % scope.byte_op_index
                elif node.node_type == TypeDesc.FLOAT:
                    str_code = f"\tIL_%0.4X: ldarg.s p_{node.node_ident.index}" % scope.byte_op_index
                scope.byte_op_index += 2
        else:
            if node.node_ident.scope != ScopeType.PARAM:
                if node.node_type == TypeDesc.INT:
                    str_code = f"\tIL_%0.4X: ldloc.s {node.node_ident.index}" % scope.byte_op_index
                elif node.node_type == TypeDesc.FLOAT:
                    str_code = f"\tIL_%0.4X: ldloc.s val_{node.node_ident.index}" % scope.byte_op_index
                scope.byte_op_index += 2
            else:
                if node.node_type == TypeDesc.INT:
                    str_code = f"\tIL_%0.4X: ldarg.s {node.node_ident.index}" % scope.byte_op_index
                elif node.node_type == TypeDesc.FLOAT:
                    str_code = f"\tIL_%0.4X: ldarg.s p_{node.node_ident.index}" % scope.byte_op_index
                scope.byte_op_index += 2
        return str_code


class LiteralNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(LiteralNodeCodeGen, self).__init__(LiteralNode)

    def gen_code(self, node: LiteralNode, scope: IdentScope, *args, **kwargs):

        if not node.literal:
            return ""

        str_code = ""

        if node.node_type == TypeDesc.INT:
            str_code = f"\tIL_%0.4X: ldc.{msil_stloc_types[node.node_type.string]}.s {node.value}" % scope.byte_op_index
            scope.byte_op_index += 2
        elif node.node_type == TypeDesc.FLOAT:
            str_code = f"\tIL_%0.4X: ldc.{msil_stloc_types[node.node_type.string]} {node.value}" % scope.byte_op_index
            scope.byte_op_index += 10
        return str_code


class AssignNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(AssignNodeCodeGen, self).__init__(AssignNode)

    def gen_code(self, node: AssignNode, scope: IdentScope, *args, **kwargs):
        str_code = ""
        str_code += self.code_generator.gen_code_for_node(node.val, scope, *args, **kwargs) + "\n"
        kwargs['stloc'] = True
        str_code += self.code_generator.gen_code_for_node(node.var, scope, *args, **kwargs)
        return str_code

class VarNodeMSILCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(VarNodeMSILCodeGen, self).__init__(VariableDefinitionNode)

    def gen_code(self, node: VariableDefinitionNode, scope: IdentScope, *args, **kwargs):

        str_code = ""

        for var in node._vars:
            if isinstance(var, AssignNode):
                str_code += self.code_generator.gen_code_for_node(var.val, scope) + "\n"
                if var.var.node_type == TypeDesc.INT:
                    str_code += f"\tIL_%0.4X: stloc.s {var.node_ident.index}\n" % scope.byte_op_index
                elif var.var.node_type == TypeDesc.FLOAT:
                    str_code += f"\tIL_%0.4X: stloc.s val_{var.node_ident.index}\n" % scope.byte_op_index
                scope.byte_op_index += 2
        return str_code[:-1]


class TypeConvertNodeGen(NodeCodeGenerator):
    def __init__(self):
        super(TypeConvertNodeGen, self).__init__(TypeConvertNode)

    def gen_code(self, node: TypeConvertNode, scope: IdentScope, *args, **kwargs):
        str_code = ""

        str_code += self.code_generator.gen_code_for_node(node.expr, scope, *args, **kwargs) + "\n"

        str_code += f"\tIL_%0.4X: conv.{msil_stloc_types[node.node_type.string]}"  % scope.byte_op_index
        scope.byte_op_index += 1

        return str_code


class BinOpNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(BinOpNodeCodeGen, self).__init__(BinaryOperationNode)

    def gen_code(self, node: BinaryOperationNode, scope: IdentScope, *args, **kwargs):
        str_code = ""

        str_code += self.code_generator.gen_code_for_node(node.arg1, scope) + "\n"
        str_code += self.code_generator.gen_code_for_node(node.arg2, scope) + "\n"

        op = msil_operators[node.op][node.node_type.string]

        str_code += f"\tIL_%0.4X: {op}" % scope.byte_op_index
        scope.byte_op_index += 1

        return str_code


class ReturnNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(ReturnNodeCodeGen, self).__init__(ReturnNode)

    def gen_code(self, node: ReturnNode, scope: IdentScope, *args, **kwargs):
        str_code = ""

        str_code += self.code_generator.gen_code_for_node(node.expr, scope) + "\n"
        str_code += f"\tIL_%0.4X: ret" % scope.byte_op_index
        scope.byte_op_index += 1

        return str_code


class FunctionDefinitionNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(FunctionDefinitionNodeCodeGen, self).__init__(FunctionDefinitionNode)

    def gen_code(self, node: FunctionDefinitionNode, scope: IdentScope, *args, **kwargs):
        params = []

        for p in node.params.params:
            params.append(f"{msil_types_init[p.name.node_type.string]} p_{p.name.node_ident.index}")

        locals_str = ""

        vars_l = len([i for _, i in node.body.inner_scope.idents.items() if i.scope == ScopeType.LOCAL])

        if vars_l > 0:
            locals_str = \
                f"""
        .locals
        init
        (
            {self.code_generator.get_static_func_locals(node.body.inner_scope)}
        )"""

        if node.name.name == 'главный':
            func_name = "Main"
        else:
            func_name = f"func_{node.name.node_ident.index}"
        body_code = self.code_generator.gen_code_for_node(node.body, node.body.inner_scope)
        str_code = \
            f""".method public hidebysig static {msil_types_init[node.name.node_type.return_type.string]} {func_name}({", ".join(params)}) cil managed
  {{
    {".entrypoint" if func_name == "Main" else ""}
    {locals_str}
    
{body_code}

  }} // end of method
"""
        return str_code


code_gens = []

for name, obj in inspect.getmembers(sys.modules[__name__]):
    if inspect.isclass(obj) and issubclass(obj, NodeCodeGenerator) and obj != NodeCodeGenerator:
        code_gens.append(obj)


class RussianLanguageMSILGenerator(RussianLanguageCodeGenerator):
    def __init__(self):
        super().__init__()
        for n in code_gens:
            self.register_code_generator(n())

    def get_static_func_locals(self, vars: IdentScope):
        locals_vars_str = []
        for name, desc in vars.idents.items():
            if not desc.type.func and desc.scope in [ScopeType.GLOBAL, ScopeType.LOCAL]:
                locals_vars_str.append(f"\t[{desc.index}] {msil_types_init[desc.type.string]} val_{desc.index}")
        return ",\n".join(locals_vars_str)

    def gen_main_class(self, name, main_scope: IdentScope, main_code, before_main_code):
        return \
            f"""
.assembly extern mscorlib
{{
  .publickeytoken = (B7 7A 5C 56 19 34 E0 89 )                         // .z\V.4..
  .ver 4:0:0:0
}}
.assembly '{name}'
{{
}}
.module '{name}.exe'

// =============== CLASS MEMBERS DECLARATION ===================

.class public auto ansi beforefieldinit {name.capitalize()}
       extends [mscorlib]System.Object
{{

  {before_main_code}
    
  {main_code}

  .method public hidebysig specialname rtspecialname 
          instance void  .ctor() cil managed
  {{
    IL_0000:  ldarg.0
    IL_0001:  call       instance void [mscorlib]System.Object::.ctor()
    IL_0006:  ret
  }} // end of method {name.capitalize()}::.ctor

}} // end of class {name.capitalize()}

"""
