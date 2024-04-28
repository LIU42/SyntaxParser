from items import Item

class BuildRecorder:

    def __init__(self, item_sets_path: str = "./records/itemsets.txt", conflicts_path: str = "./records/conflicts.txt") -> None:
        self.item_sets_file = open(item_sets_path, "w+", encoding = "utf-8")
        self.conflicts_file = open(conflicts_path, "w+", encoding = "utf-8")

    def __del__(self) -> None:
        self.item_sets_file.close()
        self.conflicts_file.close()

    def write_items(self, number: int, item_set: frozenset[Item]) -> None:
        self.item_sets_file.write(f"ItemsNo: {number}\n")
        for item in item_set:
            self.item_sets_file.write(f"{item}\n")

    def write_conflict(self, table_name: str, row: str, col: str, old_value: str, new_value: str) -> None:
        self.conflicts_file.write(f"{table_name} ({row}, {col}) old: {old_value} new: {new_value}\n")
