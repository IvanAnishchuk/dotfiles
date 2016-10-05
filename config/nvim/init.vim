" Leader
let mapleader = ","

set backspace=2   " Backspace deletes like most programs in insert mode
set nobackup
set nowritebackup
set history=50
set ruler         " show the cursor position all the time
set showcmd       " display incomplete commands
set incsearch     " do incremental searching
set laststatus=2  " Always display the status line
set autowrite     " Automatically :write before running commands
syntax on
syntax enable

if filereadable(expand("~/.config/nvim/plugins.vim"))
  source ~/.config/nvim/plugins.vim
endif


" Load matchit.vim, but only if the user hasn't installed a newer version.
if !exists('g:loaded_matchit') && findfile('plugin/matchit.vim', &rtp) ==# ''
  runtime! macros/matchit.vim
endif

filetype plugin indent on

augroup vimrcEx
  autocmd!

  " When editing a file, always jump to the last known cursor position.
  " Don't do it for commit messages, when the position is invalid, or when
  " inside an event handler (happens when dropping a file on gvim).
  autocmd BufReadPost *
    \ if &ft != 'gitcommit' && line("'\"") > 0 && line("'\"") <= line("$") |
    \   exe "normal g`\"" |
    \ endif

  " Enable spellchecking for Markdown
  autocmd FileType mkd setlocal spell
augroup END

" When the type of shell script is /bin/sh, assume a POSIX-compatible
" shell for syntax highlighting purposes.
let g:is_posix = 1

" I'm not sure why I set 2 by default. It's good for html but for no code
" Softtabs, 2 spaces
set tabstop=2
set shiftwidth=2
set shiftround
set expandtab

" Display extra whitespace
set list listchars=tab:»·,trail:·,nbsp:·

" Use one space, not two, after punctuation.
set nojoinspaces

let g:ctrlp_map = '<C-p>'
let g:ctrlp_cmd = 'CtrlP'
let g:ctrlp_working_path_mode = 'ra'
let g:ctrlp_root_markers = ['manage.py']
" Use The Silver Searcher https://github.com/ggreer/the_silver_searcher
if executable('ag')
  " Use Ag over Grep
  set grepprg=ag\ --nogroup\ --nocolor

  " Use ag in CtrlP for listing files. Lightning fast and respects .gitignore
  let g:ctrlp_user_command = 'ag -Q -l --nocolor --hidden -g "" %s'

  " ag is fast enough that CtrlP doesn't need to cache
  let g:ctrlp_use_caching = 0
endif

" Color scheme tweaks, vary greatly on what theme I prefer this year
set t_Co=256
set background=dark
"colorscheme pychimp
colorscheme kalisi
"colorscheme solarized
"" Somewhat darker
"highlight clear Normal
"highlight Normal guifg=#d0d0d0 guibg=#202022  gui=none
"highlight clear NonText
"highlight NonText guibg=#22222f ctermbg=236
"highlight NonText guibg=#060606
"highlight Folded  guibg=#0A0A0A guifg=#9090D0
" Make it red, no underline: tyypo
"highlight clear SpellBad
"highlight SpellBad guibg=#603030 ctermbg=88
" Somewhat greenish dark blue for this: vim
"highlight clear SpellRare
"highlight SpellRare guibg=#1a2c2f ctermbg=236
" Dark yellow-ish here: colour/color
"highlight clear SpellLocal
"highlight SpellLocal guibg=#553f10
highlight clear ColorColumn
"highlight ColorColumn guibg=#2c2d27 ctermbg=235
highlight ColorColumn guibg=#3b3b3d ctermbg=235
let g:airline_theme='kalisi'
"syntax enable
"highlight clear ColorColumn
"highlight ColorColumn guibg=#2c2d27 ctermbg=235

" Make it obvious where 80 characters is
"set textwidth=80
" make it wide gray area (while 80 is still recommended, something ninety-ish is| acceptable, |but nothing beyond that!)
let &colorcolumn=join(range(80,98), ",")

" Numbers
set number relativenumber
set numberwidth=5

autocmd InsertEnter * setl norelativenumber
autocmd InsertLeave * setl relativenumber
autocmd WinEnter * setl relativenumber
autocmd WinLeave * setl norelativenumber

" Trying new mode switching
inoremap jk <Esc>

" Tab completion
" will insert tab at beginning of line,
" will use completion if not at beginning
set wildmode=list:longest,list:full
function! InsertTabWrapper()
    let col = col('.') - 1
    if !col || getline('.')[col - 1] !~ '\k'
        return "\<tab>"
    else
        return "\<c-p>"
    endif
endfunction
inoremap <Tab> <c-r>=InsertTabWrapper()<cr>
inoremap <S-Tab> <c-n>

" Switch between the last two files
nnoremap <leader><leader> <c-^>

"let g:vim_markdown_initial_foldlevel=999
let g:vim_markdown_gfm=0

" Get off my lawn
nnoremap <Left> :echoe "Use h"<CR>
nnoremap <Right> :echoe "Use l"<CR>
nnoremap <Up> :echoe "Use k"<CR>
nnoremap <Down> :echoe "Use j"<CR>

" linters
autocmd! BufWritePost * Neomake
nnoremap <leader>j :lopen<CR>
nnoremap <leader>k :lclose<CR>

" vim-test mappings
nnoremap <silent> <Leader>t :TestFile<CR>
nnoremap <silent> <Leader>s :TestNearest<CR>
nnoremap <silent> <Leader>l :TestLast<CR>
nnoremap <silent> <Leader>a :TestSuite<CR>
nnoremap <silent> <leader>gt :TestVisit<CR>

" Run commands that require an interactive shell
nnoremap <Leader>r :RunInInteractiveShell<space>

" Treat <li> and <p> tags like the block tags they are
let g:html_indent_tags = 'li\|p'

" Interpreters
" Needed for deoplete (might cause some trouble elsewhere)
let g:python3_host_prog = '/usr/bin/python3'
let g:python_host_prog = '/usr/bin/python'

" Autocompletion
let g:deoplete#enable_at_startup = 1
"autocmd FileType python setlocal omnifunc=jedi#completions
"let g:jedi#completions_enabled = 0
"let g:jedi#auto_vim_configuration = 0
"let g:jedi#smart_auto_mappings = 0
"let g:jedi#show_call_signatures = 0

" Open new split panes to right and bottom, which feels more natural
set splitbelow
set splitright

" Quicker window movement
nnoremap <C-j> <C-w>j
nnoremap <C-k> <C-w>k
nnoremap <C-h> <C-w>h
nnoremap <C-l> <C-w>l

" Terminal title
augroup termtitle
  autocmd VimEnter,WinEnter,BufWinEnter * exec 'set title'
augroup END

" Set spellfile to location that is guaranteed to exist, can be symlinked to
" Dropbox or kept in Git and managed outside of thoughtbot/dotfiles using rcm.
set spellfile=$HOME/.vim-spell-en.utf-8.add

" Autocomplete with dictionary words when spell check is on
set complete+=kspell

" Always use vertical diffs
set diffopt+=vertical

" Local config
if filereadable($HOME . "/.config/nvim/local.vim")
  source ~/.config/nvim/local.vim
endif

"Enable spellchecking
set spelllang=en_us
set spell
