# archive/

In-tree archive of host configs and assets that are no longer actively
managed but worth keeping recoverable. **rcm does not look at this
directory** because it only walks `host-*/` and `tag-*/` at the top
level — anything under `archive/` is inert until you move it back.

## Contents

- `host-he11/` — config for an old laptop (`he11`). Contains touchpad
  toggle scripts. To reactivate: `mv archive/host-he11 host-he11 && rcup`.
- `host-yoga/` — config for a yoga laptop (`yoga`). Contains
  bashrc.host, screen rotation/input toggle scripts, and a
  desktop-applications directory. To reactivate:
  `mv archive/host-yoga host-yoga && rcup`.
- `themes/` — XFCE Evolution themes (~8 MB). Kept for nostalgia.
  Not used by any current host.

## Why this exists

Keeping retired host configs in `archive/` instead of just relying on
the `legacy-archive` branch means you can grep, diff, and copy
fragments out of them without checking out a different branch.
`legacy-archive` is the canonical historical snapshot;
`archive/` is the forward-recoverable working set.
