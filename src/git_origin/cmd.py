"""Commands to be used as console scripts for the git-origin project."""

from sys import argv
from os import makedirs, environ, sep
from os.path import join, isabs
from errno import EEXIST
from sys import exit, stderr
from subprocess import call
from StringIO import StringIO
from git.repo import Repo
from git.cmd import Git
from git.errors import GitCommandError
from git.commit import Commit


if "GIT_NOTES_REF" in environ:
    del environ["GIT_NOTES_REF"]


notes_ref = "refs/notes/origins"
blacklist_filename = "blacklist"
origin_usage = """git-origin ORIGIN [COMMIT]

ORIGIN - Commit to mark as an origin.
COMMIT - Commit which has ORIGIN as an origin (default=HEAD)."""
blacklist_usage = """git-blacklist COMMIT

COMMIT - Commit to add to the blacklist."""
cherry_usage = """git-cherry-origins [UPSTREAM [LOCAL]]

LOCAL - Local branch to compare against upstream, defaults to HEAD.
UPSTREAM - Upstream branch to compare against local, defaults to the remote
           the local branch is tracking."""


def _commit(repo, ref="HEAD"):
    return Commit(repo, repo.git.rev_parse(ref, verify=True))

def _existing_origins(repo, data):
    for id in data.splitlines():
        try:
            id = repo.git.rev_parse(id, verify=True)
            yield id
        except GitCommandError:
            continue

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
            wd = self.repo.wd
        else:
            git = Git(wd)
            git.extra = dict(self.git.extra)
            git.extra["env"]["GIT_WORK_TREE"] = wd

        try:
            makedirs(wd)
        except OSError, exc:
            if exc.errno != EEXIST:
                raise
        return git.checkout_index(**kwargs)

    def merge(self, remoteref, wd=None, **kwargs):
        if wd is None:
            git = self.git
        else:
            git = Git(wd)
            git.extra = dict(self.git.extra)
            git.extra["env"]["GIT_WORK_TREE"] = wd
        git.merge(remoteref)

    def merge_index(self, *args, **kwargs):
        wd = kwargs.get("work_tree")
        if wd is None:
            git = self.git
        else:
            git = Git(wd)
            git.extra = dict(self.git.extra)
            git.extra["env"]["GIT_WORK_TREE"] = wd
        return git.merge_index(*args, **kwargs)

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

    def push(self, remote):
        self.repo.git.push(remote, notes_ref)

    def pull(self, remote):
        fetches = self.repo.git.config("remote.%s.fetch" % remote, get_all=True)
        remote_ref = "refs/remotes/%s/origins" % remote
        refspec = "+%s:%s" % (self.ref, remote_ref)
        if not refspec in fetches.splitlines():
            self.repo.git.config("remote.%s.fetch" % remote, refspec, add=True)

        print(self.repo.git.fetch(remote))

        try:
            notes = self.repo.git.rev_parse(self.ref, verify=True)
        except GitCommandError:
            self.repo.git.update_ref(self.ref, remote_ref)
            return

        base = self.repo.git.merge_base(notes, remote_ref)
        self.index.read_tree(base, notes, remote_ref,
                             m=True, aggressive=True)
        self.index.checkout(self.wd, a=True, f=True)
        self.index.merge_index("-o", "git-merge-origins-driver", "-a")
        self._commit("Merge %s" % remote_ref, "-p", remote_ref)

    def _commit(self, msg, *commitargs):
        parent = _commit(self.repo, self.ref)
        newtreeid = self.index.write_tree()
        if newtreeid != parent.tree.id:
            newcommitid = self.repo.git.commit_tree(newtreeid, "-p", parent.id,
                                                    input=msg, *commitargs)
            self.repo.git.update_ref(self.ref, newcommitid)
            return self.repo.commit(newcommitid)

    def _checkout(self):
        self.index.read_tree(self.ref)
        self.index.checkout(self.wd, a=True, f=True)

    def __getitem__(self, commit):
        head = _commit(self.repo, self.ref)
        try:
            blob = head.tree[str(commit)]
        except KeyError:
            return

        return (Commit(self.repo, id) for id in _existing_origins(self.repo, blob.data))

    def __setitem__(self, commit, origins):
        msg = "Set origins for %s\n\nOrigins:\n%s"
        origindata = "\n".join(c.id for c in origins)

        self.index.read_tree(self.ref)
        self.index.data_update(str(commit), origindata, add=True)
        self._commit(msg % (commit, origindata))

    def __delitem__(self, commit):
        self.index.read_tree(self.ref)
        self.index.update(str(commit), force_remove=True)
        self._commit("Remove origins for %s" % commit)

    def __iter__(self):
        self.index.read_tree(self.ref)
        commitids = self.index.git.ls_files().splitlines()
        return (self.repo.commit(c) for c in commitids if c.strip() != blacklist_filename)


def add_origin(repo, origin, commit="HEAD"):
    origin, commit = (_commit(repo, origin), _commit(repo, commit))

    origindata = Origins(repo)
    origins = list(origindata[commit] or "")

    if not origin.id in set(c.id for c in origins):
        origins.append(origin)
        origindata[commit] = origins
        print("Added origin %s to commit %s" % (origin, commit))
    else:
        print("Origin already set")


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
        print >>stderr, origin_usage
        exit(2)


def add_blacklist(repo, commit):
    commit = _commit(repo, commit)

    origindata = Origins(repo)
    bldata = list(origindata[blacklist_filename] or "")

    if not commit.id in set(c.id for c in bldata):
        bldata.append(commit)
        origindata[blacklist_filename] = bldata
        print("Added commit %s to blacklist" % commit)
    else:
        print("Commit already in the blacklist")


