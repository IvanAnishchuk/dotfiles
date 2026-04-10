#!/bin/bash

function exec_input_filter() {
  local i=""
  local t=""
  local k=""
  for i in "$@"
  do
    if [ "$t" == "" ] 
    then
      t="$i"
      read -p "$t" k
      k="$(echo "$k" | tr '[:upper:]' '[:lower:]')"
    elif [ "$k" == "$(echo "$i" | tr '[:upper:]' '[:lower:]')" ]
    then
       echo $k
       break
    fi
  done
  [ "$k" == "" -a "$i" != "__NODEFAULT__" ] && echo "__DEFAULT__"
}
func_input_filter=`declare -f exec_input_filter`

# the function is case-insensitive, and always converts the input to lowercase
# first argument is the message, next arguments are accepted values
# if the last argument is '__NODEFAULT__' then disallow entering empty-string
# if an empty-string is enetered then the function returns '__DEFAULT__'
function exec_input() {
  local a
  while true
  do
    a=$(exec_input_filter "$@")
    test "$a" != "" && echo $a && break
    echo "Invalid selection." > /dev/tty
  done
}
func_input=`declare -f exec_input`

function exec_issystem() {
  if [ "$(echo $sudo | grep 'sudo')" -o "$(echo $sudo | grep 'root')" ]
  then
    echo "1"
  fi
}
func_issystem=`declare -f exec_issystem`

if [ "$(exec_issystem)" ]
then
   shell_init_files=("sh:/etc/profile" "bash:/etc/profile" "zsh:/etc/zshenv" "csh:/etc/csh.cshrc" "csh:/etc/csh.login" "sh:usr/local/etc/profile" "bash:/usr/local/etc/profile" "zsh:/usr/local/etc/zshenv" "csh:/usr/local/etc/csh.cshrc" "csh:/usr/local/etc/csh.login")
else
   shell_init_files=("sh:$HOME/.profile" "bash:$HOME/.bash_profile" "bash:$HOME/.bash_login" "bash:$HOME/.profile" "zsh:$HOME/.zshenv" "zsh:$HOME/.zprofile" "zsh:$HOME/.zlogin" "csh:$HOME/.tcshrc" "csh:$HOME/.cshrc" "csh:$HOME/.login")
fi
