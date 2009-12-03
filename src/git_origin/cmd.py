"""Commands to be used as console scripts for git_origin."""

from sys import argv
from os import makedirs, environ
from os.path import join, isabs
from errno import EEXIST
from subprocess import call
from git.repo import Repo
from git.cmd import Git


notes_ref = "refs/notes/origins"


class Messenger:
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

def _commit(repo, ref="HEAD"):
    id = repo.git.rev_parse(ref, verify=True).strip()
    return repo.commit(id)

def _origins(commit):
    repo = commit.repo
    notes = _commit(repo, notes_ref)
    for fn in notes.tree:
        if fn == commit.id:
            blob = notes.tree[fn]
            return [repo.commit(id.strip()) for id in blob.data.splitlines()]

def _add_origin(origin, commit):
    origin_wd = join(commit.repo.path, "origins-wd")
    try:
        makedirs(origin_wd)
    except OSError, e:
        if e.errno != EEXIST:
            raise

    originenv = {
        "GIT_INDEX_FILE": join(commit.repo.path, "origins-index"),
        "GIT_WORK_TREE": origin_wd
    }

    ret = call(["git", "read-tree", notes_ref], env=originenv)
    if ret != 0:
        raise Exception("Unable to check out origins.")

    ret = call(["git", "checkout-index", "-af"], env=originenv)
    if ret != 0:
        raise Exception("Unable to check out origins.")

def new_blob(repo, data, path=None):
    args = dict(stdin=True, t="blob", w=True, input=data)
    if path:
        args["path"] = path
    hash = repo.git.hash_object(**args)
    return repo.blob(hash)

class Index(object):
    def __init__(self, repo, path=None):
        if path is None:
            path = join(repo.path, "index")
        self.git = repo.git
        #else:
        #    self.git = Git(repo.wd, index)
        self.path = path
        self.repo = repo

    # FIXME: Make update operate against the self.path index file.
    def update(self, path, cacheinfo=None, **kwargs):
        if isabs(path):
            path = path[1:]

        if cacheinfo:
            self.git.update_index("--cacheinfo", cacheinfo.mode,
                                       cacheinfo.blob.id, path, **kwargs)
        else:
            self.git.update_index(path, **kwargs)

# Commands
def origin():
    """Add the supplied commit-ish as an origin on HEAD (or the second supplied commit-ish)."""

    if "GIT_NOTES_REF" in environ:
        del environ["GIT_NOTES_REF"]

    repo = Repo()
    if len(argv) > 1:
        commitid = repo.git.rev_parse(argv[1].strip(), verify=True)
        commit = repo.commit(commitid)
        origins = _origins(commit)
        if origins:
            print("Origins for %s:" % commit)
            for origin in origins:
                print("    %s" % origin)
        #_add_origin(commit, commit)
        #blob = new_blob(repo, "Foo\nBar\nBaz", "/foo")
        #cacheinfo = Messenger(mode="0755", blob=blob)
        #index = Index(repo)
        #index.update("/foo", cacheinfo, add=True)
