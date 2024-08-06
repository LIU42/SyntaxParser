from language import TokenParser
from parsers import SyntaxParser


def syntax_parse(parser, source_path, result_path):
    with open(source_path, 'r') as sources:
        error_list = parser(TokenParser.list(sources.readlines()))

    with open(result_path, 'w') as results:
        results.writelines(f'{error}\n' for error in error_list)


def main():
    parser = SyntaxParser()
    syntax_parse(parser, 'sources/source1.txt', 'results/result1.txt')
    syntax_parse(parser, 'sources/source2.txt', 'results/result2.txt')
    syntax_parse(parser, 'sources/source3.txt', 'results/result3.txt')
    syntax_parse(parser, 'sources/source4.txt', 'results/result4.txt')


if __name__ == '__main__':
    main()
