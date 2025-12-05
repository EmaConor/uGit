import os
import hashlib

GIT_DIR = '.ugit'

def init ():
    """
    Initialize repository storage.
    Creates `.ugit` and `.ugit/objects` directories if they do not exist.
    """
    os.makedirs(GIT_DIR, exist_ok=True)
    os.makedirs(f'{GIT_DIR}/objects', exist_ok=True)

def update_ref(ref, oid):
    """
    Update HEAD to point to the given commit object ID.
    """
    ref_path = f'{GIT_DIR}/{ref}'
    os.makedirs(os.path.dirname(ref_path), exist_ok=True)
    with open(ref_path, 'w') as f:
        f.write(oid)

def get_ref(ref):
    """
    Retrieve the current commit ID from HEAD.
    Returns None if HEAD does not exist.
    """
    ref_path = f'{GIT_DIR}/{ref}'
    if os.path.isfile(ref_path):
        with open(ref_path, 'r') as f:
            return f.read().strip()  

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