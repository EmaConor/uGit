import os
import hashlib

from collections import namedtuple

GIT_DIR = '.ugit'

def init ():
    """
    Initialize repository storage.
    Creates `.ugit` and `.ugit/objects` directories if they do not exist.
    """
    os.makedirs(GIT_DIR, exist_ok=True)
    os.makedirs(f'{GIT_DIR}/objects', exist_ok=True)

RefValue = namedtuple('RefValue', ['symbolic', 'value'])
def update_ref(ref, value):
    """
    Update a reference to point to a new value.
    Writes the new value to the corresponding file in `.ugit/refs/`.
    """
    assert not value.symbolic, "Symbolic refs not supported in update_ref"
    ref = _get_ref_internal(ref)[0]
    ref_path = f'{GIT_DIR}/{ref}'
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, 'w') as f:
        f.write(value.value)

def get_ref(ref):
    """
    Retrieve the value of a reference.
    Returns a RefValue namedtuple indicating if it's symbolic and its value.
    """
    return _get_ref_internal(ref)[1]

def _get_ref_internal(ref):
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
        return _get_ref_internal(value)
    
    return ref, RefValue(symbolic=False, value=value)

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

def iter_refs():
    """
    Iterate over all references in the repository.
    Yields tuples of (refname, refvalue).
    """
    refs = ['HEAD']
    for root, _, filesnames in os.walk(f'{GIT_DIR}/refs'):
        root = os.path.relpath(root, GIT_DIR)
        refs.extend(f'{root}/{names}' for names in filesnames)
    
    for refnames in refs:
        yield refnames, get_ref(refnames)