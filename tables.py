import json

from language import Token
from language import TokenParser
from language import FormulaElement
from language import FormulaParser
from language import FormulaUtils

from items import Item
from items import ItemSet
from items import ItemSetUtils
from items import ItemSetMap
from recorders import BuildRecorder

RECORDER = BuildRecorder()

class Table:

    def __init__(self, name: str) -> None:
        self.items = dict[object, dict[object, object]]()
        self.name = name

    def add_item(self, row: object, col: object, value: object) -> None:
        if self.items.get(row) is None:
            self.items[row] = dict[object, object]()
        if self.items[row].get(col) is None:
            self.items[row][col] = value
            return
        RECORDER.write_conflict(self.name, row, col, self.items[row][col], value)

    def get_item(self, item_index: tuple[object, object]) -> object:
        row, col = item_index
        return self.items[row][col]

class TableUtils:

    @staticmethod
    def static_add(name: str, content: dict[object, dict[object, object]], row: object, col: object, value: object) -> None:
        if content.get(row) is None:
            content[row] = dict[object, object]()
        if content[row].get(col) is None:
            content[row][col] = value
            return
        RECORDER.write_conflict(name, row, col, content[row].get(col), value)

    @staticmethod
    def static_get_item(content: dict[object, dict[object, object]], unit_index: tuple[object, object]) -> object:
        row, col = unit_index
        return content[row][col]
    
class StatusTransforms:

    def __init__(self) -> None:
        self.content = dict[int, dict[FormulaElement, int]]()

    def __getitem__(self, unit_index: tuple[int, FormulaElement]) -> int:
        return TableUtils.static_get_item(self.content, unit_index)
    
    def add_transform(self, status_from: int, element: FormulaElement, status_to: int) -> None:
        TableUtils.static_add("transforms", self.content, status_from, element, status_to)

class ActionOption:

    def __init__(self, option: str = None, number: int = None, accept: bool = False) -> None:
        self.option = option
        self.number = number
        self.accept = accept
    
    def __str__(self) -> str:
        if self.accept:
            return "accept"
        return f"{self.option}{self.number}"
    
    @staticmethod
    def parse(input: str) -> 'ActionOption':
        if input == "accept":
            return ActionOption(accept = True)
        return ActionOption(option = input[0], number = int(input[1:]))
    
    def is_shift(self) -> bool:
        return self.option == "S"
    
    def is_reduce(self) -> bool:
        return self.option == "R"
    
    def is_accept(self) -> bool:
        return self.accept

class ActionTable:

    def __init__(self) -> None:
        self.content = dict[int, dict[Token, ActionOption]]()

    def __gititem__(self, unit_index: tuple[int, Token]) -> ActionOption:
        return TableUtils.static_get_item(self.content, unit_index)

    def add_item(self, status_from: int, token: Token, option: ActionOption) -> None:
        TableUtils.static_add("action", self.content, status_from, token, option)

class GotoTable:

    def __init__(self) -> None:
        self.content = dict[int, dict[str, int]]()

    def __gititem__(self, unit_index: tuple[int, str]) -> int:
        return TableUtils.static_get_item(self.content, unit_index)

    def add_item(self, status_from: int, symbol: str, status_to: int) -> None:
        TableUtils.static_add("goto", self.content, status_from, symbol, status_to)

class ActionGotoTable:

    def __init__(self, formulas: list[str]) -> None:
        self.action_table = ActionTable()
        self.goto_table = GotoTable()
        self.formula_list = FormulaParser.parse_list(formulas)

    def create_item_sets(self) -> tuple[ItemSetMap, StatusTransforms]:
        left_part_map = FormulaUtils.get_left_part_map(self.formula_list)
        transforms = StatusTransforms()
        items_map = ItemSetMap()
        items_buffer = set[ItemSet]()

        init_items = ItemSetUtils.get_closure(ItemSetUtils.create_by_items(Item(self.formula_list[0])), left_part_map)
        items_map.if_add(init_items)
        items_buffer.add(init_items)

        while len(items_buffer) > 0:
            current_item_sets = items_buffer.copy()
            items_buffer.clear()
            for items in current_item_sets:
                for element in ItemSetUtils.get_next_elements(items):
                    next_items = ItemSetUtils.get_next_items(items, element, left_part_map)
                    if items_map.if_add(next_items):
                        RECORDER.write_items(items_map.get_number(next_items), next_items.content)
                        items_buffer.add(next_items)
                    transforms.add_transform(items_map.get_number(items), element, items_map.get_number(next_items))
        return items_map, transforms
    
    def setup_action_goto_table(self, item_sets_params: tuple[ItemSetMap, StatusTransforms], accept_token: Token = Token()) -> None:
        items_map, transforms = item_sets_params
        for status_from, element_status_map in transforms.content.items():
            for element, status_to in element_status_map.items():
                if element.is_token():
                    self.action_table.add_item(status_from, element.token, ActionOption(option = "S", number = status_to))
                elif element.is_symbol():
                    self.goto_table.add_item(status_from, element.symbol, status_to)

        index_map = FormulaUtils.get_index_map(self.formula_list)
        for number, items in items_map.number_items_map.items():
            for item in items.content:
                if not item.is_search_finished():
                    continue
                if item.formula == self.formula_list[0] and item.forward_token == accept_token:
                    option = ActionOption(accept = True)
                else:
                    option = ActionOption(option = "R", number = index_map[item.formula])
                self.action_table.add_item(number, item.forward_token, option)

    def build(self) -> None:
        self.setup_action_goto_table(self.create_item_sets())

    def save(self, action_path: str = "./tables/action.txt", goto_path: str = "./tables/goto.txt") -> None:
        with open(action_path, "w+", encoding = "utf-8") as action_file:
            for status_from, token_option_map in self.action_table.content.items():
                for token, option in token_option_map.items():
                    action_file.write(f"{status_from} {token} {option}\n")

        with open(goto_path, "w+", encoding = "utf-8") as goto_file:
            for status_from, symbol_status_map in self.goto_table.content.items():
                for symbol, status_to in symbol_status_map.items():
                    goto_file.write(f"{status_from} {symbol} {status_to}\n")

    def load(self, action_path: str = "./tables/action.txt", goto_path: str = "./tables/goto.txt") -> None:
        with open(action_path, "r", encoding = "utf-8") as action_file:
            for line in action_file.readlines():
                status_from, token, option = line.strip().split()
                self.action_table.add_item(int(status_from), TokenParser.parse_simply(token), ActionOption.parse(option))

        with open(goto_path, "r", encoding = "utf-8") as goto_file:
            for line in goto_file.readlines():
                status_from, symbol, status_to = line.strip().split()
                self.goto_table.add_item(int(status_from), symbol, int(status_to))

    def get_action(self, status_from: int, token: Token) -> ActionOption:
        try:
            return self.action_table[status_from, token]
        except:
            return None
    
    def get_goto(self, status_from: int, symbol: str) -> int:
        try:
            return self.goto_table[status_from, symbol]
        except:
            return None

if __name__ == "__main__":
    RECORDER.open_files()
    with open("./grammars/grammar.json", "r", encoding = "utf-8") as grammar_file:
        grammar_dict = json.load(grammar_file)
    action_goto_table = ActionGotoTable(grammar_dict["formulas"])
    action_goto_table.build()
    action_goto_table.save()
