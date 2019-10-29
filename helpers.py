import json
from argparse import ArgumentParser

if __name__ == '__main__':
    parser = ArgumentParser(prefix_chars='--')
    parser.add_argument('--path', type=str, default='candidates_filtered_in.json',
                        help='Save path')
    options = parser.parse_args()

    with open(options.path, encoding='utf-8') as f:
        input_dict = json.load(f)

    print("Count: {}".format(len(input_dict)))
