import os
import argparse
import sys
import textwrap
import subprocess

from sqlalchemy import func

from . import data, base, diff

def main ():
    args = parse_args()
    args.func(args)

def parse_args ():
    parser = argparse.ArgumentParser(description='ugit - a simple git implementation')
    
    commands = parser.add_subparsers(title='Commands', dest='command')
    commands.required = True
    
    oid = base.get_oid
    
    init_parser = commands.add_parser('init', help='Initialize a new repository')
    init_parser.set_defaults(func=init)
    
    hash_objet_parser = commands.add_parser('hash-object', help='Compute object ID and optionally create a blob from a file')
    hash_objet_parser.set_defaults(func=hash_object)
    hash_objet_parser.add_argument('file', help='The file to hash')
    
    cat_file_parser = commands.add_parser('cat-file', help='Provide content of repository objects')
    cat_file_parser.set_defaults(func=cat_file)
    cat_file_parser.add_argument('object', type=oid, help='The object ID to display')
    
    write_tree_parser = commands.add_parser('write-tree', help='Write the current directory as a tree object')
    write_tree_parser.set_defaults(func=write_tree)
    
    read_tree_parser = commands.add_parser('read-tree', help='Read a tree object into the working directory')
    read_tree_parser.set_defaults(func=read_tree)
    read_tree_parser.add_argument('tree', type=oid, help='The tree object ID to read')
    
    commit_parser = commands.add_parser('commit', help='Create a new commit object')
    commit_parser.set_defaults(func=commit)
    commit_parser.add_argument('-m', '--message', required=True, help='The commit message')
    
    log_parser = commands.add_parser('log', help='Display commit logs')
    log_parser.set_defaults(func=log)
    log_parser.add_argument('oid', default='@', type=oid, nargs='?', help='The commit object ID to start from')
    
    checkout_parser = commands.add_parser('checkout', help='Checkout a commit into the working directory')
    checkout_parser.set_defaults(func=checkout)
    checkout_parser.add_argument('commit', help='The commit ID or branch name to checkout')
    
    tag_parser = commands.add_parser('tag', help='Create a new tag object')
    tag_parser.set_defaults(func=tag)
    tag_parser.add_argument('name', help='The name of the tag')
    tag_parser.add_argument('oid', default='@', type=oid, nargs='?', help='The object ID the tag points to')
    
    k_parser = commands.add_parser('k', help='')
    k_parser.set_defaults(func=k)
    
    branch_parser = commands.add_parser('branch', help='Create a new branch')
    branch_parser.set_defaults(func=branch)
    branch_parser.add_argument('name', nargs='?', help='The name of the branch to create')
    branch_parser.add_argument('start_point', default='@', type=oid, nargs='?', help='The object ID the branch points to')
    
    status_parser = commands.add_parser('status', help='Show the working tree status')
    status_parser.set_defaults(func=status)
    
    reset_parser = commands.add_parser('reset', help='Reset the current HEAD to the specified state')
    reset_parser.set_defaults(func=reset)
    reset_parser.add_argument('commit', type=oid, help='The commit ID or branch name to reset to')
    
    show_parser = commands.add_parser('show', help='Show various types of objects')
    show_parser.set_defaults(func=show)
    show_parser.add_argument('oid', default='@', type=oid, nargs='?', help='The object ID to show')
    
    diff_parser = commands.add_parser('diff', help='Show changes between commits, commit and working tree, etc')
    diff_parser.set_defaults(func=_diff)
    diff_parser.add_argument('commit', default='@', type=oid, nargs='?', help='Commit to compare against (default: HEAD)')
    diff_parser.add_argument('--cached', action='store_true', help='Show staged changes')
    
    merge_parser = commands.add_parser('merge', help='')
    merge_parser.set_defaults(func=merge)
    merge_parser.add_argument('commit', type=oid, help='')
    
    merge_base_parser = commands.add_parser('merge-base', help='')
    merge_base_parser.set_defaults(func=merge_base)
    merge_base_parser.add_argument('commit1', type=oid, help='')
    merge_base_parser.add_argument('commit2', type=oid, help='')
    
    return parser.parse_args()

# Command implementations
    
def init (args):
    """
    Initialize a new repository.
    Creates the .ugit directory structure.
        Usage: ugit init   
    """
    base.init()
    print (f'Initializing empty ugit repository in {os.getcwd()}/{data.GIT_DIR}')

def hash_object (args):
    """
    Hash a  file and store it as a blob object (read file in binary mode, 
    compute its SHA-1 hash, store it in .ugit/objects/ and print the object ID)
        Usage: ugit hash-object <file>
    """
    with open(args.file, 'rb') as f:
        print(data.hash_object(f.read()))

def cat_file (args):
    """
    Display the content of a repository object (given its object ID,
    read the corresponding file from .ugit/objects/ and print its content)
        Usage: ugit cat-file <object>
    """
    sys.stdout.flush()
    sys.stdout.buffer.write(data.get_object(args.object, expected=None))

    
def write_tree (args):
    """
    Write the current directory as a tree object (traverse the current directory,
    create blob objects for files and tree objects for subdirectories,
    store them in .ugit/objects/ and print the tree object ID)
        Usage: ugit write-tree
    """    
    print(base.write_tree())

