from urllib.request import urlretrieve
import os
import json


def get_file(filepath):
    print('getting: {}'.format(filepath))
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    urlretrieve(url="https://raw.githubusercontent.com/dataloop-ai/dtlpy-documentation/main/{}".format(filepath),
                filename=filepath)


def extract_index_rec(root, filename, rst_string):
    filepath = root + '/' + filename
    get_file(filepath)
    with open(filepath) as f:
        index = json.load(f)
    for content in index['content']:
        name, ext = os.path.splitext(content['location'])
        if ext == '.json':
            rst_string += '{}\n'.format(content['displayName'])
            rst_string += '{}\n'.format('=' * len(content['displayName']))
            rst_string += '\n'
            rst_string += '{}\n'.format(content['description'])
            rst_string += '\n'
            rst_string = extract_index_rec(root=root,
                                           filename=content['location'],
                                           rst_string=rst_string)
        else:
            filepath = root + '/' + content['location']
            get_file(filepath=filepath)
            rst_string += '{}\n'.format(content['displayName'])
            rst_string += '{}\n'.format('~' * len(content['displayName']))
            rst_string += '\n'
            rst_string += '{}\n'.format(content['description'])
            rst_string += '\n'
            rst_string += '.. include:: {}\n'.format(filepath)
            rst_string += '  :parser: myst_parser.sphinx_\n'
            rst_string += '\n'
    return rst_string


def main():
    root = 'tutorials'
    filename = 'index.json'
    rst_string = ''
    rst_string += '{}\n'.format('Tutorials')
    rst_string += '{}\n'.format('*********')
    rst_string += '\n'
    rst_string = extract_index_rec(root, filename, rst_string)
    with open('tutorials.rst', 'w')as f:
        f.write(rst_string)


if __name__ == "__main__":
    main()
