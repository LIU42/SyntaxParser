from items import Item

class BuildRecorder:

    def __init__(self, items_path: str = "./records/itemsets.txt", conflicts_path: str = "./records/conflicts.txt") -> None:
        self.items_path = items_path
        self.conflicts_path = conflicts_path
        self.items_file = None
        self.conflicts_file = None

    def __del__(self) -> None:
        if self.items_file is not None and self.conflicts_file is not None:
            self.items_file.close()
            self.conflicts_file.close()

    def open_files(self) -> None:
        self.items_file = open(self.items_path, "w+", encoding = "utf-8")
        self.conflicts_file = open(self.conflicts_path, "w+", encoding = "utf-8")

    def write_items(self, number: int, items: frozenset[Item]) -> None:
        self.items_file.write(f"ItemsNo: {number}\n")
        for item in items:
            self.items_file.write(f"{item}\n")

    def write_conflict(self, table_name: str, row: object, col: object, old_value: object, new_value: object) -> None:
        self.conflicts_file.write(f"{table_name} ({row}, {col}) old: {old_value} new: {new_value}\n")
