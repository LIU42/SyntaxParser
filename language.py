import json
import re

class Token:

    def __init__(self, line_no: int = 0, index: int = 0, type: str = "ends", word: str = "#") -> None:
        self.line_no = line_no
        self.index = index
        self.type = type
        self.word = word

    def __str__(self) -> str:
        return f"<{self.type},{self.word}>"

    def __eq__(self, token: 'Token') -> bool:
        if self.type != token.type:
            return False
        if self.type == "identifiers" or self.type == "constants":
            return True
        return self.word == token.word
    
    def __hash__(self) -> int:
        if self.type == "identifiers" or self.type == "constants":
            return hash(self.type)
        return hash(self.type) + hash(self.word)
    
    def is_end(self) -> bool:
        return self.type == "ends" and self.word == "#"


class TokenParser:

    @staticmethod
    def parse_full(input: str) -> Token:
        line_no, index, type, word = re.match(r"<(.+?), (.+?), (.+?), (.*)>", input).groups()
        return Token(line_no, index, type, word)
    
    @staticmethod
    def parse_simply(input: str) -> Token:
        type, word = re.match(r"<(.+?),(.*)>", input).groups()
        return Token(type=type, word=word)
    
    @staticmethod
    def parse_lines(token_lines: list[str]) -> list[Token]:
        token_list = list()
        for line in token_lines:
            token_list.append(TokenParser.parse_full(line.strip()))
        token_list.append(Token())
        return token_list


class FormulaElement:

    def __init__(self, token: Token = None, symbol: str = None) -> None:
        self.token = token
        self.symbol = symbol

    def __str__(self) -> str:
        if self.token is not None:
            return str(self.token)
        return self.symbol

    def __eq__(self, value: object) -> bool:
        if isinstance(value, FormulaElement):
            if self.is_token():
                return value.token is not None and self.token == value.token
            if self.is_symbol():
                return value.symbol is not None and self.symbol == value.symbol
            return False
        if isinstance(value, str):
            return self.symbol == value
        if isinstance(value, Token):
            return self.token == value
        return False
    
    def __hash__(self) -> int:
        if self.token is not None:
            return hash(self.token)
        else:
            return hash(self.symbol)
    
    def is_token(self) -> bool:
        return self.token is not None
    
    def is_symbol(self) -> bool:
        return self.symbol is not None
    

class Formula:

    def __init__(self, left_part: FormulaElement, right_part: list[FormulaElement]) -> None:
        self.left_part = left_part
        self.right_part = right_part

    def __str__(self, split_symbol: str = " ") -> str:
        return f"{self.left_part} -> {split_symbol.join(str(item) for item in self.right_part)}"

    def __eq__(self, formula: 'Formula') -> bool:
        return self.left_part == formula.left_part and self.right_part == formula.right_part
    
    def __hash__(self) -> int:
        hash_code = hash(self.left_part) + len(self.right_part)
        for item in self.right_part:
            hash_code += hash(item)
        return hash_code


class FormulaParser:

    @staticmethod
    def parse(input: str) -> Formula:
        left_part_content, right_part_content = input.split(" -> ")
        right_part = list()
        for item in right_part_content.split():
            if item[0] == "<":
                right_part.append(FormulaElement(token=TokenParser.parse_simply(item)))
            else:
                right_part.append(FormulaElement(symbol=item))
        return Formula(FormulaElement(symbol=left_part_content), right_part)
    
    @staticmethod
    def parse_list(formulas: list[str]) -> list[Formula]:
        formula_list = list()
        for formula in formulas:
            formula_list.append(FormulaParser.parse(formula.strip()))
        return formula_list


class FormulaUtils:

    @staticmethod
    def get_index_dict(formula_list: list[Formula]) -> dict[Formula, int]:
        index_dict = dict()
        for index, formula in enumerate(formula_list, start=0):
            index_dict[formula] = index
        return index_dict
    
    @staticmethod
    def get_search_dict(formula_list: list[Formula]) -> dict[str, set[Formula]]:
        search_dict = dict()
        for formula in formula_list:
            search_dict.setdefault(formula.left_part.symbol, set()).add(formula)
        return search_dict
    

class GrammarLoader:

    def __init__(self, grammar_path: str = "./grammars/grammar.json", message_path: str = "./grammars/message.json") -> None:
        with open(grammar_path, mode="r", encoding="utf-8") as grammar_file:
            self.grammar_dict = json.load(grammar_file)
        with open(message_path, mode="r", encoding="utf-8") as message_file:
            self.message_dict = json.load(message_file)
        
    def get_formulas(self) -> list[Formula]:
        return FormulaParser.parse_list(self.grammar_dict["formulas"])
    
    def get_message_rules(self) -> dict[Token, str]:
        message_rules = dict()
        for rules in self.message_dict["messages"]:
            message_rules.setdefault(TokenParser.parse_simply(rules["token"]), rules["message"])
        return message_rules
    
    def get_default_message(self) -> str:
        return self.message_dict["default"]
       