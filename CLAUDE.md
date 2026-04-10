# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Personal dotfiles, forked and rewritten from thoughtbot/dotfiles. Optimized for **bash + neovim** (zsh and ruby tooling were purged). Managed with [rcm](https://github.com/thoughtbot/rcm), not a bespoke install script — almost every change ultimately works by creating a symlink from `$HOME` into this repo.

## Installing / updating after edits

```
# first time only
env RCRC=$HOME/dotfiles/rcrc rcup
# subsequently (after editing any file here, or pulling)
rcup
```

`rcrc` sets `DOTFILES_DIRS="$HOME/dotfiles-local $HOME/dotfiles"`, so a sibling repo at `~/dotfiles-local` takes precedence over anything here. When adding or renaming a file, run `rcup` to (re)create the symlink — editing in place doesn't need it because `$HOME/.foo` is already a symlink into this repo.

`hooks/post-up` runs automatically after `rcup`: it touches `~/.psqlrc.local`, bootstraps vim-plug, runs `:PlugUpgrade + :PlugInstall + :PlugClean`, and refreshes the font cache.

## Layout conventions that matter

- **Top-level files** (`bashrc`, `aliases`, `profile`, `inputrc`, `tmux.conf`, …) become `~/.bashrc`, `~/.aliases`, etc. via rcm. Don't add a leading dot.
- **`config/`** maps to `~/.config/` (e.g. `config/nvim/init.vim` → `~/.config/nvim/init.vim`). Prefer putting new XDG-style config here rather than at the top level.
- **`bin/`** becomes `~/.bin`, which `bashrc` prepends to `PATH`. New personal scripts go here.
- **`host-<name>/`** are rcm tag directories for host-specific files (e.g. `host-yoga/bashrc.host` gets sourced by `bashrc` via `~/.bashrc.host`). Tags are enabled per host via rcm; don't put machine-specific state anywhere else.
- **`hooks/`** contains rcm lifecycle hooks (`post-up` is the important one).
- **`themes/`** is a bundle of XFCE themes, not code — leave alone unless explicitly asked.
- **`gnupg/`**, `config/systemd/user/` — installed configs for gpg-agent / systemd user services. `bashrc` expects gpg-agent to provide the SSH agent socket (`SSH_AUTH_SOCK=$(gpgconf --list-dirs agent-ssh-socket)`).

## Local-override pattern

Every major config file sources a `.local` sibling if present, so machine-private settings live **outside** this repo (typically in `~/dotfiles-local`). When adding a new config, follow the same pattern rather than hardcoding host-specific values:

- `~/.aliases.local` (from `aliases`)
- `~/.bashrc.local`, `~/.bashrc.host` (from `bashrc`)
- `~/.config/nvim/local.vim`, `~/.config/nvim/plugins.local.vim` (from `init.vim` / `plugins.vim`)
- `~/.config/git/config.local` (included via `[include]` in `config/git/config`)
- `~/.git_template.local/hooks/*` (sourced by each hook in `config/git_template/hooks/`)

## Neovim

Plugin manager is **vim-plug**; plugin list lives in `config/nvim/plugins.vim`. After changing it, either run `rcup` (the post-up hook will reinstall) or manually `nvim +PlugInstall +qa`. `init.vim` pins `g:python3_host_prog` / `g:python_host_prog` to virtualenv paths under `~/.local/share/virtualenvs/py3-*` and `py2-*` — these are the envs created by `repo/sync.sh` and the hash suffix is machine-specific, so it may need updating on a new host.

Leader is `,`. `jk` is mapped to `<Esc>` in insert mode. Arrow keys are deliberately disabled in normal mode. `:Neomake` runs on every write. Save-on-`:q` is on via `set autowrite`.

## Git template

`config/git/config` sets `init.templatedir = ~/.config/git_template`, so every `git init` / `git clone` installs the hooks in `config/git_template/hooks/`. They exist mainly to auto-regenerate **ctags** in the background on checkout/commit/merge/rewrite, and to source a `~/.git_template.local/hooks/<name>` override if present. Don't put project-specific logic in them.

Commits are `gpgsign = true` by default — keep this in mind when working on a machine without a configured signing key (override in `~/.config/git/config.local`).

Useful custom aliases defined here: `git prunebranches` (delete merged branches authored by you), `git up` / `git pur` (pull --rebase), `git pf` (push --force-with-lease), `git unpull` (reset to previous HEAD).

## Python CLI tools (`repo/`)

`repo/` is **not** application code — it's a mechanism for installing Python-based CLIs (awscli, httpie, pgcli, ipython, youtube-dl, pipenv itself, …) into three isolated pipenv environments (`py2/`, `py3/`, `docker/`) and then symlinking/copying their entrypoints into `~/.local/bin`. To rebuild after editing a `Pipfile`:

```
cd repo && ./sync.sh
```

`sync.sh` runs `pipenv install` in each subdir and copies every executable from the venv's `bin/` into `~/.local/bin`, skipping `python*`, `pip*`, `easy_install*`, and `wheel`. The `gui/` and `experimental/` dirs exist for staging and are currently empty / not wired into `sync.sh`.

## Requirements files

`requirements.txt` and `requirements2.txt` at the repo root are **not** used by `sync.sh`; they're leftover reference lists. The authoritative package lists are the `Pipfile`s under `repo/`.

## When editing

- Prefer the local-override pattern over host-specific branching inside these files.
- Paths in configs assume rcm has already symlinked things into `$HOME` — write them as `~/.config/…` (the final location), not `~/dotfiles/config/…`.
- If you add a new top-level file, remember it will become `~/.<name>` after `rcup`.
