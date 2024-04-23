from language import GrammarLoader
from language import Token
from language import TokenParser
from language import Formula
from language import FormulaElement
from language import FormulaUtils

from items import Item
from items import ItemsNumberDict
from items import ItemSetUtils
from recorders import BuildRecorder

class StatusTransforms:

    def __init__(self, recorder: BuildRecorder) -> None:
        self.recorder = recorder
        self.transforms = dict[int, dict[FormulaElement, int]]()

    def create_elements_dict(self, *elements: tuple[FormulaElement, int]) -> dict[FormulaElement, int]:
        return dict[FormulaElement, int](elements)

    def add_transform(self, status_from: int, element: FormulaElement, status_to: int) -> None:
        if self.transforms.setdefault(status_from, self.create_elements_dict()).get(element) is None:
            self.transforms[status_from][element] = status_to
        else:
            self.recorder.write_conflict("transforms", status_from, element, self.transforms[status_from][element], status_to)


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

    def __init__(self, recorder: BuildRecorder = None) -> None:
        self.recorder = recorder
        self.actions = dict[int, dict[Token, ActionOption]]()

    def __getitem__(self, action_index: tuple[int, Token]) -> ActionOption:
        return self.get_action(*action_index)
    
    def create_tokens_dict(self, *tokens: tuple[Token, ActionOption]) -> dict[Token, ActionOption]:
        return dict[Token, ActionOption](tokens)
    
    def add_action(self, status_from: int, token: Token, option: ActionOption) -> None:
        if self.actions.setdefault(status_from, self.create_tokens_dict()).get(token) is None:
            self.actions[status_from][token] = option
        elif self.recorder is not None:
            self.recorder.write_conflict("actions", status_from, token, self.actions[status_from][token], option)

    def get_action(self, status_from: int, token: Token) -> ActionOption:
        return self.actions[status_from][token]

    def save(self, save_path: str) -> None:
        with open(save_path, "w+", encoding = "utf-8") as save_file:
            for status_from, tokens_dict in self.actions.items():
                for token, option in tokens_dict.items():
                    save_file.write(f"{status_from} {token} {option}\n")

    def load(self, load_path: str) -> None:
        with open(load_path, "r", encoding = "utf-8") as load_file:
            for line in load_file.readlines():
                status_from, token, option = line.strip().split()
                self.add_action(int(status_from), TokenParser.parse_simply(token), ActionOption.parse(option))


class GotoTable:

    def __init__(self, recorder: BuildRecorder = None) -> None:
        self.recorder = recorder
        self.gotos = dict[int, dict[str, int]]()

    def __getitem__(self, goto_index: tuple[int, str]) -> int:
        return self.get_goto(*goto_index)
    
    def create_symbols_dict(self, *symbols: tuple[str, int]) -> dict[str, int]:
        return dict[str, int](symbols)

    def add_goto(self, status_from: int, symbol: str, status_to: int) -> None:
        if self.gotos.setdefault(status_from, self.create_symbols_dict()).get(symbol) is None:
            self.gotos[status_from][symbol] = status_to
        elif self.recorder is not None:
            self.recorder.write_conflict("gotos", status_from, symbol, self.gotos[status_from][symbol], status_to)

    def get_goto(self, status_from: int, symbol: str) -> int:
        return self.gotos[status_from][symbol]

    def save(self, save_path: str) -> None:
        with open(save_path, "w+", encoding = "utf-8") as save_file:
            for status_from, symbols_dict in self.gotos.items():
                for symbol, status_to, in symbols_dict.items():
                    save_file.write(f"{status_from} {symbol} {status_to}\n")

    def load(self, load_path: str) -> None:
        with open(load_path, "r", encoding = "utf-8") as load_file:
            for line in load_file.readlines():
                status_from, symbol, status_to = line.strip().split()
                self.add_goto(int(status_from), symbol, int(status_to))


class ActionGotoTable:

    def __init__(self, formula_list: list[Formula], recorder: BuildRecorder = None) -> None:
        self.formula_list = formula_list
        self.recorder = recorder
        self.action_table = ActionTable(recorder)
        self.goto_table = GotoTable(recorder)

    def create_item_sets(self) -> tuple[ItemsNumberDict, StatusTransforms]:
        search_dict = FormulaUtils.get_search_dict(self.formula_list)
        transforms = StatusTransforms(self.recorder)
        items_dict = ItemsNumberDict()
        items_buffer = set[frozenset[Item]]()

        init_items = ItemSetUtils.get_closure(ItemSetUtils.create_by_items(Item(self.formula_list[0])), search_dict)
        items_dict.try_add(init_items)
        items_buffer.add(init_items)

        while len(items_buffer) > 0:
            current_item_sets = items_buffer.copy()
            items_buffer.clear()

            for items in current_item_sets:
                for element in ItemSetUtils.get_next_elements(items):
                    next_items = ItemSetUtils.get_next_items(items, element, search_dict)

                    if items_dict.try_add(next_items):
                        self.recorder.write_items(items_dict.get_number(next_items), next_items)
                        items_buffer.add(next_items)
                    transforms.add_transform(items_dict[items], element, items_dict[next_items])

        return items_dict, transforms
    
    def setup_action_goto_table(self, item_sets_params: tuple[ItemsNumberDict, StatusTransforms], accept_token: Token = Token()) -> None:
        items_dict, transforms = item_sets_params
        index_dict = FormulaUtils.get_index_dict(self.formula_list)

        for status_from, elements_dict in transforms.transforms.items():
            for element, status_to in elements_dict.items():
                if element.is_token():
                    self.action_table.add_action(status_from, element.token, ActionOption(option = "S", number = status_to))
                elif element.is_symbol():
                    self.goto_table.add_goto(status_from, element.symbol, status_to)

        for item_set, number in items_dict.items_number_dict.items():
            for item in item_set:
                if not item.is_search_finished():
                    continue
                if item.formula == self.formula_list[0] and item.forward_token == accept_token:
                    option = ActionOption(accept = True)
                else:
                    option = ActionOption(option = "R", number = index_dict[item.formula])

                self.action_table.add_action(number, item.forward_token, option)     

    def build(self) -> None:
        self.setup_action_goto_table(self.create_item_sets())

    def save(self, action_path: str = "./tables/action.txt", goto_path: str = "./tables/goto.txt") -> None:
        self.action_table.save(action_path)
        self.goto_table.save(goto_path)

    def load(self, action_path: str = "./tables/action.txt", goto_path: str = "./tables/goto.txt") -> None:
        self.action_table.load(action_path)
        self.goto_table.load(goto_path)

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
    action_goto_table = ActionGotoTable(GrammarLoader().get_formulas(), BuildRecorder())
    action_goto_table.build()
    action_goto_table.save()
