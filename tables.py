from collections import defaultdict

from items import ItemBuilder
from items import ItemsNumber
from items import ItemSetUtils

from language import GrammarLoader
from language import TokenParser


class TableElement:

    def __init__(self, row, col, value):
        self.row = row
        self.col = col
        self.value = value

    def __str__(self):
        return self.sequences

    def __iter__(self):
        return iter((self.row, self.col, self.value))

    @property
    def sequences(self):
        return f'{self.row} {self.col} {self.value}\n'


class TableConflict:

    def __init__(self, name, row, col, old_value, new_value):
        self.name = name
        self.row = row
        self.col = col
        self.old_value = old_value
        self.new_value = new_value

    def __str__(self):
        return f'{self.name} ({self.row}, {self.col}) old: {self.old_value} new: {self.new_value}'


class ConflictBuilder:

    @staticmethod
    def build(name, location, old_value, new_value):
        row = location[0]
        col = location[1]

        return TableConflict(name, row, col, old_value, new_value)


class AbstractTable:

    def __init__(self, name):
        self.elements = defaultdict(dict)
        self.name = name
        self.conflicts = []

    def __getitem__(self, location):
        row = location[0]
        col = location[1]

        return self.elements[row][col]

    def __setitem__(self, location, value):
        row = location[0]
        col = location[1]

        if col in self.elements[row]:
            self.conflicts.append(ConflictBuilder.build(self.name, location, self.elements[row][col], value))
        else:
            self.elements[row][col] = value

    def set_elements(self, elements):
        for element in elements:
            self.elements[element.row][element.col] = element.value

    @property
    def element_list(self):
        return [TableElement(row, col, value) for row, cols in self.elements.items() for col, value in cols.items()]


class ActionOption:

    def __init__(self, option, number):
        self.option = option
        self.number = number

    def __str__(self):
        return f'{self.option}-{self.number}'

    @property
    def is_accept(self):
        return self.option == 'A'

    @property
    def is_shift(self):
        return self.option == 'S'

    @property
    def is_reduce(self):
        return self.option == 'R'


class ActionBuilder:

    @staticmethod
    def shift(status):
        return ActionOption(option='S', number=int(status))

    @staticmethod
    def reduce(number):
        return ActionOption(option='R', number=int(number))

    @staticmethod
    def accept():
        return ActionOption(option='A', number=0)


class ActionParser:

    @staticmethod
    def parse(input):
        option, number = input.strip().split('-')

        if option == 'A':
            return ActionBuilder.accept()
        if option == 'S':
            return ActionBuilder.shift(number)
        if option == 'R':
            return ActionBuilder.reduce(number)
        return None


class ActionTable(AbstractTable):

    @staticmethod
    def deserialize(input):
        last_status, token, option = input.strip().split()

        token = TokenParser.simply(token)
        option = ActionParser.parse(option)

        return TableElement(int(last_status), token, option)

    def save(self):
        with open('tables/action.txt', 'w') as actions:
            actions.writelines(element.sequences for element in self.element_list)

    def load(self):
        with open('tables/action.txt', 'r') as actions:
            self.set_elements(map(self.deserialize, actions.readlines()))


class GotoTable(AbstractTable):

    @staticmethod
    def deserialize(input):
        last_status, symbol, next_status = input.strip().split()

        last_status = int(last_status)
        next_status = int(next_status)

        return TableElement(last_status, symbol, next_status)

    def save(self):
        with open('tables/goto.txt', 'w') as gotos:
            gotos.writelines(element.sequences for element in self.element_list)

    def load(self):
        with open('tables/goto.txt', 'r') as gotos:
            self.set_elements(map(self.deserialize, gotos.readlines()))


class TableBuilder:

    @staticmethod
    def action():
        return ActionTable('actions')

    @staticmethod
    def goto():
        return GotoTable('gotos')

    @staticmethod
    def transforms():
        return AbstractTable('transforms')


class BuildReport:

    def __init__(self, conflicts, items_number):
        self.conflicts = conflicts
        self.items_number = items_number

    @property
    def items_records(self):
        for item, number in self.items_number.expand_items():
            yield f'items: {number} {item}\n'

        yield f'total count: {self.items_number.items_count}\n'

    @property
    def conflict_records(self):
        for conflict in self.conflicts:
            yield f'{conflict}\n'

    def save(self):
        with open('reports/items.txt', 'w') as items:
            items.writelines(self.items_records)

        with open('reports/conflicts.txt', 'w') as conflicts:
            conflicts.writelines(self.conflict_records)


class ActionGotoTable:

    def __init__(self):
        self.actions = TableBuilder.action()
        self.gotos = TableBuilder.goto()

    @staticmethod
    def create_transforms(formulas):
        transforms = TableBuilder.transforms()
        init_items = ItemSetUtils.closure({ItemBuilder.default(formulas.init)}, formulas)

        items_buffer = {init_items}
        items_number = ItemsNumber(init_items)

        while len(items_buffer) > 0:
            current_item_sets = items_buffer.copy()
            items_buffer.clear()

            for items in current_item_sets:
                for element in ItemSetUtils.transform_elements(items):
                    next_items = ItemSetUtils.next_items(items, element, formulas)

                    if next_items not in items_number:
                        items_number.add(next_items)
                        items_buffer.add(next_items)

                    transforms[items_number[items], element] = items_number[next_items]

        return items_number, transforms
    
    def setup_tables(self, formulas):
        items_number, transforms = self.create_transforms(formulas)

        for last_status, element, next_status in transforms.element_list:
            if element.is_symbol:
                self.gotos[last_status, element.symbol] = next_status
            else:
                self.actions[last_status, element.token] = ActionBuilder.shift(next_status)

        for item, number in items_number.expand_items():
            if item.search_finished:
                if item.formula == formulas.init and item.forward_token.is_end:
                    option = ActionBuilder.accept()
                else:
                    option = ActionBuilder.reduce(formulas.number(item.formula))

                self.actions[number, item.forward_token] = option

        return BuildReport(transforms.conflicts + self.actions.conflicts + self.gotos.conflicts, items_number)

    def build(self, formulas):
        self.setup_tables(formulas).save()

    def save(self):
        self.actions.save()
        self.gotos.save()

    def load(self):
        self.actions.load()
        self.gotos.load()

    def action(self, last_status, token):
        try:
            return self.actions[last_status, token]
        except KeyError:
            return None
    
    def goto(self, last_status, symbol):
        try:
            return self.gotos[last_status, symbol]
        except KeyError:
            return None


def build():
    tables = ActionGotoTable()
    tables.build(GrammarLoader.formulas())
    tables.save()


if __name__ == '__main__':
    build()
