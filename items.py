from language import Formula
from language import FormulaElement
from language import Token

class Item:

    def __init__(self, formula: Formula, forward_index: int = 0, forward_token: Token = None) -> None:
        self.formula = formula
        self.forward_index = forward_index
        if forward_token is None:
            self.forward_token = Token()
        else:
            self.forward_token = forward_token

    def __str__(self) -> str:
        return f"{self.formula}, {self.forward_index}, {self.forward_token}"

    def __eq__(self, item: 'Item') -> bool:
        if self.formula != item.formula:
            return False
        if self.forward_index != item.forward_index:
            return False
        if self.forward_token != item.forward_token:
            return False
        return True
    
    def __hash__(self) -> int:
        return hash(self.formula) + hash(self.forward_index) + hash(self.forward_token)
    
    def is_search_finished(self) -> bool:
        return self.forward_index >= len(self.formula.right_part)
    
    def get_current_element(self) -> FormulaElement:
        if self.forward_index >= len(self.formula.right_part):
            return None
        return self.formula.right_part[self.forward_index]
    
    def get_next_element(self) -> FormulaElement:
        if self.forward_index + 1 >= len(self.formula.right_part):
            return None
        return self.formula.right_part[self.forward_index + 1]


class ItemSetUtils:

    @staticmethod
    def create_by_items(*items: Item) -> frozenset[Item]:
        return frozenset(items)
    
    @staticmethod
    def create_token_set(*tokens: Token) -> set[Token]:
        return set(tokens)

    @staticmethod
    def get_first_set(element: FormulaElement, search_dict: dict[str, set[Formula]], except_set: set[str] = None) -> set[Token]:
        first_set = set()
        if element.is_token():
            first_set.add(element.token)
            return first_set
        
        if except_set is None:
            new_except_set = set()
        else:
            new_except_set = except_set.copy()
        new_except_set.add(element.symbol)

        for formula in search_dict[element.symbol]:
            if formula.right_part[0].symbol not in new_except_set:
                first_set = first_set.union(ItemSetUtils.get_first_set(formula.right_part[0], search_dict, new_except_set))

        return first_set
    
    @staticmethod
    def get_new_items(item: Item, status: str, search_dict: dict[str, set[Formula]]) -> frozenset[Item]:
        new_item_set = set()
        for formula in search_dict[status]:
            if next_element := item.get_next_element():
                forward_set = ItemSetUtils.get_first_set(next_element, search_dict)
            else:
                forward_set = ItemSetUtils.create_token_set(item.forward_token)

            for forward_token in forward_set:
                new_item_set.add(Item(formula, 0, forward_token))

        return frozenset(new_item_set)
    
    @staticmethod
    def get_closure(item_set: frozenset[Item], search_dict: dict[str, set[Formula]]) -> frozenset[Item]:
        closure_item_set = set(item_set)
        item_buffer = set(item_set)

        while True:
            search_items = item_buffer.copy()
            item_buffer.clear()

            for item in search_items:
                if item.is_search_finished() or item.get_current_element().is_token():
                    continue
                for new_item in ItemSetUtils.get_new_items(item, item.get_current_element().symbol, search_dict):
                    if new_item not in closure_item_set:
                        item_buffer.add(new_item)

            if len(item_buffer) == 0:
                break
            closure_item_set = closure_item_set.union(item_buffer)

        return frozenset(closure_item_set)
    
    @staticmethod
    def get_transform_elements(item_set: frozenset[Item]) -> set[FormulaElement]:
        element_set = set()
        for item in item_set:
            if element := item.get_current_element():
                element_set.add(element)
        return element_set
    
    @staticmethod
    def goto(item_set: frozenset[Item], element: FormulaElement) -> frozenset[Item]:
        goto_item_set = set()
        for item in item_set:
            if current_element := item.get_current_element():
                if current_element != element:
                    continue
                goto_item_set.add(Item(item.formula, item.forward_index + 1, item.forward_token))
        return frozenset(goto_item_set)
    
    @staticmethod
    def get_next_items(item_set: frozenset[Item], element: FormulaElement, search_dict: dict[str, set[Formula]]) -> frozenset[Item]:
        return ItemSetUtils.get_closure(ItemSetUtils.goto(item_set, element), search_dict)


class ItemsNumberDict:

    def __init__(self) -> None:
        self.items_number_dict = dict()
        self.items_count = 0

    def __contains__(self, key: frozenset[Item]) -> bool:
        return key in self.items_number_dict
    
    def __getitem__(self, item_set: frozenset[Item]) -> int:
        return self.get_number(item_set)
    
    def try_add(self, item_set: frozenset[Item]) -> bool:
        if item_set in self.items_number_dict:
            return False
        else:
            self.items_number_dict[item_set] = self.items_count
            self.items_count += 1
            return True
    
    def get_number(self, item_set: frozenset[Item]) -> int:
        try:
            return self.items_number_dict[item_set]
        except KeyError:
            return None
    
    def clear(self) -> None:
        self.items_number_dict.clear()
        self.items_count = 0
