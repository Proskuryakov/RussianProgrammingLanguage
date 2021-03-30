import os

from pyparsing import unicode

from src.syntax.parser import RussianLanguageCodeSyntaxAnalyser


if __name__ == '__main__':

    parser = RussianLanguageCodeSyntaxAnalyser()
    print()

    with open("../resources/example6", 'r', encoding='utf-8') as code:
        file_str = unicode(code.read())

    prog = parser.parse_string(file_str)
    print(*prog.tree, sep=os.linesep)
