Tools for tracking git cherry pick operations

These are most useful when dealing with multiple long lived branches, where
one is cherry picking in both directions.  If one does a cherry pick and has
to change the patch to make it apply, the patch-id is no longer the same, and
git's existing tools are unable to associate it with the original.  As a
result, it's quite difficult to get an accurate list of commits that still
need to go from A to B, or from B to A.

Note that one commit can have multiple origins, and multiple commits can have
the same origin.  This is to facilitate the cases where you split a commit, or
squash multiple commits, when pulling the changes over.

Tools:
- git-origin: Add/set/remove/list origins on a commit.
- git-origin-blacklist: Mark a commit as blacklisted--will be shown as
                        existing in both branches without associating an
                        origin or origins.  This is useful for internal-only
                        changes you don't need to see when checking against
                        upstream.  This is also useful for handling git-revert
                        commits, but I'd like to find a better solution for
                        that.
- git-cherry-origins: Command like git-cherry but which obeys the origin data
                      rather than the patch-ids.
- git-log-origins: Wrapper around git-cherry-origins which provides a
                   git-log-like interface.  If 'tig' is available, it will use
                   it as the pager by default, otherwise it falls back to less
                   or more.
- git-origins-from-patch-id: Populates origin information using patch-id
                             information to identify identical commits.


TODO:
- Create a function which takes a Repo object and a file-like object with the
  blob data, which writes a new git object with that data into the git object
  database and returns a Blob object for it.
- Add a function which takes an index object and creates a Tree object from
  it, by running write-tree and creating a Tree from the new git object.
- Add a function which takes a Tree and creates a git commit from it,
  returning a Commit for that git object.
- Add a convenience function for a Repo which runs git-commit on its work tree
  and returns the new Commit object, as well as adding it to the Repo.
- Add a convenience class representing a git Index.  It should provide
  convenience methods for common tasks like updating the contents of the index
  and checking the index out into a work tree. The repo should hold an
  instance of this class for the default index.

Miscellaneous Notes:
Process for creating a commit that changes a file:
- read-tree: read a tree-ish into the index
- checkout-index: populate the working copy from the index

- update-index: update the index with modifications from the working copy

- write-tree: write a tree from the index
- commit-tree: create a commit from a tree
- update-ref: update ref to point at the new commit
