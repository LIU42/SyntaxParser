import json

from parsers import SyntaxParser
from language import TokenParser

class MainProgram:

    def __init__(self, grammar_path: str = "./grammars/grammar.json") -> None:
        with open(grammar_path, "r", encoding = "utf-8") as grammar_file:
            self.parser = SyntaxParser(json.load(grammar_file))

    def parse_file(self, input_path: str = "./inputs/input1.txt", output_path: str = "./outputs/output1.txt") -> None:
        with open(input_path, "r", encoding = "utf-8") as input_file:
            token_list = TokenParser.parse_lines(input_file.readlines())
            error_list = self.parser(token_list)

        with open(output_path, "w+", encoding = "utf-8") as output_file:
            if len(error_list) > 0:
                output_file.write("Failure\n")
                for error in error_list:
                    output_file.write(f"{error}\n")
            else:
                output_file.write("Success\n")

if __name__ == "__main__":
    main_program = MainProgram()
    main_program.parse_file("./inputs/input1.txt", "./outputs/output1.txt")
    main_program.parse_file("./inputs/input2.txt", "./outputs/output2.txt")
    main_program.parse_file("./inputs/input3.txt", "./outputs/output3.txt")
    main_program.parse_file("./inputs/input4.txt", "./outputs/output4.txt")
  