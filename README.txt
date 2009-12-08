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
:git-populate-origins:
    Populates origin information using patch-id
    information to identify identical commits.

TODO
----
- git-python: repo.commit(<some merge commit>) seems to ignore the merge
              commit, returning the next non-merge commit.
- git-python: getting the commit corresponding to a ref is not as easy as it
              should be.  You have to call find_all and grab the first
              element, which seems silly.  I think we should add a
              Commit.rev(ref) which calls rev-parse, then cat-file and parses
              that into a new Commit.  Either that, or we handle refs being
              passed into a Commit constructor.  You can do that today, but
              then the .id will point to the ref, it doesn't call rev-parse
              against it itself.
- git-cherry-origins: Implement.
- git-log-origins: Implement.
- git-populate-origins: Implement.
- git-origin: Add proper commandline argument handling, with subcommands for
  show/add/remove and possibly a subcommand to show the all of the origin data
  for the commits on the current (or specified) branch.
- Split up the cmd module.
- Switch everything to the logger module.
- git-python: Add our _rev function to Repo as a rev_parse method.

Uncertain:
- git-python: add Index class from git-origin.
- git-python: Make Repo utilize Index.
- git-python: Allow passing custom work tree and index in Repo's constructor.
              I really don't know if this would be useful, because it would
              still be using the default HEAD ref.  If you were to run
              repo.git.checkout() with a non-standard index and work tree, it
              would still update the HEAD ref, which would no longer match the
              primary checkout.  It would make it slightly more convenient for
              non-porcelain commands like read-tree/write-tree, but that's
              about all the usefulness I can see.

.. vim: set encoding=utf-8 ft=rst:
