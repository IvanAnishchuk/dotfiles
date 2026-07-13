# Hand-off: git CLAUDE.md / exclude cleanup (finalize dotfiles)

**Date:** 2026-06-15 · **Status:** operational fix done across repos; **dotfiles
reconciliation still TODO (this doc).**

This is a hand-off for the agent that finalizes the dotfiles side. The per-repo
emergency cleanup is already done; what remains is making the dotfiles the single
clean source so the bug can't recur.

---

## 1. The bug

A **stale** `~/dotfiles/config/git_template/info/exclude` (838 B) globally ignored
a bare **`CLAUDE.md`** line. `CLAUDE.md` is a normal, committable project file and
must **never** be ignored globally — the meta-repo's root `CLAUDE.md` had to be
`git add -f`'d because of this.

### How it happened (root cause)

- `git config init.templatedir = ~/.config/git_template` (set in dotfiles
  `config/git/config`, symlinked to `~/.config/git/config`).
- Historically `~/.config/git_template/info/exclude` was itself a **symlink** to
  the dotfiles file above, and `git init`/`clone` **copies that symlink verbatim**
  — so every new repo got `.git/info/exclude` → the dotfiles file (838 B, with
  `CLAUDE.md`).
- On **2026-06-14** `~/.config/git_template/info/exclude` was replaced with a
  **corrected real file** (487 B, `CLAUDE.local.md` only, no `CLAUDE.md`). New
  clones from that point are fine — **but the ~160 already-existing repos kept
  their symlinks to the un-corrected dotfiles file**, and the dotfiles file itself
  was never corrected. That orphaned set is what broke.

---

## 2. What has already been done (no action needed)

- **All 160 repos** under `/home/user` whose `.git/info/exclude` symlinked the
  stale dotfiles file were **converted to independent real-file copies**, with the
  bare `CLAUDE.md` line **dropped** and `CLAUDE.local.md` + everything else kept.
  Verified 160/160. (They are now independent — no longer centrally managed.)
- The stale dotfiles file was **renamed** (content untouched):
  `config/git_template/info/exclude` → `config/git_template/info/exclude.DISABLED-20260615-claudemd-global-ignore`.
  → **dotfiles `git status` currently shows:** `D config/git_template/info/exclude`
  and `?? …exclude.DISABLED-20260615-…`. Nothing was committed.
- Per-repo decisions already applied:
  - `MEGAsync`, `meganz-sdk` — had a **stray** untracked `CLAUDE.md`; re-excluded
    it **locally** in their `.git/info/exclude` (interim; user may rename those to
    `CLAUDE.local.md` later).
  - `jose-hpke`, `unipy` — user's **own** projects; `CLAUDE.md` left **visible /
    committable**.
- Verified clean: `core.excludesFile` has no `CLAUDE.md` rule; a fresh `git init`
  leaves `CLAUDE.md` **not ignored**.

---

## 3. The divergence to reconcile

Two template-exclude files exist and disagree:

| Pattern | `~/.config/git_template/info/exclude` (487 B, live) | dotfiles `…/exclude.DISABLED-…` (838 B, stale) |
|---|---|---|
| `CLAUDE.md` | ❌ absent (correct) | ⚠️ **present (the bug)** |
| `CLAUDE.local.md` | ✅ | ✅ |
| build dirs, `.sdk-*`, `.clangd`, `compile_commands.json`, `review.md`, `/file`, `.test-run/`, `megaclient_statecache*.db` | ✅ | ✅ |
| `# claude-code-runtime` block (`**/.claude/scheduled_tasks.*`, `routines/.state/`, `worktrees/`, `checkpoints/`, `mailbox/`, `agent-registry.json`, `agent-memory-local`, `first-run`, `assistant-daemon-state.json`), `build-fuse/`, `.claude/settings.local.json` | ❌ **missing** | ✅ present |

So each file has something the other lacks. The detached per-repo copies were
built from the **838 B content minus `CLAUDE.md`** (i.e. the richer set).

---

## 4. Recommended target design (per user direction)

> **Universal excludes belong in `core.excludesFile` (`~/.config/git/ignore`),
> not copied into every repo via the template.** And `CLAUDE.md` must be in **no**
> ignore anywhere.

`~/.config/git/ignore` → dotfiles `config/git/ignore` (local-only, never committed
into any repo → zero upstream footprint, which is exactly what the `CLAUDE.local.md`
flow wants). Split the patterns by scope:

**A. Move to global `~/.config/git/ignore` (dotfiles `config/git/ignore`) — truly universal:**
```
# Claude Code: personal/local agent instructions (never committed anywhere)
CLAUDE.local.md
# Claude Code runtime state (never want this committed in any repo)
**/.claude/scheduled_tasks.lock
**/.claude/scheduled_tasks.json
**/.claude/routines/.state/
**/.claude/worktrees/
**/.claude/checkpoints/
**/.claude/mailbox/
**/.claude/agent-registry.json
**/.claude/agent-memory-local
**/.claude/first-run
**/.claude/assistant-daemon-state.json
.claude/settings.local.json
```
**Never add `CLAUDE.md` here.**

**B. Keep in the template `~/.config/git_template/info/exclude` (a REAL file — never
re-symlink it to dotfiles; that re-symlink is what caused the stale divergence) —
project-type-specific seeds only:**
```
build-clang21/  build-clang15/  build-sanitize/  build-warnaudit/  build-clang18/
build-warnaudit-clang/  build-cmake/  build-fuse/
.sdk-logs/  .clangd  compile_commands.json  .sdk-test-accounts.env
megaclient_statecache*.db  review.md  /file  .test-run/
```
Drop `CLAUDE.local.md` from the template once it lives in the global ignore (avoid
duplication). Consider trimming these C/SDK/mega-specific patterns too — they're
not universal — but that's optional.

---

## 5. Finalization steps

1. **Edit global ignore** — add block **A** to `config/git/ignore`. Confirm no
   `CLAUDE.md` line exists there.
2. **Fix the template** — make `~/.config/git_template/info/exclude` the real file
   from block **B** (no `CLAUDE.md`, no `CLAUDE.local.md`). **Keep it a regular
   file**; do **not** symlink it back to dotfiles. Decide whether/how the template
   itself is tracked in dotfiles (it currently is **not** dotfiles-managed —
   `~/.config/git_template` is a standalone real dir).
3. **Delete the quarantined file** once 1–2 are in place:
   `git rm config/git_template/info/exclude` (it's the deletion already staged-as-`D`)
   and remove `config/git_template/info/exclude.DISABLED-20260615-…`. Or keep the
   whole `config/git_template/` tree out of dotfiles entirely if the live template
   is the source of truth — your call; just don't leave the `CLAUDE.md` version
   reachable.
4. **Commit** the dotfiles changes (signed, explicit paths — no `git add -A`).
5. **(Optional) re-slim the 160 detached repo copies.** They currently carry
   `CLAUDE.local.md` + the runtime block inline; once global handles those it's
   redundant-but-harmless. Only worth a pass if you want them minimal.

---

## 6. Verification

```bash
# global ignore: CLAUDE.local.md yes, CLAUDE.md no
grep -nE 'CLAUDE' ~/.config/git/ignore        # expect only CLAUDE.local.md

# fresh repo: CLAUDE.md visible, CLAUDE.local.md + runtime ignored
t=$(mktemp -d); git -C "$t" init -q
git -C "$t" check-ignore CLAUDE.md           # expect: (no output, exit 1)
git -C "$t" check-ignore CLAUDE.local.md     # expect: match
git -C "$t" check-ignore .claude/settings.local.json
rm -rf "$t"

# no symlinks left pointing at the renamed dotfiles file
find /home/user -path '*/.git/info/exclude' -type l \
  -exec sh -c 'readlink "$1" | grep -q git_template/info/exclude$ && echo "$1"' _ {} \;
```

---

## 7. Reversal (if needed)

The 160 repos are now independent real-file copies. To restore central management,
re-point each `.git/info/exclude` at a corrected central file (symlink) — but note
that re-symlinking the **template's** `info/exclude` to dotfiles is what re-creates
the copy-the-symlink fragility; prefer the global-ignore design above.

---

## Open question

The mechanism that originally symlinked repo `.git/info/exclude` → dotfiles was
**not** `hooks/post-up` (that only bootstraps nvim/fonts/psqlrc). It was almost
certainly `git init` copying a then-symlinked template `info/exclude`. Worth
confirming no other script re-creates such symlinks before considering this closed.
