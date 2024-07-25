from language import TokenBuilder


class Item:

    def __init__(self, formula, forward_index, forward_token):
        self.formula = formula
        self.forward_index = forward_index
        self.forward_token = forward_token

    def __str__(self):
        return f'{self.formula}, {self.forward_index}, {self.forward_token}'

    def __eq__(self, value):
        if not isinstance(value, Item):
            return False
        if self.formula != value.formula:
            return False
        if self.forward_index != value.forward_index:
            return False
        if self.forward_token != value.forward_token:
            return False
        return True
    
    def __hash__(self):
        return hash(self.formula) + hash(self.forward_index) + hash(self.forward_token)

    @property
    def is_search_finished(self):
        return self.forward_index >= len(self.formula.rights)

    @property
    def current_element(self):
        try:
            return self.formula.rights[self.forward_index]
        except IndexError:
            return None

    @property
    def next_element(self):
        try:
            return self.formula.rights[self.forward_index + 1]
        except IndexError:
            return None


class ItemBuilder:

    @staticmethod
    def default(formula, forward_index=0, forward_token=None):
        if forward_token is None:
            return Item(formula, forward_index, TokenBuilder.ends())
        else:
            return Item(formula, forward_index, forward_token)

    @staticmethod
    def next(item):
        return Item(item.formula, item.forward_index + 1, item.forward_token)


class ItemSetUtils:

    @staticmethod
    def subsets(element, formulas, excepts):
        for formula in formulas.search(element.symbol):
            if formula.head.symbol not in excepts:
                yield ItemSetUtils.first_set(formula.head, formulas, excepts)

    @staticmethod
    def first_set(element, formulas, excepts=None):
        if element.is_token:
            return {element.token}

        if excepts is None:
            current_excepts = {element.symbol}
        else:
            current_excepts = excepts.union({element.symbol})

        return {token for subset in ItemSetUtils.subsets(element, formulas, current_excepts) for token in subset}

    @staticmethod
    def generate_forward_item(item, status, formulas):
        for formula in formulas.search(status):
            if next_element := item.next_element:
                forward_set = ItemSetUtils.first_set(next_element, formulas)
            else:
                forward_set = {item.forward_token}

            for forward_token in forward_set:
                yield ItemBuilder.default(formula, forward_token=forward_token)

    @staticmethod
    def forward_items(item, status, formulas):
        return {item for item in ItemSetUtils.generate_forward_item(item, status, formulas)}
    
    @staticmethod
    def closure(items, formulas):
        item_closure = items.copy()
        item_buffer = items.copy()

        while len(item_buffer) > 0:
            search_items = item_buffer.copy()
            item_buffer.clear()

            for item in search_items:
                if item.is_search_finished or item.current_element.is_token:
                    continue
                for forward_item in ItemSetUtils.forward_items(item, item.current_element.symbol, formulas):
                    if forward_item not in item_closure:
                        item_buffer.add(forward_item)

            item_closure = item_closure.union(item_buffer)

        return frozenset(item_closure)
    
    @staticmethod
    def transform_elements(items):
        return {element for item in items if (element := item.current_element)}

    @staticmethod
    def goto(items, element):
        return {ItemBuilder.next(item) for item in items if item.current_element == element}

    @staticmethod
    def next_items(items, element, formulas):
        return ItemSetUtils.closure(ItemSetUtils.goto(items, element), formulas)


class ItemsNumber:

    def __init__(self, init_items):
        self.items_number = {init_items: 0}
        self.items_count = 1

    def __contains__(self, items):
        return items in self.items_number
    
    def __getitem__(self, items):
        return self.items_number[items]

    @property
    def items(self):
        return self.items_number.items()

    def add(self, items):
        self.items_number[items] = self.items_count
        self.items_count += 1

    def clear(self):
        self.items_number.clear()
        self.items_count = 0
