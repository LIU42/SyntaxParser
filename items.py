from language import TokenBuilder


class Item:

    def __init__(self, formula, forward_index, forward_token):
        self.formula = formula
        self.forward_index = forward_index
        self.forward_token = forward_token

    def __str__(self):
        return f'{self.formula}, {self.forward_index}, {self.forward_token}'

    def __eq__(self, item):
        if not isinstance(item, Item):
            return False
        if self.formula != item.formula:
            return False
        if self.forward_index != item.forward_index:
            return False
        if self.forward_token != item.forward_token:
            return False
        return True
    
    def __hash__(self):
        return hash(self.formula) + hash(self.forward_index) + hash(self.forward_token)

    @property
    def search_finished(self):
        return self.forward_index >= self.formula.length

    @property
    def current_element(self):
        try:
            return self.formula.r_part[self.forward_index]
        except IndexError:
            return None

    @property
    def next_element(self):
        try:
            return self.formula.r_part[self.forward_index + 1]
        except IndexError:
            return None

    @property
    def closure_enable(self):
        return not self.search_finished and self.current_element.is_symbol


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
        for formula in filter(lambda formula: formula.head.symbol not in excepts, formulas.search(element.symbol)):
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
    def generate_closure_item(item, formulas):
        for formula in formulas.search(item.current_element.symbol):
            if next_element := item.next_element:
                forward_set = ItemSetUtils.first_set(next_element, formulas)
            else:
                forward_set = {item.forward_token}

            for forward_token in forward_set:
                yield ItemBuilder.default(formula, forward_token=forward_token)

    @staticmethod
    def new_closure_items(item, closure, formulas):
        return {item for item in ItemSetUtils.generate_closure_item(item, formulas) if item not in closure}

    @staticmethod
    def closure(items, formulas):
        item_closure = items.copy()
        item_buffer = items.copy()

        while len(item_buffer) > 0:
            await_items = filter(lambda item: item.closure_enable, item_buffer.copy())
            item_buffer.clear()

            for item in await_items:
                item_buffer = item_buffer.union(ItemSetUtils.new_closure_items(item, item_closure, formulas))

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

    def expand_items(self):
        for items, number in self.items_number.items():
            for item in items:
                yield item, number

    def add(self, items):
        self.items_number[items] = self.items_count
        self.items_count += 1
