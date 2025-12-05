import os
import itertools
import operator

from collections import namedtuple
from . import data

def write_tree(directory='.'):
    """
    Write the current directory as a tree object.
    Recursively traverses the directory, hashing files as blobs
    and subdirectories as trees. Returns the tree object ID.
    """
    entries = []
    with os.scandir(directory) as it:
        for entry in it:
            full = f'{directory}/{entry.name}'
            
            if is_ignored(full):
                continue
            
            if entry.is_file(follow_symlinks=False):
                type_ = 'blob'
                with open(full, 'rb') as f:
                    oid = data.hash_object(f.read())
            elif entry.is_dir(follow_symlinks=False):
                type_ = 'tree'
                oid = write_tree(full)
            entries.append((entry.name, oid, type_))
    
    tree = ''.join(f'{type_} {oid} {name}' 
                    for name, oid, type_ 
                    in sorted(entries))
    return data.hash_object(tree.encode(), 'tree')

def _iter_tree_entries(oid):
    """
    Iterate over entries in a tree object.
    Yields tuples (type, oid, name) for each entry in the tree.
    """
    if not oid:
        return
    tree = data.get_object(oid, 'tree')
    for entry in tree.decode().splitlines():
        type_, oid, name = entry.split(' ', 2)
        yield type_, oid, name

def get_tree (oid, base_path=''):
    """
    Build a dictionary of paths to object IDs from a tree object.
    Recursively expands subtrees to include all files and directories.
    """
    result = {}
    for type_, oid, name in _iter_tree_entries(oid):
        assert '/' not in name
        assert name not in ('.', '..')
        path = base_path + name
        if type_ == 'blob':
            result[path] = oid
        elif type_ == 'tree':
            result.update(get_tree(oid, f'{path}/'))
        else:
            assert False, f'Unknown tree entry type: {type_}'
    return result

def _empty_current_directory():
    """
    Clear the current working directory.
    Removes all files and directories except ignored paths (.ugit, .git, .venv).
    """
    for root, dirnames, filenames in os.walk('.', topdown=False):
        for filename in filenames:
            path = os.path.relpath(f'{root}/{filename}')
            if is_ignored(path) or not os.path.isfile(path):
                continue
            os.remove(path)
        for dirname in dirnames:
            path = os.path.relpath(f'{root}/{dirname}')
            if is_ignored(path):
                continue
            try:
                os.rmdir(path)
            except (FileNotFoundError, OSError):
                # Deletion might fail if the directory contains ignored files,
                # so it's OK
                pass

def read_tree(tree_oid):
    """
    Restore the working directory from a tree object.
    Clears the current directory and writes files from the tree object.
    """
    _empty_current_directory()
    for path, oid in get_tree(tree_oid, base_path='./').items():
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'wb') as f:
            f.write(data.get_object(oid))

def commit(message):
    """
    Create a new commit object.
    References the current tree, optionally includes the parent commit,
    and stores the commit with the given message. Updates HEAD.
    """
    commit = f'tree {write_tree()}\n'
    
    HEAD = data.get_HEAD()
    if HEAD:
        commit += f'parent {HEAD}\n'
    
    commit += '\n'
    commit += f'\n{message}\n'

    oid = data.hash_object(commit.encode(), 'commit')
    data.set_HEAD(oid)
    return oid

Commit = namedtuple('Commit', ['tree', 'parent', 'message'])
def get_commit(oid):
    """
    Parse a commit object.
    Returns a Commit namedtuple with fields: tree, parent, message.
    """
    parent = None
    
    commit = data.get_object(oid, 'commit').decode()
    lines = iter(commit.splitlines())
    for line in itertools.takewhile(operator.truth, lines):
        key, value = line.split(' ', 1)
        if key == 'tree':
            tree = value
        elif key == 'parent':
            parent = value
        else:
            assert False, f'Unknown commit field: {key}'
    
    message = '\n'.join(lines)
    return Commit(tree=tree, parent=parent, message=message)

def checkout(oid):
    """
    Checkout a commit.
    Restores the working directory to the state of the commit's tree
    and updates HEAD to point to the commit.
    """
    commit = get_commit(oid)
    read_tree(commit.tree)
    data.set_HEAD(oid)




def is_ignored(path):
    """
    Determine if a path should be ignored.
    Returns True if the path is inside `.ugit`, `.git`, or `.venv`.
    """
    ignored_dirs = {'.ugit', '.git', '.venv'}
    return os.path.basename(path) in ignored_dirs
