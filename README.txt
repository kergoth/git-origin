git-origin
==========

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

Tools
-----
:git-origin: Add/set/remove/list origins on a commit.
:git-origin-blacklist:
    Mark a commit as blacklisted--will be shown as
    existing in both branches without associating an
    origin or origins.  This is useful for internal-only
    changes you don't need to see when checking against
    upstream.  This is also useful for handling git-revert
    commits, but I'd like to find a better solution for
    that.
:git-cherry-origins:
    Command like git-cherry but which obeys the origin data
    rather than the patch-ids.
:git-log-origins:
    Wrapper around git-cherry-origins which provides a
    git-log-like interface.  If 'tig' is available, it will use
    it as the pager by default, otherwise it falls back to less
    or more.
:git-origins-from-patch-id:
    Populates origin information using patch-id
    information to identify identical commits.

TODO
----
- :git-python: Alter cmd.Git class to accept both work tree and index file,
               and to obey both paths via the environment.
- Fix the Index class to use the above functionality to ensure it obeys the
  path to that particular index.
- Add checkout method to the Index class to make calls to checkout-index
  more convenient, operating against this specific index into a specified
  work tree.
- Add a function which takes an Index and uses write-tree to generate a
  tree object for it, returning the new Tree.
- Add a function which takes a Tree and creates a git commit from it,
  returning the new Commit.
- Add a function which takes a Repo and does a commit using its index and
  work tree and returns the new Commit object.

Miscellaneous Notes
-------------------
Process for creating a commit that changes a file:

#. :read-tree: read a tree-ish into the index
#. :checkout-index: populate the working copy from the index
#. :update-index: update the index with modifications from the working copy
#. :write-tree: write a tree from the index
#. :commit-tree: create a commit from a tree
#. :update-ref: update ref to point at the new commit

.. vim: set encoding=utf-8 ft=rst:
