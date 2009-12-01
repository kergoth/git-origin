"""Commands to be used as console scripts for git_origin."""

from sys import argv
from os import makedirs, environ
from os.path import join
from errno import EEXIST
from subprocess import call
from git.repo import Repo
from git.cmd import Git


notes_ref = "refs/notes/origins"


def _commit(repo, ref="HEAD"):
    id = repo.git.rev_parse(ref, verify=True).strip()
    return repo.commit(id)

def _origins(commit):
    repo = commit.repo
    commits = repo.commits(notes_ref, max_count=1)
    tree = commits[0].tree
    for fn in tree:
        if fn == commit.id:
            blob = tree[fn]
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
        _add_origin(commit, commit)
