import os

from pyparsing import unicode

from src.semantic import scopes
import src.semantic.node_handlers as semantic_an
from src.semantic.scopes import SemanticException
from src.syntax.parser import RussianLanguageCodeSyntaxAnalyser


if __name__ == '__main__':

    parser = RussianLanguageCodeSyntaxAnalyser()
    semantic_analyser = semantic_an.get_global_semantic_analyser()
    print()

    with open("../resources/example7", 'r', encoding='utf-8') as code:
        file_str = unicode(code.read())

    prog = parser.parse_string(file_str)
    print(*prog.tree, sep=os.linesep)

    print('semantic_check:')
    try:
        scope = scopes.prepare_global_scope(semantic_analyser)
        semantic_analyser.process_node(prog, scope)
        print(*prog.tree, sep=os.linesep)
    except SemanticException as e:
        print('Ошибка: {}'.format(e.message))
    print()
