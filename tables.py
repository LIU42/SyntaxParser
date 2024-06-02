from items import Item
from items import ItemsNumberDict
from items import ItemSetUtils

from language import Formula
from language import FormulaElement
from language import FormulaUtils
from language import GrammarLoader
from language import Token
from language import TokenParser

from recorders import BuildRecorder

class AbstractTable:

    def __init__(self, name: str, recorder: BuildRecorder = None) -> None:
        self.items = dict()
        self.name = name
        self.recorder = recorder

    def add_item(self, row_index: object, col_index: object, value: object) -> None:
        if col_index not in self.items.setdefault(row_index, dict()):
            self.items[row_index][col_index] = value
        elif self.recorder is not None:
            self.recorder.write_conflict(self.name, row_index, col_index, self.items[row_index][col_index], value)

    def get_item(self, row_index: object, col_index: object) -> object:
        return self.items[row_index][col_index]
    
    def to_sparse_list(self) -> list[tuple[object, object, object]]:
        sparse_list = list()
        for row_index, col_value_dict in self.items.items():
            for col_index, value in col_value_dict.items():
                sparse_list.append((row_index, col_index, value))
        return sparse_list

    @staticmethod
    def to_sparse_line(row_index: object, col_index: object, value: object) -> str:
        return f"{str(row_index)} {str(col_index)} {str(value)}\n"
    
    @staticmethod
    def get_sparse_items(line: str) -> list[str]:
        return line.strip().split()


class StatusTransforms(AbstractTable):

    def __init__(self, name: str = "transforms", recorder: BuildRecorder = None) -> None:
        super().__init__(name, recorder)
    
    def add_transform(self, last_status: int, element: FormulaElement, next_status: int) -> None:
        self.add_item(last_status, element, next_status)


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


class ActionTable(AbstractTable):

    def __init__(self, name: str = "actions", recorder: BuildRecorder = None) -> None:
        super().__init__(name, recorder)

    def __getitem__(self, action_index: tuple[int, Token]) -> ActionOption:
        return self.get_item(*action_index)
    
    def add_action_item(self, last_status: int, token: Token, option: ActionOption) -> None:
        return self.add_item(last_status, token, option)

    def save(self, save_path: str) -> None:
        with open(save_path, mode="w", encoding="utf-8") as save_file:
            for last_status, token, option in self.to_sparse_list():
                save_file.write(AbstractTable.to_sparse_line(last_status, token, option))

    def load(self, load_path: str) -> None:
        with open(load_path, mode="r", encoding="utf-8") as load_file:
            for line in load_file.readlines():
                last_status, token, option = AbstractTable.get_sparse_items(line)
                self.add_action_item(int(last_status), TokenParser.parse_simply(token), ActionOption.parse(option))


class GotoTable(AbstractTable):

    def __init__(self, name: str = "gotos", recorder: BuildRecorder = None) -> None:
        super().__init__(name, recorder)

    def __getitem__(self, goto_index: tuple[int, str]) -> int:
        return self.get_item(*goto_index)

    def add_goto_item(self, last_status: int, symbol: str, next_status: int) -> None:
        return self.add_item(last_status, symbol, next_status)

    def save(self, save_path: str) -> None:
        with open(save_path, mode="w", encoding="utf-8") as save_file:
            for last_status, symbol, next_status in self.to_sparse_list():
                save_file.write(AbstractTable.to_sparse_line(last_status, symbol, next_status))

    def load(self, load_path: str) -> None:
        with open(load_path, mode="r", encoding="utf-8") as load_file:
            for line in load_file.readlines():
                last_status, symbol, next_status = AbstractTable.get_sparse_items(line)
                self.add_goto_item(int(last_status), symbol, int(next_status))


class ActionGotoTable:

    def __init__(self, formula_list: list[Formula], recorder: BuildRecorder = None) -> None:
        self.formula_list = formula_list
        self.recorder = recorder
        self.action_table = ActionTable(recorder=recorder)
        self.goto_table = GotoTable(recorder=recorder)

    def create_item_sets(self) -> tuple[ItemsNumberDict, StatusTransforms]:
        transforms = StatusTransforms(recorder=self.recorder)
        search_dict = FormulaUtils.get_search_dict(self.formula_list)

        init_items = ItemSetUtils.get_closure(ItemSetUtils.create_by_items(Item(self.formula_list[0])), search_dict)
        items_dict = ItemsNumberDict()
        items_dict.try_add(init_items)

        items_buffer = set()
        items_buffer.add(init_items)

        while len(items_buffer) > 0:
            current_item_sets = items_buffer.copy()
            items_buffer.clear()

            for items in current_item_sets:
                for element in ItemSetUtils.get_transform_elements(items):
                    next_items = ItemSetUtils.get_next_items(items, element, search_dict)

                    if items_dict.try_add(next_items):
                        self.recorder.write_items(items_dict[next_items], next_items)
                        items_buffer.add(next_items)
                    transforms.add_transform(items_dict[items], element, items_dict[next_items])

        return items_dict, transforms
    
    def setup_action_goto_table(self, items_dict: ItemsNumberDict, transforms: StatusTransforms) -> None:
        for last_status, element, next_status in transforms.to_sparse_list():
            if element.is_token():
                self.action_table.add_action_item(last_status, element.token, ActionOption(option="S", number=next_status))
            elif element.is_symbol():
                self.goto_table.add_goto_item(last_status, element.symbol, next_status)

        index_dict = FormulaUtils.get_index_dict(self.formula_list)

        for item_set, number in items_dict.items_number_dict.items():
            for item in item_set:
                if not item.is_search_finished():
                    continue
                if item.formula == self.formula_list[0] and item.forward_token.is_end():
                    option = ActionOption(accept=True)
                else:
                    option = ActionOption(option="R", number=index_dict[item.formula])

                self.action_table.add_action_item(number, item.forward_token, option)

    def build(self) -> None:
        self.setup_action_goto_table(*self.create_item_sets())

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
