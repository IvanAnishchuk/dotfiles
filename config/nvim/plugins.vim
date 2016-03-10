call plug#begin('~/.config/nvim/plugged')

Plug 'croaky/vim-colors-github'
Plug 'danro/rename.vim'
Plug 'kchmck/vim-coffee-script'
Plug 'ctrlpvim/ctrlp.vim'
Plug 'tpope/vim-endwise'
Plug 'tpope/vim-fugitive'
Plug 'tpope/vim-surround'
Plug 'vim-scripts/matchit.zip'
Plug 'vim-scripts/ctags.vim'
Plug 'bling/vim-airline'
Plug 'scrooloose/nerdcommenter'
Plug 'scrooloose/nerdtree'
Plug 'godlygeek/tabular'
Plug 'junegunn/vader.vim'
"Plug 'tuxcanfly/ViMango'
Plug 'Chiel92/vim-autoformat'
Plug 'IvanAnishchuk/spell-vim'
Plug 'plasticboy/vim-markdown'
" New stuff
Plug 'janko-m/vim-test'
Plug 'benekastah/neomake'
Plug 'Shougo/deoplete.nvim'
Plug 'davidhalter/jedi-vim'
Plug 'rking/ag.vim'
" Colors
Plug 'altercation/vim-colors-solarized'
Plug 'freeo/vim-kalisi'
Plug 'IvanAnishchuk/pychimp-vim'
" Don't need this anymore/doesn't work with neovim
"Plug 'IvanAnishchuk/fb2-vim'
"Plug 'z2v/vim-yo-spell'
"Plug 'klen/rope-vim'

if filereadable(expand("~/.config/nvim/plugins.local.vim"))
  source ~/.config/nvim/plugins.local.vim
endif

call plug#end()