def read_tree (args):
    """
    Read a tree object into the working directory (given a tree object ID,
    clear the current directory and recreate files and directories   
    according to the tree object)
        Usage: ugit read-tree <tree>
    """
    base.read_tree(args.tree)

def commit (args):
    """
    Create a new commit object (create a commit object with the current tree,
    the parent commit (if any) and the given commit message, updates HEAD to point to the new commit.
    store it in .ugit/objects/ and print the commit object ID)
        Usage: ugit commit -m <message>
    """
    print(base.commit(args.message))

def log (args):
    """
    Display commit logs (starting from the given commit object ID or HEAD,
    traverse the commit history and print each commit's ID and message)
        Usage: ugit log [<oid>]
    """
    refs = {}
    for refname, ref in data.iter_refs():
        refs.setdefault(ref.value, []).append(refname)

    for oid in base.iter_commits_and_parents([args.oid]):
        commit = base.get_commit(oid)
        
        _print_commit(oid, commit, refs.get(oid))

def checkout (args):
    """
    Checkout a commit into the working directory (Restores the working directory to
    the state of the given commit ID and updates HEAD to point to that commit.
        Usage: ugit checkout <oid>
    """
    base.checkout(args.commit)

def tag (args):
    """
    Create a new tag object (create a tag with the given name pointing to the specified object ID,
    store it in .ugit/objects/)
        Usage: ugit tag <name> <oid>
    """
    base.created_tag(args.name, args.oid)

def k (args):
    """
    Display a simplified commit graph (prints all references and their object IDs,
    then traverses all commits reachable from those references, printing each commit's ID and its parent commit ID)
        Usage: ugit k
    """
    dot = 'digraph commits {\n'
    
    oids = set()
    for refname, ref in data.iter_refs(deref=False):
        dot += f'"{refname}" [shape=box];\n'
        dot += f'"{refname}" -> "{ref.value}";\n'
        if not ref.symbolic:
            oids.add(ref.value)
    
    for oid in base.iter_commits_and_parents(oids):
        commit = base.get_commit(oid)
        dot += f'"{oid}" [shape=oval style=filled label="{oid[:10]}"];\n'
        for parent in commit.parents:
            dot += f'"{oid}" -> "{parent}"\n'
    
    dot += '}\n'
    print(dot)
    
    with subprocess.Popen(
        ['dot', '-Tpng'], 
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE
    ) as proc:
        out, _ = proc.communicate(dot.encode())
        with open('commit-graph.png', 'wb') as f:
            f.write(out)

def branch (args):
    """
    Create a new branch.
    Updates the reference for the branch name to point to the given object ID.
        Usage: ugit branch <name> <oid> 
    """
    if not args.name:
        current = base.get_branch_name()
        for branch in base.iter_branch_names():
            prefix = '*' if branch == current else ' '
            print(f'{prefix} {branch}')
    else:
        base.create_branch(args.name, args.start_point) 
        print(f'Branch {args.name} created at {args.start_point[:10]}')

def status (args):
    """
    Show the working tree status.
    Compares the current working directory with the index and HEAD commit,
    and prints the status of files (modified, staged, untracked).
        Usage: ugit status
    """
    HEAD = base.get_oid('@')
    branch = base.get_branch_name()
    if branch:
        print(f'On branch {branch}')
    else:
        print(f'HEAD detached at {HEAD}')
    MERGE_HEAD = data.get_ref('MERGE_HEAD').value
    if MERGE_HEAD:
        print(f'Merging with {MERGE_HEAD[:10]}')
    
    print('\nChanges to be committed:\n')
    HEAD_tree = HEAD and base.get_commit(HEAD).tree
    for path, action in diff.iter_changed_files(base.get_tree(HEAD_tree), base.get_working_tree()):
        print(f'{action:>12}: {path}')

def reset (args):
    """
    Reset to a specific commit.
    Restores the working directory to the state of the given commit ID
    and updates HEAD to point to that commit.
        Usage: ugit reset <commit>
    """
    base.reset(args.commit)
    print(f'HEAD reset to {args.commit[:10]}')

def _print_commit(oid, commit, refs=None):
    refs_str = f' ({", ".join(refs)})' if refs else ''
    print(f'commit {oid}{refs_str}\n')
    print(textwrap.indent(commit.message, '    '))
    print('')

def show (args):
    """
    Show various types of objects.
    Depending on the object type (blob, tree, commit, tag),
    displays its content in a human-readable format.
        Usage: ugit show <oid>
    """
    if not args.oid:
        return
    commit = base.get_commit(args.oid)
    
    parent_tree = None
    if commit.parents:
        parent_tree = base.get_commit(commit.parents[0]).tree
    _print_commit(args.oid, commit)
    result = diff.diff_trees(base.get_tree(parent_tree), base.get_tree(commit.tree))
    sys.stdout.flush()
    sys.stdout.buffer.write(result)

def _diff(args):
    tree = args.commit and base.get_commit(args.commit).tree
    
    result = diff.diff_trees(base.get_tree(tree), base.get_working_tree())
    sys.stdout.flush()
    sys.stdout.buffer.write(result)

def merge(args):
    base.merge(args.commit)

def merge_base(args):
    print(base.get_merge_base(args.commit1, args.commit2))