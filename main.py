from language import TokenParser
from parsers import SyntaxParser


def syntax_parse(parser, source_path, output_path):
    with open(source_path, 'r') as sources:
        error_list = parser(TokenParser.list(sources.readlines()))

    with open(output_path, 'w') as outputs:
        outputs.writelines(f'{error}\n' for error in error_list)


def main():
    parser = SyntaxParser()
    syntax_parse(parser, 'sources/source1.txt', 'outputs/output1.txt')
    syntax_parse(parser, 'sources/source2.txt', 'outputs/output2.txt')
    syntax_parse(parser, 'sources/source3.txt', 'outputs/output3.txt')
    syntax_parse(parser, 'sources/source4.txt', 'outputs/output4.txt')


if __name__ == '__main__':
    main()
