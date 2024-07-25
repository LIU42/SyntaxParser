from language import TokenParser
from parsers import SyntaxParser


def preprocess(inputs):
    return TokenParser.list(inputs)


def syntax_parse(parser, source_path, result_path):
    with open(source_path, mode='r') as sources, open(result_path, mode='w') as results:
        inputs = sources.readlines()

        token_list = preprocess(inputs)
        error_list = parser(token_list)

        results.writelines(f'{error}\n' for error in error_list)


def main():
    parser = SyntaxParser()
    syntax_parse(parser, 'inputs/input1.txt', 'outputs/output1.txt')
    syntax_parse(parser, 'inputs/input2.txt', 'outputs/output2.txt')
    syntax_parse(parser, 'inputs/input3.txt', 'outputs/output3.txt')
    syntax_parse(parser, 'inputs/input4.txt', 'outputs/output4.txt')


if __name__ == '__main__':
    main()
