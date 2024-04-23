from language import Token
from language import Formula
from language import FormulaElement

class Item:

    def __init__(self, formula: Formula, forward_index: int = 0, forward_token: Token = Token()) -> None:
        self.formula = formula
        self.forward_index = forward_index
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
    
class ItemSet:

    def __init__(self, items: set[Item] = set[Item]()) -> None:
        self.content = frozenset[Item](items)

    def __eq__(self, item_set: 'ItemSet') -> bool:
        return self.content == item_set.content
    
    def __hash__(self) -> int:
        return hash(self.content)
    
    def copy_editable(self) -> set[Item]:
        return set[Item](self.content)
    
class ItemSetUtils:

    @staticmethod
    def create_by_items(*items: Item) -> ItemSet:
        return ItemSet(items)

    @staticmethod
    def get_first_set(element: FormulaElement, left_part_map: dict[str, set[Formula]], except_set: set[str] = set[str]()) -> set[Token]:
        first_set = set[Token]()
        if element.is_token():
            first_set.add(element.token)
            return first_set
        new_except_set = except_set.copy()
        new_except_set.add(element.symbol)
        for formula in left_part_map[element.symbol]:
            if formula.right_part[0].symbol not in new_except_set:
                first_set = first_set.union(ItemSetUtils.get_first_set(formula.right_part[0], left_part_map, new_except_set))
        return first_set
    
    @staticmethod
    def get_new_item(item: Item, status: str, left_part_map: dict[str, set[Formula]]) -> set[Item]:
        new_item_set = set[Item]()
        for formula in left_part_map[status]:
            if next_element := item.get_next_element():
                forward_set = ItemSetUtils.get_first_set(next_element, left_part_map)
            else:
                forward_set = { item.forward_token }
            for forward_token in forward_set:
                new_item_set.add(Item(formula, 0, forward_token))
        return new_item_set
    
    @staticmethod
    def get_closure(item_set: ItemSet, left_part_map: dict[str, set[Formula]]) -> ItemSet:
        closure_item_set = item_set.copy_editable()
        item_buffer = item_set.copy_editable()
        while True:
            search_items = item_buffer.copy()
            item_buffer.clear()
            for item in search_items:
                if item.is_search_finished() or item.get_current_element().is_token():
                    continue
                for new_item in ItemSetUtils.get_new_item(item, item.get_current_element().symbol, left_part_map):
                    if new_item not in closure_item_set:
                        item_buffer.add(new_item)
            if len(item_buffer) == 0:
                break
            closure_item_set = closure_item_set.union(item_buffer)
        return ItemSet(closure_item_set)
    
    @staticmethod
    def get_next_elements(item_set: ItemSet) -> set[FormulaElement]:
        element_set = set[FormulaElement]()
        for item in item_set.content:
            if element := item.get_current_element():
                element_set.add(element)
        return element_set
    
    @staticmethod
    def goto(item_set: ItemSet, element: FormulaElement) -> ItemSet:
        goto_item_set = set[Item]()
        for item in item_set.content:
            if current_element := item.get_current_element():
                if current_element != element:
                    continue
                goto_item_set.add(Item(item.formula, item.forward_index + 1, item.forward_token))
        return ItemSet(goto_item_set)
    
    @staticmethod
    def get_next_items(item_set: ItemSet, element: FormulaElement, left_part_map: dict[str, set[Formula]]) -> ItemSet:
        return ItemSetUtils.get_closure(ItemSetUtils.goto(item_set, element), left_part_map)
    
class ItemSetMap:

    def __init__(self) -> None:
        self.items_number_map = dict[ItemSet, int]()
        self.number_items_map = dict[int, ItemSet]()
        self.element_count = 0

    def __contains__(self, key: object) -> bool:
        if isinstance(key, ItemSet):
            return key in self.items_number_map
        if isinstance(key, int):
            return key in self.number_items_map
        return False
    
    def if_add(self, item_set: ItemSet) -> bool:
        if item_set in self.items_number_map:
            return False
        self.items_number_map[item_set] = self.element_count
        self.number_items_map[self.element_count] = item_set
        self.element_count += 1
        return True
    
    def get_number(self, item_set: ItemSet) -> int:
        return self.items_number_map.get(item_set)
    
    def get_items(self, number: int) -> ItemSet:
        return self.number_items_map.get(number)
    
    def clear(self) -> None:
        self.items_number_map.clear()
        self.number_items_map.clear()
        self.element_count = 0
