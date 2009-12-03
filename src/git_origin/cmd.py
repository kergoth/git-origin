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


def _commit(repo, ref="HEAD"):
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

    def checkout(self):
        self.index.read_tree(notes_ref)
        self.index.checkout(join(repo.path, "origins-wd"), a=True, f=True)

    def add(self, origin, commit="HEAD"):
        origin, commit = (_commit(repo, origin), _commit(repo, commit))

        origins = _origins(commit) or []
        originids = [c.id for c in origins]
        if origin.id in originids:
            return

        origins.append(origin)
        originids.append(origin.id)

        self.index.read_tree(notes_ref)
        self.index.data_update(commit.id, "\n".join(originids), add=True)
        newtreeid = self.index.write_tree()
        newcommitid = self.repo.git.commit_tree(newtreeid,
                                           "-p", _commit(self.repo, notes_ref).id,
                                           input="Add origin %s to commit %s" % (origin.id, commit.id))
        self.repo.git.update_ref(notes_ref, newcommitid)
        return True, origins

    def __getitem__(self, commit):
        notes = _commit(self.repo, notes_ref)
        try:
            blob = notes.tree[commit.id]
        except KeyError:
            return

        return [self.repo.commit(id.strip()) for id in blob.data.splitlines()]

    def __setitem__(self, commit, origins):
        git = self.repo.git
        msg = "Set origins for %s\n\nOrigins:\n%s"
        origindata = "\n".join(c.id for c in origins)
        notes_head = _commit(self.repo, notes_ref)

        self.index.read_tree(notes_ref)
        self.index.data_update(commit.id, origindata, add=True)
        newtreeid = self.index.write_tree()
        newcommitid = git.commit_tree(newtreeid,
                                      "-p", notes_head,
                                      input=msg % (commit.id, origindata))
        git.update_ref(notes_ref, newcommitid)

    def __delitem__(self, commit):
        git = self.repo.git
        msg = "Remove origins for %s"
        notes_head = _commit(self.repo, notes_ref)

        self.index.read_tree(notes_ref)
        self.index.update(commit.id, force_remove=True)
        newtreeid = self.index.write_tree()
        newcommitid = git.commit_tree(newtreeid,
                                      "-p", notes_head,
                                      input=msg % commit.id)
        git.update_ref(notes_ref, newcommitid)

    def __iter__(self):
        self.index.read_tree(notes_ref)
        commitids = self.index.git.ls_files().splitlines()
        return (self.repo.commit(c) for c in commitids)

# Commands
def origin():
    """Add the supplied commit-ish as an origin on HEAD (or the second supplied commit-ish)."""

    if "GIT_NOTES_REF" in environ:
        del environ["GIT_NOTES_REF"]

    if 1 < len(argv) < 4:
        repo = Repo()

        try:
            origin = _commit(repo, argv[1])
            try:
                commit = _commit(repo, argv[2])
            except IndexError:
                commit = _commit(repo)

            origindata = Origins(repo)
            origins = origindata[commit] or []

            if not origin.id in set(c.id for c in origins):
                origins.append(origin)
                origindata[commit] = origins
                print("Added origin %s to commit %s" % (origin.id, commit.id))
            else:
                print("Origin already set.")
        except GitCommandError, exc:
            exit("Failed to add origin when executing %s:\n%s" % (exc.command, exc.stderr))
    else:
        print >>stderr, usage
        exit(2)
