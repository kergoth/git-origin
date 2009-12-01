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

TODO:
- GitPython:
  - Add mechanisms/classes to manipulate the GIT_INDEX_FILE and GIT_WORK_TREE
    being used for the git commands.
  - Add mechanisms/classes to facilitate programmatically taking a tree,
    altering it, reading it into the index, generating a commit from that
    index, and updating a ref to point at the new commit.

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
