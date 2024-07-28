from language import ElementBuilder
from language import GrammarLoader
from language import TokenBuilder

from tables import ActionGotoTable


class SyntaxError:

    def __init__(self, token, message):
        self.token = token
        self.message = message

    def __str__(self):
        return f'Error at {self.token.line}:{self.token.index} `{self.token.word}`: {self.message}'


class StatusManager:

    def __init__(self, token_list):
        self.status_stack = [0]
        self.symbol_stack = [ElementBuilder.token(TokenBuilder.ends())]

        self.error_list = []
        self.token_list = token_list

        self.token_index = 0
        self.parse_finished = False

    @property
    def reached_end(self):
        return self.token_index >= len(self.token_list)

    @property
    def finished(self):
        return self.reached_end or self.parse_finished

    @property
    def status(self):
        return self.status_stack[-1]

    @property
    def symbol(self):
        return self.symbol_stack[-1]

    @property
    def token(self):
        return self.token_list[self.token_index]

    def push(self, status, symbol):
        self.status_stack.append(status)
        self.symbol_stack.append(symbol)

    def pop(self, count):
        del self.status_stack[-count:]
        del self.symbol_stack[-count:]

    def add_error(self, error):
        self.error_list.append(error)

    def next(self):
        self.token_index += 1


class SyntaxParser:

    def __init__(self):
        self.tables = ActionGotoTable()
        self.tables.load()

        self.formulas = GrammarLoader.formulas()
        self.messages = GrammarLoader.messages()

    def __call__(self, token_list):
        manager = StatusManager(token_list)

        while not manager.finished:
            self.parse_process(manager)

        return manager.error_list

    def error(self, token):
        return SyntaxError(token, self.messages[token])

    def parse_process(self, manager):
        action_option = self.tables.action(manager.status, manager.token)

        if action_option is None:
            manager.add_error(self.error(manager.token))
            manager.next()

            while not manager.reached_end and self.tables.action(manager.status, manager.token) is None:
                manager.next()

        elif action_option.is_accept:
            manager.parse_finished = True

        elif action_option.is_shift:
            manager.push(action_option.number, ElementBuilder.token(manager.token))
            manager.next()

        elif action_option.is_reduce:
            reduce_formula = self.formulas.list[action_option.number]

            manager.pop(reduce_formula.length)
            manager.push(self.tables.goto(manager.status, reduce_formula.lefts.symbol), reduce_formula.lefts)

            if manager.status is None:
                manager.add_error(self.error(manager.token))
                manager.parse_finished = True
