import os

from . import data, base

REMOTE_REFS_BASE = 'refs/heads/'
LOCAL_REFS_BASE = 'refs/remote/'

def fetch(remote_path):
    """
    Fetch objects and refs from a remote repository.

    :param remote_path: The path to the remote repository.
    """
    refs = _get_remote_refs(remote_path, REMOTE_REFS_BASE)
    
    for oid in base.iter_objects_in_commits(refs.values()):
        data.fetch_objects_if_missing(oid, remote_path)
    
    for remote_name, value in refs.items():
        refname = os.path.relpath(remote_name, REMOTE_REFS_BASE)
        data.update_ref(f'{LOCAL_REFS_BASE}/{refname}',
                        data.RefValue(symbolic=False, value=value))

def _get_remote_refs(remote_path, prefix=''):
    """
    Get all refs from a remote repository.

    :param remote_path: The path to the remote repository.
    :param prefix: A prefix to filter the refs.
    :return: A dictionary of refs.
    """
    with data.change_git_dir(remote_path):
        return{refname: ref.value for refname, ref in data.iter_refs(prefix)}

def push(remote_path, refname):
    """
    Push a ref to a remote repository.

    :param remote_path: The path to the remote repository.
    :param refname: The name of the ref to push.
    """
    remote_refs = _get_remote_refs(remote_path)
    remote_ref = remote_refs.get(refname)
    local_ref = data.get_ref(refname).value
    assert local_ref
    assert not remote_refs or base.is_ascestor_of(local_ref, remote_ref)
    
    know_remote_refs = filter(data.object_exists, remote_refs.values())
    remote_objects = set(base.iter_objects_in_commits(know_remote_refs))
    local_objects = set(base.iter_objects_in_commits({local_ref}))
    
    objects_to_push = local_objects - remote_objects
    
    for oid in objects_to_push:
        data.push_object(oid, remote_path)
    
    with data.change_git_dir(remote_path):
        data.update_ref(refname, data.RefValue(symbolic=False, value=local_ref))