def blacklist():
    """Add the supplied commit-ish to the blacklist."""

    if len(argv) == 2:
        repo = Repo()
        try:
            add_blacklist(repo, argv[1])
        except GitCommandError, exc:
            exit("Failed to add commit to blacklist when executing %s:\n%s" % (exc.command, exc.stderr))
    else:
        print >>stderr, blacklist_usage
        exit(2)


def left_right(repo, left, right, *args):
    def _rev_left_right(left, right):
        if args:
            revinfo = repo.git.rev_list("%s...%s" % (left, right), left_right=True, *args)
        else:
            revinfo = repo.git.rev_list("%s...%s" % (left, right), left_right=True)

        for rev in revinfo.splitlines():
            c = Commit(repo, rev[1:])
            c.direction = rev[0]
            yield c

    def _origins_batch(commits):
        blobs = "\n".join("%s:%s" % (notes_ref, c) for c in commits)
        contentstr = repo.git.cat_file(batch=True, input=blobs)
        content = StringIO(contentstr)
        while content:
            line = content.readline().rstrip()
            if not line:
                break

            words = line.split()
            if words[1] == "missing":
                yield None
                continue

            (hash, type, size) = words
            data = content.read(int(size))
            content.read(1) # Kill the trailing LF

            yield (Commit(repo, sha1) for sha1 in _existing_origins(repo, data))

    commits = list(_rev_left_right(left, right))
    commitmap = dict((c.id, c) for c in commits)
    commitids = set(c.id for c in commits)
    origindata = dict(zip(commits, _origins_batch(commits)))
    blorigins = Origins(repo)[blacklist_filename]
    if blorigins:
        blacklist = set(c.id for c in blorigins)
    else:
        blacklist = set()

    for (commit, origins) in origindata.iteritems():
        if commit.id in blacklist:
            commit.direction = "-"
        elif origins is not None:
            for o in origins:
                if o.id in commitmap:
                    commitmap[o.id].direction = "-"

            if all(o.id in commitids for o in origins):
                commit.direction = "-"

    return commits


def cherry():
    """Display a git-cherry-like view of the commits between two branches."""

    args = len(argv)
    repo = Repo()

    if args > 1:
        upstream = argv[1]
    else:
        headref = repo.git.rev_parse("HEAD", symbolic_full_name=True)
        if not headref:
            exit("Must supply upstream ref when using a detached HEAD.")

        upstream = repo.git.for_each_ref(headref, format="%(upstream)")
        if not upstream:
            exit("No remote tracking branch for this branch, please supply upstream ref.")

    if args > 2:
        local = argv[2]
    else:
        local = "HEAD"

    try:
        upstream, local = (_commit(repo, upstream), _commit(repo, local))
        extra = argv[3:]
        if extra:
            commits = reversed(left_right(repo, upstream, local, *extra))
        else:
            commits = reversed(left_right(repo, upstream, local))

        for c in commits:
            if c.direction == "-":
                print("%s %s" % (c.direction, c))
            elif c.direction == ">":
                print("+ %s" % c)
    except GitCommandError, exc:
        exit("Failed to display commits when executing %s:\n%s" % (exc.command, exc.stderr))

def _traverse(tree, path):
    parts = path.split(sep)
    while parts:
        piece = parts.pop(0)
        obj = tree[piece]
        if hasattr(obj, "mime_type"):
            yield obj

        tree = obj

def file():
    """For a given file, compare its history against UPSTREAM."""

    repo = Repo()
    fn = argv[1]
    upstream = argv[2]
    try:
        local = argv[3]
    except IndexError:
        local = "HEAD"

    lstart = Commit.find_all(repo, local, fn)[-1]
    initialblob = _traverse(lstart.tree, fn).next()
    def _commit_for_blob(ref, fn):
        upstream = Commit.find_all(repo, ref, fn)
        for commit in upstream:
            try:
                blob = _traverse(commit.tree, fn).next()
            except KeyError:
                return

            if blob.id == initialblob.id:
                return commit

    ustart = _commit_for_blob(upstream, fn)
    if ustart:
        upstream_precommits = set(c.id for c in Commit.find_all(repo, ustart, fn))
    else:
        print >>stderr, "Warning: upstream does not have the initial blob for %s." % fn

    upstream, local = (_commit(repo, upstream), _commit(repo, local))
    commits = reversed(left_right(repo, upstream, local, fn))
    for commit in commits:
        if ustart:
            if commit.direction != "-" and \
               commit.id in upstream_precommits:
                commit.direction = "-"
        print("%s %s" % (commit.direction, commit))


def pull():
    remote = argv[1]
    repo = Repo()
    origins = Origins(repo)
    try:
        origins.pull(remote)
    except GitCommandError, exc:
        exit("Unable to pull when executing %s:\n%s" % (exc.command, exc.stderr))

def push():
    remote = argv[1]
    repo = Repo()
    origins = Origins(repo)
    try:
        origins.push(remote)
    except GitCommandError, exc:
        exit("Unable to push when executing %s:\n%s" % (exc.command, exc.stderr))

def merge():
    repo = Repo()
    fn = argv[4]
    base = Blob(repo, argv[1], name=fn)
    left = Blob(repo, argv[2], name=fn)
    right = Blob(repo, argv[3], name=fn)

    origins = set(left.data.splitlines())
    base_origins = set(base.data.splitlines())
    right_origins = set(right.data.splitlines())

    removed = base_origins.difference(right_origins)
    for rem in removed:
        if rem in origins:
            origins.remove(rem)

    added = right_origins.difference(base_origins)
    for add in added:
        if not add in origins:
            origins.add(add)

    open(fn, "w").write(linesep.join(leftorigins))
