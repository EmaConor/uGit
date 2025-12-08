import subprocess

from collections import defaultdict
from tempfile import NamedTemporaryFile as Temp

from . import data

def compare_trees (*trees):
    """
    Compare multiple tree dictionaries. 
    Yields tuples of (path, oid1, oid2, ...) for each unique path 
    found in any of the provided trees.
    """
    entries = defaultdict(lambda: [None] * len(trees))
    for i, tree in enumerate(trees):
        for path, oid in tree.items():
            entries[path][i] = oid
    
    for path, oids in entries.items():
        yield (path, *oids)

def diff_trees (t_from, t_to):
    """
    Generate a diff between two tree objects.
    Compares the files in the two trees and returns a string
    summarizing the changes (added, removed, modified files).
    """
    output = b''
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            output += diff_blobs(o_from, o_to, path)
    return output

def diff_blobs (o_from, o_to, path='blob'):
    """
    Generate a diff between two blob objects.
    Uses the system `diff` command to compute the differences
    between the contents of the two blobs.   
    """
    with Temp() as f_from, Temp() as f_to:
        for oid, f in [(o_from, f_from), (o_to, f_to)]:
            if oid:
                f.write(data.get_object(oid))
                f.flush()
        
        with subprocess.Popen(
            ['diff', '--unified', '--show-c-function', '--label', f'a/{path}', f_from.name, '--label', f'b/{path}', f_to.name],
            stdout=subprocess.PIPE
        ) as proc:
            output, _ = proc.communicate()
        return output

def iter_changed_files(t_from, t_to):
    """
    Iterate over files that have changed between two trees.

    :param t_from: The from tree.
    :param t_to: The to tree.
    :return: A generator of (path, action) tuples.
    """
    for path, o_from, o_to in compare_trees(t_from, t_to):
        if o_from != o_to:
            action = ('new file' if not o_from else 'deleted' if not o_to else 'modified')
            yield path, action

def merge_trees(t_base, t_HEAD, t_other):
    """
    Merge three trees.

    :param t_base: The base tree.
    :param t_HEAD: The HEAD tree.
    :param t_other: The other tree.
    :return: The merged tree.
    """
    tree = {}
    for path, o_base, o_HEAD, o_other in compare_trees(t_base, t_HEAD, t_other):
        tree[path] = data.hash_objects(merge_blobs(o_base, o_HEAD, o_other))
    return tree

def merge_blobs(o_base, o_HEAD, o_other):
    """
    Merge three blobs.

    :param o_base: The base blob object ID.
    :param o_HEAD: The HEAD blob object ID.
    :param o_other: The other blob object ID.
    :return: The merged blob content.
    """
    with Temp() as f_base, Temp() as f_HEAD, Temp() as f_other:
        for oid, f in ((o_base, f_base), (o_HEAD, f_HEAD), (o_other, f_other)):
            if oid:
                f.write(data.get_object(oid))
                f.flush()
        with subprocess.Popen(
            ['diff3', '-m',
            '-L', 'HEAD', f_HEAD.name,
            '-L', 'BASE', f_base.name,
            '-L', 'MERGE_HEAD', f_other.name,
            ], stdout=subprocess.PIPE) as proc:
            output, _ = proc.communicate()
            assert proc.returncode in (0, 1)
        return output