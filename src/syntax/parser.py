import inspect
import string
from collections import defaultdict
from contextlib import suppress

import pyparsing as pp
from pyparsing import pyparsing_common as ppc
from varname import nameof

from .ast_tree import *

b = BinOp.ADD


class RussianLanguageCodeSyntaxAnalyser:
    def __init__(self):
        self.rules = defaultdict(list)
        self.start_rule = None
        self._init_rules()
        self._set_parser_action()

    def _register_rule_as(self, name, rule):
        self.rules[name].append(rule)

    def _init_rules(self):
        LPAR, RPAR = pp.Literal('(').suppress(), pp.Literal(')').suppress()
        ASSIGN_OPERATOR = pp.Literal('=')
        SEMI, COMMA = pp.Literal(';').suppress(), pp.Literal(',').suppress()
        LBRACE, RBRACE = pp.Literal("{").suppress(), pp.Literal("}").suppress()
        LBRACK, RBRACK = pp.Literal("[").suppress(), pp.Literal("]").suppress()

        ADD, SUB = pp.Literal('+'), pp.Literal('-')
        MUL, DIV, MOD = pp.Literal('*'), pp.Literal('/'), pp.Literal('%')
        AND = pp.Literal('И')
        OR = pp.Literal('ИЛИ')
        GE, LE, GT, LT = pp.Literal('>='), pp.Literal('<='), pp.Literal('>'), pp.Literal('<')
        NEQUALS, EQUALS = pp.Literal('!='), pp.Literal('==')

        IF, ELSE = pp.Keyword("если"), pp.Keyword("иначе")
        WHILE = pp.Keyword('пока')
        DO = pp.Keyword("делать")
        FOR = pp.Keyword("цикл")
        RETURN = pp.Keyword("вернуть")

        rus_alphas = u'йцукенгшщзхъфывапролджэячсмитьбюёЙЦУКЕНГШЩЗХЪФЫВАПРОЛДЖЭЯЧСМИТЬБЮЁ'
        rus_digits = u'0123456789'

        rus = rus_digits + rus_alphas

        number = ppc.fnumber

        string_ = pp.QuotedString('"', escChar='\\', unquoteResults=False, convertWhitespaceEscapes=False)

        literal = number | string_ | pp.Regex(u'ЛОЖЬ|ИСТИНА')

        self._register_rule_as(nameof(literal), literal)

        rus_identifier = pp.Word(rus + '_').setName("rus_identifier")
        self._register_rule_as(nameof(rus_identifier), rus_identifier)

        type_ = rus_identifier.copy().setName("type")
        self._register_rule_as("type", type_)

        expression = pp.Forward()
        self._register_rule_as(nameof(expression), expression)

        array_identifier = rus_identifier + LBRACK + expression + RBRACK
        self._register_rule_as(nameof(array_identifier), array_identifier)

        identifier = array_identifier | rus_identifier

        expression_list = pp.Optional(expression + pp.ZeroOrMore(COMMA + expression))
        self._register_rule_as(nameof(expression_list), expression_list)

        call = identifier + LPAR + expression_list + RPAR
        self._register_rule_as(nameof(call), call)

        group = (
                literal |
                call |
                identifier |
                LPAR + expression + RPAR
        )

        multiply = pp.Group(group + pp.ZeroOrMore((MUL | DIV | MOD) + group)).setName('binary_operation')
        self._register_rule_as("binary_operation", multiply)

        addition = pp.Group(multiply + pp.ZeroOrMore((ADD | SUB) + multiply)).setName('binary_operation')
        self._register_rule_as("binary_operation", multiply)

        compare_high_priority = pp.Group(addition + pp.Optional((GE | LE | GT | LT) + addition)).setName(
            'binary_operation')
        self._register_rule_as("binary_operation", addition)

        compare_low_priority = pp.Group(
            compare_high_priority + pp.Optional((EQUALS | NEQUALS) + compare_high_priority)).setName('binary_operation')
        self._register_rule_as("binary_operation", compare_low_priority)

        logical_and = pp.Group(compare_low_priority + pp.ZeroOrMore(AND + compare_low_priority)).setName(
            'binary_operation')
        self._register_rule_as("binary_operation", logical_and)

        logical_or = pp.Group(logical_and + pp.ZeroOrMore(OR + logical_and)).setName('binary_operation')
        self._register_rule_as("binary_operation", logical_or)

        expression << logical_or

        statement_list = pp.Forward()

        simple_assign = (identifier + ASSIGN_OPERATOR.suppress() + expression).setName('assign')
        self._register_rule_as("assign", simple_assign)

        var_inner = simple_assign | rus_identifier
        variable_definition = type_ + var_inner + pp.ZeroOrMore(COMMA + var_inner)
        self._register_rule_as(nameof(variable_definition), variable_definition)

        assign = identifier + ASSIGN_OPERATOR.suppress() + expression
        self._register_rule_as(nameof(assign), assign)

        array_ident_allocate = rus_identifier + LBRACK + (literal | pp.Group(pp.empty)) + RBRACK
        self._register_rule_as(nameof(array_ident_allocate), array_ident_allocate)

        array_definition_in_place = type_ + array_ident_allocate + ASSIGN_OPERATOR.suppress() + LBRACE + expression_list + RBRACE
        self._register_rule_as(nameof(array_definition_in_place), array_definition_in_place)

        array_definition = type_ + array_ident_allocate
        self._register_rule_as(nameof(array_definition), array_definition)

        block = LBRACE + statement_list + RBRACE

        statement = pp.Forward()

        if_ = IF.suppress() + LPAR + expression + RPAR + statement + pp.Optional(
            ELSE.suppress() + statement)

        self._register_rule_as("if", if_)

        while_head = WHILE.suppress() + LPAR + expression + RPAR

        while_ = while_head + statement
        self._register_rule_as("while", while_)

        do_while = DO.suppress() + statement + while_head
        self._register_rule_as(nameof(do_while), do_while)

        simple_statement = assign | call

        self._register_rule_as("statement", simple_statement)

        for_vars0 = pp.Optional(simple_statement + pp.ZeroOrMore(COMMA + simple_statement))
        self._register_rule_as("statement_list", for_vars0)

        for_vars = variable_definition | for_vars0
        for_cond = expression | pp.Group(pp.Empty())
        self._register_rule_as("statement", for_cond)

        for_step = for_vars0
        self._register_rule_as("statement_list", for_step)

        for_body = statement | pp.Group(SEMI)
        self._register_rule_as("statement_list", for_body)

        for_ = (FOR.suppress() + LPAR +
                for_vars + SEMI +
                for_cond + SEMI +
                for_step + RPAR +
                for_body)

        self._register_rule_as(nameof(for_), for_)

        param = type_ + rus_identifier
        self._register_rule_as("param", param)

        param_list = pp.Optional(param + pp.ZeroOrMore(COMMA + param))
        self._register_rule_as(nameof(param_list), param_list)

        function_declaration = type_ + rus_identifier + LPAR + param_list + RPAR
        self._register_rule_as(nameof(function_declaration), function_declaration)

        function_definition = type_ + rus_identifier + LPAR + param_list + RPAR + block
        self._register_rule_as(nameof(function_definition), function_definition)

        return_ = RETURN.suppress() + expression
        self._register_rule_as(nameof(return_), return_)

        statement << (
                if_ |
                for_ |
                while_ |
                do_while |
                return_ + SEMI |
                simple_statement + SEMI |
                (array_definition_in_place | array_definition) + SEMI |
                variable_definition + SEMI |
                block |
                function_definition |
                function_declaration + SEMI

        )
        self._register_rule_as(nameof(statement), statement)

        statement_list << pp.ZeroOrMore(statement + pp.ZeroOrMore(SEMI))
        self._register_rule_as(nameof(statement_list), statement_list)

        program = statement_list.ignore(pp.pythonStyleComment).ignore(pp.cStyleComment) + pp.StringEnd()
        start = program
        self.start_rule = start

    def _set_parser_action(self):
        for rule_name, rules in self.rules.items():
            [self.set_parse_action(rule_name, rule) for rule in rules]

    def get_parser(self):
        return self.start_rule

    def parse_string(self, prog) -> StatementListNode:
        locs = []
        row, col = 0, 0
        for ch in prog:
            if ch == '\n':
                row += 1
                col = 0
            elif ch == '\r':
                pass
            else:
                col += 1
            locs.append((row, col))
        old_init_action = AstNode.init_action

        def init_action(node: AstNode) -> None:
            loc = getattr(node, 'loc', None)
            if isinstance(loc, int):
                node.row = locs[loc][0] + 1
                node.col = locs[loc][1] + 1

        AstNode.init_action = init_action
        try:
            prog: StatementListNode = self.get_parser().parseString(str(prog))[0]
            prog.program = True
            return prog
        finally:
            AstNode.init_action = old_init_action

    @staticmethod
    def set_parse_action(rule_name: str, parser: pp.ParserElement) -> None:
        if rule_name == rule_name.upper():
            return
        if rule_name == 'binary_operation':
            def bin_op_parse_action(s, loc, tocs):
                node = tocs[0]
                if not isinstance(node, AstNode):
                    node = bin_op_parse_action(s, loc, node)
                for i in range(1, len(tocs) - 1, 2):
                    second_node = tocs[i + 1]
                    if not isinstance(second_node, AstNode):
                        second_node = bin_op_parse_action(s, loc, second_node)
                    node = BinaryOperationNode(BinOp(tocs[i]), node, second_node)
                return node

            parser.setParseAction(bin_op_parse_action)
        else:
            cls = ''.join(x.capitalize() for x in rule_name.split('_')) + 'Node'
            with suppress(NameError):
                cls = eval(cls)

                if not inspect.isabstract(cls):
                    def parse_action(s, loc, tocs):
                        return cls(*tocs, loc=loc)

                    parser.setParseAction(parse_action)
