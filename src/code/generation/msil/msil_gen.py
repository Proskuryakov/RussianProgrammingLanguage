import inspect
import sys

from src.code.generation.common.code_generator import RussianLanguageCodeGenerator, NodeCodeGenerator, LabelProvider
from src.semantic.scopes import IdentScope
from src.semantic.scopes_include import ScopeType
from src.semantic.types import TypeDesc
from src.syntax.ast_tree import VariableDefinitionNode, AssignNode, LiteralNode, StatementListNode, StatementNode, \
    ExpressionNode, BinaryOperationNode, RusIdentifierNode, CallNode, ParamNode, ExpressionListNode, \
    FunctionDefinitionNode, ReturnNode, TypeConvertNode, IfNode, ForNode
from src.syntax.types import BinOp, inverse_op

msil_types_init = {TypeDesc.INT.string: 'int32',
                   TypeDesc.VOID.string: "void",
                   TypeDesc.FLOAT.string: "float64",
                   TypeDesc.STR.string: "string"}

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
    },
    BinOp.MORE_E: {
        TypeDesc.INT.string: 'bge.s',
        TypeDesc.BOOL.string: 'bge.s',
        TypeDesc.FLOAT.string: 'bge.s'
    },
    BinOp.MORE: {
        TypeDesc.INT.string: 'bgt.s',
        TypeDesc.BOOL.string: 'bgt.s',
        TypeDesc.FLOAT.string: 'bgt.s'
    },
    BinOp.LESS_E: {
        TypeDesc.INT.string: 'ble.s',
        TypeDesc.BOOL.string: 'ble.s',
        TypeDesc.FLOAT.string: 'ble.s'
    },
    BinOp.LESS: {
        TypeDesc.INT.string: 'blt.s',
        TypeDesc.BOOL.string: 'blt.s',
        TypeDesc.FLOAT.string: 'blt.s'
    },
    BinOp.EQ: {
        TypeDesc.INT.string: 'beq.s',
        TypeDesc.BOOL.string: 'beq.s',
        TypeDesc.FLOAT.string: 'beq.s'
    },
    BinOp.NOT_EQ: {
        TypeDesc.INT.string: 'bne.un.s',
        TypeDesc.BOOL.string: 'bne.un.s',
        TypeDesc.FLOAT.string: 'bne.un.s'
    }

}

msil_built_in_fuctions = {"вывод": "[mscorlib]System.Console::Write",
                          "вывод_перенос": "[mscorlib]System.Console::WriteLine",
                          "вывод_целый": "[mscorlib]System.Console::WriteLine",
                          "вывод_вещ": "[mscorlib]System.Console::WriteLine"}


class StatementListNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(StatementListNodeCodeGen, self).__init__(StatementListNode)

    def gen_code(self, node: StatementListNode, scope: IdentScope, label_provider: LabelProvider, *args, **kwargs):
        str_code = ""
        for stmt in node.exprs:
            str_code += self.code_generator.gen_code_for_node(stmt, scope, label_provider, *args, **kwargs)
            str_code += "\n"
        return str_code


class ExpressionListNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(ExpressionListNodeCodeGen, self).__init__(ExpressionListNode)

    def gen_code(self, node: ExpressionListNode, scope: IdentScope, label_provider: LabelProvider, *args, **kwargs):
        str_code = ""

        for expr in node.exprs:
            str_code += self.code_generator.gen_code_for_node(expr, scope, label_provider, *args, **kwargs) + "\n"

        return str_code[:-1]


class CallNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(CallNodeCodeGen, self).__init__(CallNode)

    def gen_code(self, node: CallNode, scope: IdentScope, label_provider: LabelProvider, *args, **kwargs):

        str_code = ""

        str_code += self.code_generator.gen_code_for_node(node.params, scope, label_provider, *args, **kwargs) + "\n"

        params_types = []
        for p in node.params.exprs:
            params_types.append(msil_types_init[p.node_type.string])

        if node.func.node_ident.built_in:
            str_code += f"\t{label_provider.get_usual_label()}: call {msil_types_init[node.node_type.string]} " \
                        f"{msil_built_in_fuctions[node.func.node_ident.name]}({','.join(params_types)})"
        else:
            ident = scope.get_ident(node.func.name)
            str_code += f"\t{label_provider.get_usual_label()}: call {msil_types_init[node.node_type.string]} " \
                        f"Main::func_{ident.index}({','.join(params_types)})"
        return str_code


class RusIdentifierNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(RusIdentifierNodeCodeGen, self).__init__(RusIdentifierNode)

    def gen_code(self, node: RusIdentifierNode, scope: IdentScope, label_provider: LabelProvider, *args, **kwargs):
        str_code = ""
        if 'stloc' in kwargs and kwargs['stloc']:
            if node.node_ident.scope != ScopeType.PARAM:
                if node.node_type == TypeDesc.INT:
                    str_code = f"\t{label_provider.get_usual_label()}: stloc.s {node.node_ident.index}"
                elif node.node_type == TypeDesc.FLOAT:
                    str_code = f"\t{label_provider.get_usual_label()}: stloc.s val_{node.node_ident.index}"
            else:
                if node.node_type == TypeDesc.INT:
                    str_code = f"\t{label_provider.get_usual_label()}: ldarg.s {node.node_ident.index}"
                elif node.node_type == TypeDesc.FLOAT:
                    str_code = f"\t{label_provider.get_usual_label()}: ldarg.s p_{node.node_ident.index}"
        else:
            if node.node_ident.scope != ScopeType.PARAM:
                if node.node_type == TypeDesc.INT:
                    str_code = f"\t{label_provider.get_usual_label()}: ldloc.s {node.node_ident.index}"
                elif node.node_type == TypeDesc.FLOAT:
                    str_code = f"\t{label_provider.get_usual_label()}: ldloc.s val_{node.node_ident.index}"
            else:
                if node.node_type == TypeDesc.INT:
                    str_code = f"\t{label_provider.get_usual_label()}: ldarg.s {node.node_ident.index}"
                elif node.node_type == TypeDesc.FLOAT:
                    str_code = f"\t{label_provider.get_usual_label()}: ldarg.s p_{node.node_ident.index}"
        return str_code


class LiteralNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(LiteralNodeCodeGen, self).__init__(LiteralNode)

    def gen_code(self, node: LiteralNode, scope: IdentScope, label_provider: LabelProvider, *args, **kwargs):

        if not node.literal:
            return ""

        str_code = ""

        if node.node_type == TypeDesc.INT:
            str_code = f"\t{label_provider.get_usual_label()}: ldc.{msil_stloc_types[node.node_type.string]}.s {node.value}"
        elif node.node_type == TypeDesc.FLOAT:
            str_code = f"\t{label_provider.get_usual_label()}: ldc.{msil_stloc_types[node.node_type.string]} {node.value}"
        elif node.node_type == TypeDesc.STR:
            str_bytes = [f"%0.2X" % b for b in bytes(node.value, 'utf-8')]
            str_code = f"\t{label_provider.get_usual_label()}: ldstr bytearray ({' '.join(str_bytes)} )"
        return str_code


class AssignNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(AssignNodeCodeGen, self).__init__(AssignNode)

    def gen_code(self, node: AssignNode, scope: IdentScope, label_provider: LabelProvider, *args, **kwargs):
        str_code = ""
        str_code += self.code_generator.gen_code_for_node(node.val, scope, label_provider, *args, **kwargs) + "\n"
        kwargs['stloc'] = True
        str_code += self.code_generator.gen_code_for_node(node.var, scope, label_provider, *args, **kwargs)
        return str_code


class VarNodeMSILCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(VarNodeMSILCodeGen, self).__init__(VariableDefinitionNode)

    def gen_code(self, node: VariableDefinitionNode, scope: IdentScope, label_provider: LabelProvider, *args, **kwargs):

        str_code = ""

        for var in node._vars:
            if isinstance(var, AssignNode):
                str_code += self.code_generator.gen_code_for_node(var.val, scope, label_provider, *args,
                                                                  **kwargs) + "\n"
                if var.var.node_type == TypeDesc.INT:
                    str_code += f"\t{label_provider.get_usual_label()}: stloc.s {var.node_ident.index}\n"
                elif var.var.node_type == TypeDesc.FLOAT:
                    str_code += f"\t{label_provider.get_usual_label()}: stloc.s val_{var.node_ident.index}\n"
        return str_code[:-1]


class TypeConvertNodeGen(NodeCodeGenerator):
    def __init__(self):
        super(TypeConvertNodeGen, self).__init__(TypeConvertNode)

    def gen_code(self, node: TypeConvertNode, scope: IdentScope, label_provider: LabelProvider, *args, **kwargs):
        str_code = ""

        str_code += self.code_generator.gen_code_for_node(node.expr, scope, label_provider, *args, **kwargs) + "\n"

        str_code += f"\t{label_provider.get_usual_label()}: conv.{msil_stloc_types[node.node_type.string]}"

        return str_code


class BinOpNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(BinOpNodeCodeGen, self).__init__(BinaryOperationNode)

    def gen_code(self, node: BinaryOperationNode, scope: IdentScope, label_provider: LabelProvider, *args, **kwargs):
        str_code = ""

        str_code += self.code_generator.gen_code_for_node(node.arg1, scope, label_provider, *args, **kwargs) + "\n"
        str_code += self.code_generator.gen_code_for_node(node.arg2, scope, label_provider, *args, **kwargs) + "\n"

        op = msil_operators[node.op][node.node_type.string]

        str_code += f"\t{label_provider.get_usual_label()}: {op}"

        return str_code

    @staticmethod
    def logical_expression_resolve(gen: RussianLanguageCodeGenerator,
                                   node: BinaryOperationNode, scope: IdentScope, label_provider: 'LabelProvider',
                                   if_false_label: str,
                                   if_true_label: str,
                                   *args, **kwargs):
        str_code = ""
        if node.op not in [BinOp.LOGICAL_OR, BinOp.LOGICAL_AND]:
            # in-place resolve
            if 'negative' not in kwargs or kwargs['negative']:
                inv_op = inverse_op(node.op)
                str_code += gen.gen_code_for_node(node.arg1, scope, label_provider, *args, **kwargs) + "\n"
                str_code += gen.gen_code_for_node(node.arg2, scope, label_provider, *args, **kwargs) + "\n"
                str_code += f"\t{label_provider.get_usual_label()}: {msil_operators[inv_op][node.node_type.string]}" \
                            f" {if_false_label}\n"
                str_code += f"\tbr.s {if_true_label}"
                return str_code
            else:
                str_code += gen.gen_code_for_node(node.arg1, scope, label_provider, *args, **kwargs) + "\n"
                str_code += gen.gen_code_for_node(node.arg2, scope, label_provider, *args, **kwargs) + "\n"
                str_code += f"\t{label_provider.get_usual_label()}: {msil_operators[node.op][node.node_type.string]}" \
                            f" {if_true_label}\n"
                str_code += f"\tbr.s {if_false_label}"
                return str_code

        if node.op == BinOp.LOGICAL_OR:
            second_arg_label = label_provider.get_jump_label()
            str_code = ""
            kwargs['negative'] = False
            str_code += BinOpNodeCodeGen.logical_expression_resolve(gen, node.arg1, scope, label_provider,
                                                                    second_arg_label,
                                                                    if_true_label, *args, **kwargs) + "\n"
            kwargs['negative'] = False
            str_code += BinOpNodeCodeGen.logical_expression_resolve(gen, node.arg2, scope, label_provider,
                                                                    if_false_label,
                                                                    if_true_label, *args, **kwargs)
        elif node.op == BinOp.LOGICAL_AND:
            second_arg_label = label_provider.get_jump_label()
            str_code = ""
            kwargs['negative'] = False
            str_code += BinOpNodeCodeGen.logical_expression_resolve(gen, node.arg1, scope, label_provider,
                                                                    if_false_label,
                                                                    second_arg_label, *args, **kwargs) + "\n"
            kwargs['negative'] = False
            str_code += BinOpNodeCodeGen.logical_expression_resolve(gen, node.arg2, scope, label_provider,
                                                                    if_false_label,
                                                                    if_true_label, *args, **kwargs)
        return str_code


class IfNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(IfNodeCodeGen, self).__init__(IfNode)

    def _gen_if_node(self, node: IfNode, scope: IdentScope, label_provider: 'MSILLabelProvider', *args, **kwargs):
        if_false_label = label_provider.get_jump_label()
        if_true_label = label_provider.get_jump_label()

        str_code = ""

        str_code += BinOpNodeCodeGen.logical_expression_resolve(self.code_generator,
                                                                node.cond, scope, label_provider, if_false_label,
                                                                if_true_label, *args, **kwargs) + "\n"

        label_provider.push_label(if_true_label)
        str_code += self.code_generator.gen_code_for_node(node.if_stmt, scope, label_provider, *args, **kwargs) + "\n"

        label_provider.push_label(if_false_label)

        return str_code

    def _gen_if_else_node(self, node: IfNode, scope: IdentScope, label_provider: 'MSILLabelProvider', *args, **kwargs):
        if_false_label = label_provider.get_jump_label()
        if_true_label = label_provider.get_jump_label()
        next_code_label = label_provider.get_jump_label()

        str_code = ""

        str_code += BinOpNodeCodeGen.logical_expression_resolve(self.code_generator,
                                                                node.cond, scope, label_provider, if_false_label,
                                                                if_true_label, *args, **kwargs) + "\n"

        label_provider.push_label(if_true_label)
        str_code += self.code_generator.gen_code_for_node(node.if_stmt, scope, label_provider, *args, **kwargs) + "\n"
        str_code += f"\t{label_provider.get_usual_label()}: br.s {next_code_label}\n"
        label_provider.push_label(if_false_label)
        str_code += self.code_generator.gen_code_for_node(node.else_stmt, scope, label_provider, *args, **kwargs) + "\n"
        label_provider.push_label(next_code_label)

        return str_code

    def gen_code(self, node: IfNode, scope: IdentScope, label_provider: 'MSILLabelProvider', *args, **kwargs):
        return self._gen_if_else_node(node, scope, label_provider, *args, **kwargs) if node.else_stmt and len(node.else_stmt.childs) > 0 \
            else self._gen_if_node(node, scope, label_provider, *args, **kwargs)


class ForNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(ForNodeCodeGen, self).__init__(ForNode)

    def gen_code(self, node: ForNode, scope: IdentScope, label_provider: 'MSILLabelProvider', *args, **kwargs):
        check_label = label_provider.get_jump_label()
        body_label = label_provider.get_jump_label()
        next_code_label = label_provider.get_jump_label()

        str_code = self.code_generator.gen_code_for_node(node.init, scope, label_provider, *args, **kwargs) + "\n"
        str_code += f"\tbr.s {check_label}\n"

        label_provider.push_label(body_label)
        str_code += self.code_generator.gen_code_for_node(node.body, scope, label_provider, *args, **kwargs) + "\n"

        str_code += self.code_generator.gen_code_for_node(node.step, scope, label_provider,  *args, **kwargs) + "\n"
        label_provider.push_label(check_label)
        str_code += BinOpNodeCodeGen.logical_expression_resolve(self.code_generator,
                                                                node.cond, scope, label_provider, next_code_label,
                                                                body_label)
        label_provider.push_label(next_code_label)

        return str_code


class ReturnNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(ReturnNodeCodeGen, self).__init__(ReturnNode)

    def gen_code(self, node: ReturnNode, scope: IdentScope, label_provider: LabelProvider, *args, **kwargs):
        str_code = ""

        str_code += self.code_generator.gen_code_for_node(node.expr, scope, label_provider, *args, **kwargs) + "\n"
        str_code += f"\t{label_provider.get_usual_label()}: ret"

        return str_code


class FunctionDefinitionNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(FunctionDefinitionNodeCodeGen, self).__init__(FunctionDefinitionNode)

    def gen_code(self, node: FunctionDefinitionNode, scope: IdentScope, label_provider: LabelProvider, *args, **kwargs):
        params = []

        for p in node.params.params:
            params.append(f"{msil_types_init[p.name.node_type.string]} p_{p.name.node_ident.index}")

        locals_str = ""

        vars_l = len([i for _, i in node.inner_scope.idents.items() if i.scope == ScopeType.LOCAL])

        if vars_l > 0:
            locals_str = \
                f"""
        .locals
        init
        (
            {self.code_generator.get_static_func_locals(node.inner_scope)}
        )"""

        if node.name.name == 'главный':
            func_name = "Main"
        else:
            func_name = f"func_{node.name.node_ident.index}"
        body_code = self.code_generator.gen_code_for_node(node.body, node.inner_scope, label_provider, *args, **kwargs)
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


class MSILLabelProvider(LabelProvider):
    def __init__(self):
        super(MSILLabelProvider, self).__init__()
        self.label_counter = 0
        self.pushed = []

    def get_jump_label(self):
        label = f"JP_%0.4X" % self.label_counter
        self.label_counter += 1
        return label

    def get_usual_label(self):
        if len(self.pushed) > 0:
            return self.pushed.pop()
        label = f"IL_%0.4X" % self.label_counter
        self.label_counter += 1
        return label

    def push_label(self, label: str):
        self.pushed.append(label)


class RussianLanguageMSILGenerator(RussianLanguageCodeGenerator):
    def __init__(self):
        super().__init__()
        for n in code_gens:
            self.register_code_generator(n())

    def start_gen_code(self, node, scope: IdentScope, *args, **kwargs):
        return self.gen_code_for_node(node, scope, MSILLabelProvider(), *args, **kwargs)

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
