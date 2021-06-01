import os

from pyparsing import unicode

from src.code.generation.msil.msil_gen import RussianLanguageMSILGenerator
from src.code_compile import compile_code, run_exe
from src.semantic import scopes
import src.semantic.node_handlers as semantic_an
from src.semantic.scopes import SemanticException
from src.syntax.ast_tree import FunctionDefinitionNode
from src.syntax.parser import RussianLanguageCodeSyntaxAnalyser


if __name__ == '__main__':

    parser = RussianLanguageCodeSyntaxAnalyser()
    semantic_analyser = semantic_an.get_global_semantic_analyser()
    print()

    with open("../resources/example8.ru", 'r', encoding='utf-8') as code:
        file_str = unicode(code.read())

    prog = parser.parse_string(file_str)
    print(*prog.tree, sep=os.linesep)

    print('semantic_check:')
    try:
        scope = scopes.prepare_global_scope(semantic_analyser)
        semantic_analyser.process_node(prog, scope, disable_hard_check=False)

        main = scope.get_ident("главный")

        if not main or not main.type.func:
            raise SemanticException("Нет точки входа в программу (функция главный)")

        print(*prog.tree, sep=os.linesep)

        code_gen = RussianLanguageMSILGenerator()
        main_code = code_gen.gen_code_for_node(main.node, scope)

        before_main = ""

        for stmt in prog.exprs:
            if isinstance(stmt, FunctionDefinitionNode) and stmt.name.name == 'главный':
                pass
            else:
                before_main += code_gen.gen_code_for_node(stmt, scope)

        asbl = code_gen.gen_main_class("main", main.node.inner_scope, main_code, before_main)
        print(asbl)
        exe = compile_code(asbl, "../output/main.ilasm")
        print("Run code result...")
        print(run_exe(exe))

    except SemanticException as e:
        print('Ошибка: {}'.format(e.message))
    print()
