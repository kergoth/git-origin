"""Commands to be used as console scripts for git_origin."""

from sys import argv
from os import makedirs
from os.path import join
from errno import EEXIST
from git.repo import Repo
from git.cmd import Git


notes_ref = "refs/notes/origins"


def _commit(repo, ref=None):
    if ref is None:
        ref = "HEAD"
    id = repo.git.rev_parse(ref, verify=True).strip()
    return repo.commit(id)

def _origins(commit):
    repo = commit.repo
    commits = repo.commits(notes_ref, max_count=1)
    for fn in commits[0].tree:
        if fn == commit.id:
            blob = head.tree[fn]
            return [repo.commit(id.strip()) for id in blob.data.splitlines()]

def _add_origin(origin, commit):
    git = commit.repo.git
    origin_wd = join(commit.repo.path, "checkout_wd")
    git.execute(["git", "--work-tree=%s" % origin_wd, "checkout", "-f", notes_ref])

# Commands
def origin():
    """Add the supplied commit-ish as an origin on HEAD (or the second supplied commit-ish)."""
    print(argv)
