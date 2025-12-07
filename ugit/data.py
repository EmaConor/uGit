import os
import hashlib
import shutil

from collections import namedtuple
from contextlib import contextmanager

GIT_DIR = None

@contextmanager
def change_git_dir(new_dir):
    global GIT_DIR
    old_dir = GIT_DIR
    GIT_DIR = f'{new_dir}/.ugit'
    yield
    GIT_DIR = old_dir

def init ():
    """
    Initialize repository storage.
    Creates `.ugit` and `.ugit/objects` directories if they do not exist.
    """
    os.makedirs(GIT_DIR, exist_ok=True)
    os.makedirs(f'{GIT_DIR}/objects', exist_ok=True)

RefValue = namedtuple('RefValue', ['symbolic', 'value'])
def update_ref(ref, value, deref=True):
    """
    Update the value of a reference.
    If the reference is symbolic, updates the target reference instead.
    """
    ref = _get_ref_internal(ref, deref)[0]
    
    assert value.value
    if value.symbolic:
        value = f'ref: {value.value}'
    else:
        value = value.value
    
    ref_path = f'{GIT_DIR}/{ref}'
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, 'w') as f:
        f.write(value)

def get_ref(ref, deref=True):
    """
    Retrieve the value of a reference.
    Returns a RefValue namedtuple indicating if it's symbolic and its value.
    """
    return _get_ref_internal(ref, deref)[1]

def _get_ref_internal(ref, deref):
    """
    Internal helper to retrieve reference value.
    Handles symbolic references and returns the resolved reference name and value.
    """ 
    ref_path = f'{GIT_DIR}/{ref}'
    value = None
    if os.path.isfile(ref_path):
        with open(ref_path, 'r') as f:
            value = f.read().strip()
    
    symbolic = bool(value) and value.startswith('ref: ')
    if symbolic:
        value = value.split(' ', 1)[1].strip()
        if deref:
            return _get_ref_internal(value, deref=True)
    
    return ref, RefValue(symbolic=symbolic, value=value)

def hash_object (data, type='blob'):
    """
    Store an object in `.ugit/objects`.
    Prepends the type (blob/tree/commit) to the data,
    computes its SHA-1 hash, saves it under `.ugit/objects/<oid>`,
    and returns the object ID. 
    """
    obj = type.encode() + b'\x00' + data
    oid = hashlib.sha1(obj).hexdigest()
    with open(f'{GIT_DIR}/objects/{oid}', 'wb') as out:
        out.write(obj)
    return oid

def get_object (oid, expected ='blob'):
    """
    Retrieve an object by its ID.
    Reads the object from `.ugit/objects/<oid>`, validates its type,
    and returns its content. 
    """
    with open (f'{GIT_DIR}/objects/{oid}', 'rb') as f:
        obj = f.read()
    
    type_, _, content = obj.partition(b'\x00')
    type_ = type_.decode() 
    
    if expected is not None:
        assert type_ == expected, f'Expected object of type {expected}, got {type_}'
    return content

def iter_refs(prefix='', deref=True):
    """
    Iterate over all references in the repository.
    Yields tuples of (refname, refvalue).
    """
    refs = ['HEAD', 'MERGE_HEAD']
    for root, _, filesnames in os.walk(f'{GIT_DIR}/refs'):
        root = os.path.relpath(root, GIT_DIR)
        refs.extend(f'{root}/{names}' for names in filesnames)
    
    for refname in refs:
        refname = refname.replace('\\', '/')
        if not refname.startswith(prefix):
            continue
        ref = get_ref(refname, deref=deref)
        if ref.value:
            yield refname, ref

def delete_ref(ref, deref=True):
    ref = _get_ref_internal(ref, deref)[0]
    os.remove(f'{GIT_DIR/{ref}}')

def object_exists(oid):
    return os.path.isfile(f'{GIT_DIR}/objects/{oid}')

def fetch_objects_if_missing(oid, remote_git_dir):
    if object_exists(oid):
        return
    remote_git_dir += '/.ugit'
    shutil.copy(f'{remote_git_dir}/objects/{oid}',
                f'{GIT_DIR}/objects/{oid}')

def push_object(oid, remote_git_dir):
    remote_git_dir += '/.ugit'
    shutil.copy(f'{GIT_DIR}/objects/{oid}',
                f'{remote_git_dir}/objects/{oid}')
