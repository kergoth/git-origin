"""Commands to be used as console scripts for the git-origin project."""

from sys import argv
from os import makedirs, environ
from os.path import join, isabs
from errno import EEXIST
from subprocess import call
from sys import exit, stderr
from git.repo import Repo
from git.cmd import Git
from git.errors import GitCommandError


notes_ref = "refs/notes/origins"
usage = """git-origin ORIGIN [COMMIT]

ORIGIN - Commit to mark as an origin.
COMMIT - Commit which has ORIGIN as an origin (default=HEAD)"""


def _rev(repo, ref="HEAD"):
    id = repo.git.rev_parse(ref, verify=True)
    return repo.commit(id)


class Messenger:
    def __init__(self, **kwargs):
        self.__dict__ = kwargs


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

    def data_update(self, path, data, mode="0644", **kwargs):
        path = str(path)
        if isabs(path):
            path = path[1:]

        hash = self.repo.git.hash_object(stdin=True, t="blob", w=True,
                                         input=data, path=path)
        self.git.update_index("--cacheinfo", mode, hash, path, **kwargs)

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

    def update(self, path, **kwargs):
        self.git.update_index(path, **kwargs)


class Origins(object):
    def __init__(self, repo):
        self.repo = repo
        self.wd = join(repo.path, "origins-wd")
        self.index = Index(repo, join(repo.path, "origins-index"))
        self.ref = notes_ref

    def _commit(self, msg):
        parent = _rev(self.repo, self.ref)
        newtreeid = self.index.write_tree()
        newcommitid = self.repo.git.commit_tree(newtreeid, "-p", parent.id,
                                                input=msg)
        self.repo.git.update_ref(self.ref, newcommitid)
        return self.repo.commit(newcommitid)

    def _checkout(self):
        self.index.read_tree(self.ref)
        self.index.checkout(self.wd, a=True, f=True)

    def __getitem__(self, commit):
        head = _rev(self.repo, self.ref)
        try:
            blob = head.tree[commit.id]
        except KeyError:
            return

        return [self.repo.commit(id.strip()) for id in blob.data.splitlines()]

    def __setitem__(self, commit, origins):
        msg = "Set origins for %s\n\nOrigins:\n%s"
        origindata = "\n".join(c.id for c in origins)

        self.index.read_tree(self.ref)
        self.index.data_update(commit.id, origindata, add=True)
        self._commit(msg % (commit.id, origindata))

    def __delitem__(self, commit):
        self.index.read_tree(self.ref)
        self.index.update(commit.id, force_remove=True)
        self._commit("Remove origins for %s" % commit.id)

    def __iter__(self):
        self.index.read_tree(self.ref)
        commitids = self.index.git.ls_files().splitlines()
        return (self.repo.commit(c) for c in commitids)


def add_origin(repo, origin, commit="HEAD"):
    origin, commit = (_rev(repo, origin), _rev(repo, commit))

    origindata = Origins(repo)
    origins = origindata[commit] or []

    if not origin.id in set(c.id for c in origins):
        origins.append(origin)
        origindata[commit] = origins
        print("Added origin %s to commit %s" % (origin.id, commit.id))
    else:
        print("Origin already set.")


# Commands
def origin():
    """Add the supplied commit-ish as an origin on HEAD (or the second supplied commit-ish)."""

    if "GIT_NOTES_REF" in environ:
        del environ["GIT_NOTES_REF"]

    if 1 < len(argv) < 4:
        repo = Repo()
        try:
            add_origin(repo, *argv[1:])
        except GitCommandError, exc:
            exit("Failed to add origin when executing %s:\n%s" % (exc.command, exc.stderr))
    else:
        print >>stderr, usage
        exit(2)
