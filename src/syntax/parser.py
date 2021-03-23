import inspect
import string
from contextlib import suppress

import pyparsing as pp
from pyparsing import pyparsing_common as ppc
from varname import nameof

from .ast_tree import *

b = BinOp.ADD


class RussianLanguageCodeSyntaxAnalyser:
    def __init__(self):
        self.rules = dict()
        self.start_rule = None
        self._init_rules()
        self._set_parser_action()

    def _register_rule_as(self, name, rule):
        self.rules[name] = rule
        
    def _init_rules(self):
        LPAR, RPAR = pp.Literal('(').suppress(), pp.Literal(')').suppress()
        ASSIGN_OPERATOR = pp.Literal('=')
        SEMI, COMMA = pp.Literal(';').suppress(), pp.Literal(',').suppress()


        rus_alphas = u'йцукенгшщзхъфывапролджэячсмитьбюёЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮЁ'
        rus_digits = u'0123456789'

        rus = rus_digits + rus_alphas

        # TRUE, FALSE = pp.Keyword('истина'), pp.Keyword('ложь')

        number = ppc.fnumber
        self._register_rule_as(nameof(number), number)

        rus_identifier = pp.Word(rus + '_').setName("rus_identifier")
        self._register_rule_as(nameof(rus_identifier), rus_identifier)

        type = rus_identifier.copy().setName("type")
        self._register_rule_as(nameof(type), type)

        expression = pp.Forward()
        self._register_rule_as(nameof(expression), expression)

        group = (
                rus_identifier |
                number |
                LPAR + expression + RPAR
        )

        assign = rus_identifier + ASSIGN_OPERATOR.suppress() + expression
        self._register_rule_as(nameof(assign), assign)

        variable_defenition = type + assign
        self._register_rule_as(nameof(variable_defenition), variable_defenition)

        expression << group

        statement = (
                variable_defenition + SEMI |
                assign + SEMI)
        self._register_rule_as(nameof(statement), statement)

        statement_list = pp.ZeroOrMore(statement)
        self._register_rule_as(nameof(statement_list), statement_list)

        program = statement_list.ignore(pp.cStyleComment).ignore(pp.dblSlashComment) + pp.StringEnd()
        self._register_rule_as(nameof(program), program)

        start = program
        self._register_rule_as(nameof(start), start)
        self.start_rule = start

    def _set_parser_action(self):
        for rule_name, rule in self.rules.items():
            self.set_parse_action_magic(rule_name, rule)

    def get_parser(self):
        return self.start_rule

    def parse_string(self, string) -> StatementListNode:
        return self.get_parser().parseString(string)[0]

    def set_parse_action_magic(self, rule_name: str, parser: pp.ParserElement) -> None:
        if rule_name == rule_name.upper():
            return
        if rule_name in ('mult', 'add', 'compare'):
            pass
            # def bin_op_parse_action(s, loc, tocs):
            #     node = tocs[0]
            #     for i in range(1, len(tocs) - 1, 2):
            #         node = BinOpNode(BinOp(tocs[i]), node, tocs[i + 1])
            #     return node
            #
            # parser.setParseAction(bin_op_parse_action)
        else:
            cls = ''.join(x.capitalize() for x in rule_name.split('_')) + 'Node'
            with suppress(NameError):
                cls = eval(cls)
                if not inspect.isabstract(cls):
                    def parse_action(s, loc, tocs):
                        return cls(*tocs)

                    parser.setParseAction(parse_action)
