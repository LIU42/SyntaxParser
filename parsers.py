from language import GrammarLoader
from language import Token
from language import FormulaElement
from tables import ActionGotoTable

class SyntaxError:

    def __init__(self, token: Token) -> None:
        self.token = token

    def __str__(self) -> str:
        return f"Error at {self.token.line_no}:{self.token.index} \"{self.token.word}\""


class SyntaxParser:

    def __init__(self, grammar_loader: GrammarLoader = GrammarLoader()) -> None:
        self.action_goto_table = ActionGotoTable(grammar_loader.get_formulas())
        self.action_goto_table.load()
        self.symbol_stack = list[FormulaElement]()
        self.status_stack = list[int]()

    def __call__(self, token_list: list[Token]) -> list[SyntaxError]:
        return self.parse(token_list)
    
    def action_error_handler(self, token_list: list[Token], token_index: int, error_list: list[SyntaxError]) -> tuple[bool, int]:
        error_list.append(SyntaxError(token_list[token_index]))
        token_index += 1

        while token_index < len(token_list):
            if self.action_goto_table.get_action(self.status_stack[-1], token_list[token_index]) is not None:
                break
            token_index += 1

        return token_index >= len(token_list), token_index
    
    def goto_error_handler(self, token_list: list[Token], token_index: int, error_list: list[SyntaxError]) -> tuple[bool, int]:
        error_list.append(SyntaxError(token_list[token_index]))
        return True, token_index

    def parse_process(self, token_list: list[Token], token_index: int, error_list: list[SyntaxError]) -> tuple[bool, int]:
        current_status = self.status_stack[-1]
        current_token = token_list[token_index]
        action_option = self.action_goto_table.get_action(current_status, current_token)

        if action_option is None:
            return self.action_error_handler(token_list, token_index, error_list)
        if action_option.is_accept():
            return True, token_index
        
        if action_option.is_shift():
            self.symbol_stack.append(FormulaElement(token = current_token))
            self.status_stack.append(action_option.number)
            token_index += 1

        elif action_option.is_reduce():
            reduce_formula = self.action_goto_table.formula_list[action_option.number]
            reduce_length = len(reduce_formula.right_part)

            self.status_stack = self.status_stack[:-reduce_length]
            self.symbol_stack = self.symbol_stack[:-reduce_length]
            self.symbol_stack.append(reduce_formula.left_part)

            goto_status = self.action_goto_table.get_goto(self.status_stack[-1], reduce_formula.left_part.symbol)
            if goto_status is None:
                return self.goto_error_handler(token_list, token_index, error_list)
            self.status_stack.append(goto_status)
            
        return False, token_index

    def parse(self, token_list: list[Token]) -> list[SyntaxError]:
        self.symbol_stack.clear()
        self.status_stack.clear()
        self.symbol_stack.append(FormulaElement(token = Token()))
        self.status_stack.append(0)

        error_list = list[SyntaxError]()
        token_index = 0
        parse_finished = False
        
        while token_index < len(token_list) and not parse_finished:
            parse_finished, token_index = self.parse_process(token_list, token_index, error_list)
        return error_list
