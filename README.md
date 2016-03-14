My dotfiles
===================

These are forked (and then rewritten) from thoughtbot dotfiles. Intended for my personal use but feel free to fork if you find them useful. I made a point not to add any personal or not reusable stuff except in hosts and tags but anything could happen.

Requirements
------------

Unlike the original thoughtbot dotfiles, these are optimized for bash and neovim. zsh and anything ruby-related was purged.

You still need rcm, of course, it's by far the best tool for this.

Install
-------

Clone the repo to `~/dotfiles`. Clone personal overrides repo (if you have one) to
`~/dotfiles-local`.

(Or, [fork and keep your fork
updated](http://robots.thoughtbot.com/keeping-a-github-fork-updated)).

Install [rcm](https://github.com/thoughtbot/rcm):

    sudo apt-add-repository -y ppa:martin-frost/thoughtbot-rcm
    sudo apt-get update
    sudo apt-get install rcm

Install the dotfiles:

    env RCRC=$HOME/dotfiles/rcrc rcup

After the initial installation, you can run `rcup` without the one-time variable
`RCRC` being set (`rcup` will symlink the repo's `rcrc` to `~/.rcrc` for future
runs of `rcup`). [See
example](https://github.com/thoughtbot/dotfiles/blob/master/rcrc).

This command will create symlinks for config files in your home directory.
Setting the `RCRC` environment variable tells `rcup` to use standard
configuration options:

* Exclude the `README.md` and `LICENSE` files, which are part of
  the `dotfiles` repository but do not need to be symlinked in.
* Give precedence to personal overrides which by default are placed in
  `~/dotfiles-local`

You can safely run `rcup` multiple times to update:

    rcup

You should run `rcup` after pulling a new version of the repository to symlink
any new files in the repository.

Make your own customizations
----------------------------

Not all of these will work, but I'm working on it:

* `~/.aliases.local`
* `~/.config/git/local`
* Where should I put it instead? `~/.git_template.local/*`
* `~/.tmux.conf.local`
* `~/.config/nvim/local.vim`
* `~/.config/nvim/plugins.local.vim`
* `~/.bashrc.local`
* `~/.psqlrc.local` (we supply a blank `.psqlrc.local` to prevent `psql` from
  throwing an error, but you should overwrite the file with your own copy)

What's in it?
-------------

It's quite different from the original, I'll describe it later.
