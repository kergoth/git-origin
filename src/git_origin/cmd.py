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
        else:
            self.git = Git(repo.wd)
            env = {
                "GIT_INDEX_FILE": path,
            }
            if not repo.bare:
                env["GIT_WORK_TREE"] = repo.wd
            self.git.extra["env"] = env

        self.path = path
        self.repo = repo

    def update(self, path, cacheinfo=None, **kwargs):
        if isabs(path):
            path = path[1:]

        if cacheinfo:
            self.git.update_index("--cacheinfo", cacheinfo.mode,
                                       cacheinfo.blob.id, path, **kwargs)
        else:
            self.git.update_index(path, **kwargs)

    def data_update(self, filename, data, mode="0644", **kwargs):
        hash = repo.git.hash_object(stdin=True, t="blob", w=True,
                                    input=data, path=filename)
        blob = repo.blob(hash)
        self.update(filename, Messenger(mode=mode, blob=blob), **kwargs)

    def checkout(self, wd=None, **kwargs):
        if wd is None:
            git = self.git
        else:
            git = Git(wd)
            git.extra = dict(self.git.extra)
            git.extra["env"]["GIT_WORK_TREE"] = wd
        return git.checkout_index(**kwargs)

    def read_tree(self, *args, **kwargs):
        return self.git.read_tree(*args, **kwargs)

    def write_tree(self, *args, **kwargs):
        return self.git.write_tree(*args, **kwargs)

def checkout_origins(repo):
    index = Index(repo, join(repo.path, "origins-index"))
    index.read_tree(notes_ref)
    index.checkout(join(repo.path, "origins-wd"), a=True, f=True)

def add_origin(repo, commit, origin):
    origins = _origins(commit) or []
    originids = [c.id for c in origins]
    if origin.id in originids:
        return

    origins.append(origin)
    originids.append(origin.id)

    index = Index(repo, join(repo.path, "origins-index"))
    index.read_tree(notes_ref)
    index.data_update(commit.id, "\n".join(originids), add=True)
    newtreeid = index.write_tree()
    newcommitid = repo.git.commit_tree(newtreeid,
                                       "-p", repo.commit(notes_ref).id,
                                       input="Add origin %s to commit %s" % (neworigin.id, commitid))
    repo.git.update_ref(notes_ref, newcommitid.strip())
    return True, origins

# Commands
def origin():
    """Add the supplied commit-ish as an origin on HEAD (or the second supplied commit-ish)."""

    if "GIT_NOTES_REF" in environ:
        del environ["GIT_NOTES_REF"]

    repo = Repo()
    if len(argv) > 1:
        origin = _commit(argv[1])
        try:
            commit = _commit(repo, argv[2])
        except IndexError:
            commit = _commit(repo)

        if add_origin(repo, commit, origin):
            print("Added origin %s to commit %s" % (origin.id, commit.id))
        else:
            print("Origin already set.")
    else:
        checkout_origins(repo)
