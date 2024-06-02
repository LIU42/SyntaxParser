from language import GrammarLoader
from language import TokenParser
from parsers import SyntaxParser

def parse_file(parser: SyntaxParser, input_path: str, output_path: str) -> None:
    with open(input_path, mode="r", encoding="utf-8") as input_file:
            token_list = TokenParser.parse_lines(input_file.readlines())
            error_list = parser(token_list)

    with open(output_path, mode="w", encoding="utf-8") as output_file:
        if len(error_list) > 0:
            output_file.write("Failure\n")
            for error in error_list:
                output_file.write(f"{error}\n")
        else:
            output_file.write("Success\n")


if __name__ == "__main__":
    parser = SyntaxParser(GrammarLoader())
    parse_file(parser, "./inputs/input1.txt", "./outputs/output1.txt")
    parse_file(parser, "./inputs/input2.txt", "./outputs/output2.txt")
    parse_file(parser, "./inputs/input3.txt", "./outputs/output3.txt")
    parse_file(parser, "./inputs/input4.txt", "./outputs/output4.txt")
  