import os
import argparse
import sys

from . import data, base

def main ():
    args = parse_args()
    args.func(args)

def parse_args ():
    parser = argparse.ArgumentParser(description='ugit - a simple git implementation')
    
    commands = parser.add_subparsers(title='Commands', dest='command')
    commands.required = True
    
    init_parser = commands.add_parser('init', help='Initialize a new repository')
    init_parser.set_defaults(func=init)
    
    hash_objet_parser = commands.add_parser('hash-object', help='Compute object ID and optionally create a blob from a file')
    hash_objet_parser.set_defaults(func=hash_object)
    hash_objet_parser.add_argument('file', help='The file to hash')
    
    cat_file_parser = commands.add_parser('cat-file', help='Provide content of repository objects')
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument('object', help='The object ID to display')
    
    write_tree_parser = commands.add_parser('write-tree', help='Write the current directory as a tree object')
    write_tree_parser.set_defaults(func=write_tree)
    
    read_tree_parser = commands.add_parser('read-tree', help='Read a tree object into the working directory')
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument('tree', help='The tree object ID to read')
    
    commit_parser = commands.add_parser('commit', help='Create a new commit object')
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument('-m', '--message', required=True, help='The commit message')
    
    return parser.parse_args()

def init (args):
    data.init()
    print (f'Initializing empty ugit repository in {os.getcwd()}/{data.GIT_DIR}')

def hash_object (args):
    with open(args.file, 'rb') as f:
        print(data.hash_object(f.read()))

def cat_file (args):
    sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object, expected=None))

def write_tree (args):
    print(base.write_tree())

def read_tree (args):
    base.read_tree(args.tree)

def commit (args):
    print(base.commit(args.message))