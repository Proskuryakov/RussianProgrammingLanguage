import inspect
import sys

from src.code.generation.common.code_generator import RussianLanguageCodeGenerator, NodeCodeGenerator, LabelProvider
from src.semantic.scopes import IdentScope
from src.semantic.scopes_include import ScopeType
from src.semantic.types import TypeDesc
from src.syntax.ast_tree import VariableDefinitionNode, AssignNode, LiteralNode, StatementListNode, StatementNode, \
    ExpressionNode, BinaryOperationNode, RusIdentifierNode, CallNode, ParamNode, ExpressionListNode, \
    FunctionDefinitionNode, ReturnNode, TypeConvertNode, ForNode, IfNode
from src.syntax.types import BinOp, inverse_op

jbc_types_init = {TypeDesc.INT.string: 'I', TypeDesc.VOID.string: "V", TypeDesc.FLOAT.string: "F"}

jbc_stloc_types = {TypeDesc.INT.string: 'i', TypeDesc.FLOAT.string: "f"}

jbc_compare_additions = \
    {
        TypeDesc.INT.string: "",
        TypeDesc.FLOAT.string: "fcmpl"
    }

jbc_operators = {
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
        TypeDesc.INT.string: 'if_icmpge',
        TypeDesc.BOOL.string: 'if_icmpge',
        TypeDesc.FLOAT.string: 'ifge'
    },
    BinOp.MORE: {
        TypeDesc.INT.string: 'if_icmpgt',
        TypeDesc.BOOL.string: 'if_icmpgt',
        TypeDesc.FLOAT.string: 'ifgt'
    },
    BinOp.LESS_E: {
        TypeDesc.INT.string: 'if_icmple',
        TypeDesc.BOOL.string: 'if_icmple',
        TypeDesc.FLOAT.string: 'ifle'
    },
    BinOp.LESS: {
        TypeDesc.INT.string: 'if_icmplt',
        TypeDesc.BOOL.string: 'if_icmplt',
        TypeDesc.FLOAT.string: 'iflt'
    },
    BinOp.EQ: {
        TypeDesc.INT.string: 'if_icmpeq',
        TypeDesc.BOOL.string: 'if_icmpeq',
        TypeDesc.FLOAT.string: 'ifeq'
    },
    BinOp.NOT_EQ: {
        TypeDesc.INT.string: 'if_icmpne',
        TypeDesc.BOOL.string: 'if_icmpne',
        TypeDesc.FLOAT.string: 'ifne'
    }
}

jbc_built_in_fuctions = {"вывод_целый": "invokevirtual java/io/PrintStream/println(I)V",
                         "вывод_вещ": "invokevirtual java/io/PrintStream/println(F)V"}
jbc_built_in_load_func = {"вывод_целый": "getstatic java/lang/System/out Ljava/io/PrintStream;",
                          "вывод_вещ": "getstatic java/lang/System/out Ljava/io/PrintStream;"}


class StatementListNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(StatementListNodeCodeGen, self).__init__(StatementListNode)

    def gen_code(self, node: StatementListNode, scope: IdentScope, label_provider: 'LabelProvider', *args, **kwargs):
        str_code = ""
        for stmt in node.exprs:
            str_code += self.code_generator.gen_code_for_node(stmt, scope, label_provider, *args, **kwargs)
            str_code += "\n"
        return str_code


class ExpressionListNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(ExpressionListNodeCodeGen, self).__init__(ExpressionListNode)

    def gen_code(self, node: ExpressionListNode, scope: IdentScope, label_provider: 'LabelProvider', *args, **kwargs):
        str_code = ""

        for expr in node.exprs:
            str_code += self.code_generator.gen_code_for_node(expr, scope, label_provider, *args, **kwargs) + "\n"

        return str_code[:-1]


class CallNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(CallNodeCodeGen, self).__init__(CallNode)

    def gen_code(self, node: CallNode, scope: IdentScope, label_provider: 'LabelProvider', *args, **kwargs):

        str_code = ""

        if node.func.node_ident.built_in:
            str_code += f"\t{label_provider.get_usual_label()}: {jbc_built_in_load_func[node.func.node_ident.name]}\n"

        str_code += self.code_generator.gen_code_for_node(node.params, scope, label_provider, *args, **kwargs) + "\n"

        params_types = []
        for p in node.params.exprs:
            params_types.append(jbc_types_init[p.node_type.string])

        if node.func.node_ident.built_in:
            str_code += f"\t{label_provider.get_usual_label()}: {jbc_built_in_fuctions[node.func.node_ident.name]}"
        else:
            ident = scope.get_ident(node.func.name)
            str_code += f"\t{label_provider.get_usual_label()}: invokestatic\t\t\t\t" \
                        f"Main/func_{ident.index}({''.join(params_types)}){jbc_types_init[node.node_type.string]}"
        return str_code


class RusIdentifierNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(RusIdentifierNodeCodeGen, self).__init__(RusIdentifierNode)

    def gen_code(self, node: RusIdentifierNode, scope: IdentScope, label_provider: 'LabelProvider', *args, **kwargs):

        locals_offset = 0
        if 'locals_offset' in kwargs:
            locals_offset = kwargs['locals_offset']
        if node.node_ident.scope != ScopeType.PARAM:
            if "store" in kwargs:
                str_code = f"\t{label_provider.get_usual_label()}: {jbc_stloc_types[node.node_type.string]}store\t\t\t\t{node.node_ident.index + locals_offset}"
            else:
                str_code = f"\t{label_provider.get_usual_label()}: {jbc_stloc_types[node.node_type.string]}load\t\t\t\t{node.node_ident.index + locals_offset}"
        else:
            if "store" in kwargs:
                str_code = f"\t{label_provider.get_usual_label()}: {jbc_stloc_types[node.node_type.string]}store\t\t\t\t{node.node_ident.index}"
            else:
                str_code = f"\t{label_provider.get_usual_label()}: {jbc_stloc_types[node.node_type.string]}load\t\t\t\t{node.node_ident.index}"
        return str_code


class LiteralNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(LiteralNodeCodeGen, self).__init__(LiteralNode)

    def gen_code(self, node: LiteralNode, scope: IdentScope, label_provider: 'LabelProvider', *args, **kwargs):

        if not node.literal:
            return ""

        str_code = ''

        if node.node_type == TypeDesc.INT:
            str_code = f"\t{label_provider.get_usual_label()}: bipush\t\t\t\t{node.value}"
        if node.node_type == TypeDesc.FLOAT:
            str_code = f"\t{label_provider.get_usual_label()}: ldc\t\t\t\t{node.value}"
        return str_code


class AssignNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(AssignNodeCodeGen, self).__init__(AssignNode)

    def gen_code(self, node: AssignNode, scope: IdentScope, label_provider: LabelProvider, *args, **kwargs):
        str_code = ""
        str_code += self.code_generator.gen_code_for_node(node.val, scope, label_provider, *args, **kwargs) + "\n"
        kwargs['store'] = True
        str_code += self.code_generator.gen_code_for_node(node.var, scope, label_provider, *args, **kwargs)
        return str_code


class TypeConvertNodeGen(NodeCodeGenerator):
    def __init__(self):
        super(TypeConvertNodeGen, self).__init__(TypeConvertNode)

    def gen_code(self, node: TypeConvertNode, scope: IdentScope, label_provider: LabelProvider, *args, **kwargs):
        str_code = ""

        str_code += self.code_generator.gen_code_for_node(node.expr, scope, label_provider, *args, **kwargs) + "\n"

        str_code += f"\t{label_provider.get_usual_label()}: {jbc_stloc_types[node.expr.node_type.string]}2{jbc_stloc_types[node.node_type.string]}"

        return str_code


class VarNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(VarNodeCodeGen, self).__init__(VariableDefinitionNode)

    def gen_code(self, node: VariableDefinitionNode, scope: IdentScope, label_provider: 'LabelProvider', *args,
                 **kwargs):

        str_code = ""

        for var in node._vars:
            if isinstance(var, AssignNode):
                aaa = 4
                print(aaa)
                str_code += self.code_generator.gen_code_for_node(var.val, scope, label_provider, *args,
                                                                  **kwargs) + "\n"
                kwargs['store'] = 'store'
                str_code += self.code_generator.gen_code_for_node(var.var, scope, label_provider, *args,
                                                                  **kwargs) + "\n"
        return str_code[:-1]


class BinOpNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(BinOpNodeCodeGen, self).__init__(BinaryOperationNode)

    def gen_code(self, node: BinaryOperationNode, scope: IdentScope, label_provider: LabelProvider, *args, **kwargs):
        str_code = ""

        str_code += self.code_generator.gen_code_for_node(node.arg1, scope, label_provider, *args, **kwargs) + "\n"
        str_code += self.code_generator.gen_code_for_node(node.arg2, scope, label_provider, *args, **kwargs) + "\n"

        op = jbc_operators[node.op][node.node_type.string]

        str_code += f"\t{label_provider.get_usual_label()}: {jbc_stloc_types[node.node_type.string]}{op}"

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
                op_type = node.arg1.node_type
                addition = jbc_compare_additions[op_type.string]
                if addition and addition != "":
                    str_code += f"\t{label_provider.get_usual_label()}: {addition}\n"
                str_code += f"\t{label_provider.get_usual_label()}: {jbc_operators[inv_op][op_type.string]}" \
                            f" {if_false_label}\n"
                str_code += f"\t{label_provider.get_usual_label()}: goto {if_true_label}"
                return str_code
            else:
                str_code += gen.gen_code_for_node(node.arg1, scope, label_provider, *args, **kwargs) + "\n"
                str_code += gen.gen_code_for_node(node.arg2, scope, label_provider, *args, **kwargs) + "\n"
                op_type = node.arg1.node_type
                addition = jbc_compare_additions[op_type.string]
                if addition and addition != "":
                    str_code += f"\t{label_provider.get_usual_label()}: {addition}\n"
                str_code += f"\t{label_provider.get_usual_label()}: {jbc_operators[node.op][op_type.string]}" \
                            f" {if_true_label}\n"
                str_code += f"\t{label_provider.get_usual_label()}: goto {if_false_label}"
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

    def _gen_if_node(self, node: IfNode, scope: IdentScope, label_provider: 'LabelProvider', *args, **kwargs):
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

    def _gen_if_else_node(self, node: IfNode, scope: IdentScope, label_provider: 'LabelProvider', *args, **kwargs):
        if_false_label = label_provider.get_jump_label()
        if_true_label = label_provider.get_jump_label()
        next_code_label = label_provider.get_jump_label()

        str_code = ""

        str_code += BinOpNodeCodeGen.logical_expression_resolve(self.code_generator,
                                                                node.cond, scope, label_provider, if_false_label,
                                                                if_true_label, *args, **kwargs) + "\n"

        label_provider.push_label(if_true_label)
        str_code += self.code_generator.gen_code_for_node(node.if_stmt, scope, label_provider, *args, **kwargs) + "\n"
        str_code += f"\t{label_provider.get_usual_label()}: goto {next_code_label}\n"
        label_provider.push_label(if_false_label)
        str_code += self.code_generator.gen_code_for_node(node.else_stmt, scope, label_provider, *args, **kwargs) + "\n"
        label_provider.push_label(next_code_label)

        return str_code

    def gen_code(self, node: IfNode, scope: IdentScope, label_provider: 'LabelProvider', *args, **kwargs):
        return self._gen_if_else_node(node, scope, label_provider, *args, **kwargs) if node.else_stmt and len(node.else_stmt.childs) > 0 \
            else self._gen_if_node(node, scope, label_provider, *args, **kwargs)

class ForNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(ForNodeCodeGen, self).__init__(ForNode)

    def gen_code(self, node: ForNode, scope: IdentScope, label_provider: 'LabelProvider', *args, **kwargs):
        check_label = label_provider.get_jump_label()
        body_label = label_provider.get_jump_label()
        next_code_label = label_provider.get_jump_label()

        str_code = self.code_generator.gen_code_for_node(node.init, scope, label_provider, *args, **kwargs) + "\n"
        str_code += f"\t{label_provider.get_usual_label()}: goto {check_label}\n"

        label_provider.push_label(body_label)
        str_code += self.code_generator.gen_code_for_node(node.body, scope, label_provider, *args, **kwargs) + "\n"

        str_code += self.code_generator.gen_code_for_node(node.step, scope, label_provider, *args, **kwargs) + "\n"
        label_provider.push_label(check_label)
        str_code += BinOpNodeCodeGen.logical_expression_resolve(self.code_generator,
                                                                node.cond, scope, label_provider, next_code_label,
                                                                body_label, *args, **kwargs)
        label_provider.push_label(next_code_label)

        return str_code


class ReturnNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(ReturnNodeCodeGen, self).__init__(ReturnNode)

    def gen_code(self, node: ReturnNode, scope: IdentScope, label_provider: 'LabelProvider', *args, **kwargs):
        str_code = ""

        str_code += self.code_generator.gen_code_for_node(node.expr, scope, label_provider, *args, **kwargs) + "\n"
        if not node.expr.node_type:
            str_code += f"\t{label_provider.get_usual_label()}: return"
        else:
            str_code += f"\t{label_provider.get_usual_label()}: {jbc_stloc_types[node.expr.node_type.string]}return"

        return str_code


class FunctionDefinitionNodeCodeGen(NodeCodeGenerator):
    def __init__(self):
        super(FunctionDefinitionNodeCodeGen, self).__init__(FunctionDefinitionNode)

    def gen_code(self, node: FunctionDefinitionNode, scope: IdentScope, label_provider: 'LabelProvider', *args,
                 **kwargs):
        params = []

        for p in node.params.params:
            params.append(f"{jbc_types_init[p.name.node_type.string]}")

        locals_c = len([i for _, i in node.body.inner_scope.idents.items() if i.scope != ScopeType.PARAM])

        locals_c += len(params)

        if node.name.name == 'главный':
            locals_c = 1
            func_name = "main"
            params = ["[Ljava/lang/String;"]
        else:
            func_name = f"func_{node.name.node_ident.index}"
            kwargs['locals_offset'] = locals_c
        kwargs['locals_offset'] = locals_c
        body_code = self.code_generator.gen_code_for_node(node.body, node.body.inner_scope, label_provider, *args,
                                                          **kwargs)
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


class JBCLabelProvider(LabelProvider):
    def __init__(self):
        super(JBCLabelProvider, self).__init__()
        self.label_counter = 0
        self.pushed = []

    def get_jump_label(self):
        label = f"{self.label_counter}"
        self.label_counter += 1
        return label

    def get_usual_label(self):
        if len(self.pushed) > 0:
            return self.pushed.pop()
        label = f"{self.label_counter}"
        self.label_counter += 1
        return label

    def push_label(self, label: str):
        self.pushed.append(label)


class RussianLanguageJBCGenerator(RussianLanguageCodeGenerator):
    def __init__(self):
        super().__init__()
        for n in code_gens:
            self.register_code_generator(n())

    def start_gen_code(self, node, scope: IdentScope, *args, **kwargs):
        return self.gen_code_for_node(node, scope, JBCLabelProvider(), *args, **kwargs)

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
