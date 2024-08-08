import json
import re

from collections import defaultdict


class Token:

    def __init__(self, line, index, type, word):
        self.line = line
        self.index = index
        self.type = type
        self.word = word

    def __str__(self):
        return f'<{self.type},{self.word}>'

    def __eq__(self, token):
        if isinstance(token, Token):
            if self.type == 'identifiers' or self.type == 'constants':
                return self.type == token.type
            else:
                return self.type == token.type and self.word == token.word
        return False
    
    def __hash__(self):
        if self.type == 'identifiers' or self.type == 'constants':
            return hash(self.type)
        else:
            return hash(self.type) + hash(self.word)

    @property
    def is_end(self):
        return self.type == 'ends' and self.word == '#'


class TokenBuilder:

    @staticmethod
    def ends():
        return Token(0, 0, 'ends', '#')

    @staticmethod
    def full(line, index, type, word):
        return Token(line, index, type, word)

    @staticmethod
    def simply(type, word):
        return Token(0, 0, type, word)


class TokenParser:

    @staticmethod
    def full(input):
        match = re.match(r'<(.+?), (.+?), (.+?), (.*)>', input)

        line = match.group(1)
        index = match.group(2)
        type = match.group(3)
        word = match.group(4)

        return TokenBuilder.full(line, index, type, word)
    
    @staticmethod
    def simply(input):
        match = re.match(r'<(.+?),(.*)>', input)

        type = match.group(1)
        word = match.group(2)

        return TokenBuilder.simply(type, word)
    
    @staticmethod
    def list(token_list):
        return [TokenParser.full(token) for token in token_list] + [TokenBuilder.ends()]


class FormulaElement:

    def __init__(self, token, symbol):
        self.token = token
        self.symbol = symbol

    def __str__(self):
        if self.is_token:
            return str(self.token)
        else:
            return str(self.symbol)

    def __eq__(self, element):
        if isinstance(element, FormulaElement):
            if self.is_token:
                return element.is_token and self.token == element.token
            if self.is_symbol:
                return element.is_symbol and self.symbol == element.symbol
        return False
    
    def __hash__(self):
        if self.is_token:
            return hash(self.token)
        else:
            return hash(self.symbol)

    @property
    def is_token(self):
        return self.token is not None

    @property
    def is_symbol(self):
        return self.symbol is not None


class ElementBuilder:

    @staticmethod
    def token(token):
        return FormulaElement(token, None)

    @staticmethod
    def symbol(symbol):
        return FormulaElement(None, symbol)


class ElementUtils:

    @staticmethod
    def stringify(element_list):
        return ' '.join(map(str, element_list))


class Formula:

    def __init__(self, l_part, r_part):
        self.l_part = l_part
        self.r_part = r_part

    def __str__(self):
        return f'{self.l_part} -> {ElementUtils.stringify(self.r_part)}'

    def __eq__(self, formula):
        if not isinstance(formula, Formula):
            return False
        if self.l_part != formula.l_part:
            return False
        if self.r_part != formula.r_part:
            return False
        return True

    def __hash__(self):
        return hash(self.l_part) + sum(hash(item) for item in self.r_part)

    @property
    def head(self):
        return self.r_part[0]

    @property
    def length(self):
        return len(self.r_part)


class FormulasWrapper:

    def __init__(self, formulas):
        self.formulas = formulas
        self.number_dict = defaultdict(int)
        self.symbol_dict = defaultdict(set)
        self.setup_dicts()

    @property
    def list(self):
        return self.formulas

    @property
    def init(self):
        return self.formulas[0]

    def setup_dicts(self):
        for number, formula in enumerate(self.formulas):
            self.number_dict[formula] = number
            self.symbol_dict[formula.l_part.symbol].add(formula)

    def number(self, formula):
        return self.number_dict[formula]

    def search(self, symbol):
        return self.symbol_dict[symbol]


class FormulaParser:

    @staticmethod
    def item(item):
        if item[0] == '<':
            return ElementBuilder.token(TokenParser.simply(item))
        else:
            return ElementBuilder.symbol(item)

    @staticmethod
    def formula(input):
        left_content, right_content = input.split(' -> ')

        return Formula(ElementBuilder.symbol(left_content), [
            FormulaParser.item(item) for item in right_content.split()
        ])

    @staticmethod
    def list(formulas):
        return [FormulaParser.formula(formula.strip()) for formula in formulas]


class GrammarLoader:

    @staticmethod
    def formulas():
        with open('grammars/grammar.json', 'r') as grammar_json:
            grammar_config = json.load(grammar_json)
            formulas = grammar_config['formulas']

        return FormulasWrapper(FormulaParser.list(formulas))

    @staticmethod
    def messages():
        with open('grammars/message.json', 'r') as message_json:
            message_config = json.load(message_json)
            messages = message_config['messages']
            defaults = message_config['defaults']

        message_rules = defaultdict(lambda: defaults)

        for message in messages:
            message_rules[TokenParser.simply(message['token'])] = message['message']

        return message_rules
