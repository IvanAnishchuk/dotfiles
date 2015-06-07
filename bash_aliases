# Unix
alias tlf="tail -f"
alias ln='ln -v'
alias mkdir='mkdir -p'
alias ...='../..'

# ls
alias l='ls -CF'
alias ll='ls -alF'
alias la='ls -A'
alias lh='ls -Alh'

# FIXME: -g? zsh stuff?
#alias -g G='| grep'
#alias -g M='| less'
#alias -g L='| wc -l'
#alias -g ONE="| awk '{ print \$1}'"
alias e="$EDITOR"
alias v="$VISUAL"

# git
alias gci="git pull --rebase && rake && git push"

# Bundler
alias b="bundle"

# Tests and Specs
alias t="ruby -I test"
alias cuc="bundle exec cucumber"

# Rails
alias migrate="rake db:migrate db:rollback && rake db:migrate db:test:prepare"
alias m="migrate"
alias rk="rake"
alias s="rspec"
alias z="zeus"

# Include custom aliases
[[ -f ~/.aliases.local ]] && source ~/.aliases.local

# Net stuff
alias myip="dig +short myip.opendns.com @resolver1.opendns.com"
alias whois="whois -H"

# mplayer (downmixing 5.1 sound stream)
alias mplayer6='mplayer -af pan=2:1:.39:.6:.6:.39:.17:-.17:-.17:.17:.32:.32:.33:.33 -channels 2'

# servers don't usually support my locale
alias ssh='LANG=en_US.UTF-8 LC_ALL=en_US.UTF-8 ssh'
