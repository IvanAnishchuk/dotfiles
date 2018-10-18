#!/bin/bash
# My favorite layout settings at the moment
# Separate script to be called for connected keyboards (I map it to Caps Lock)
# Unset caps lock (in case script is triggered by caps on new keyboard)
xset q | grep -o 'Caps Lock:   on' && xdotool key Caps_Lock
# normal us, additional escape on caps, compose on ralt
setxkbmap -layout us -option caps:escape,compose:ralt
# aditional backtick/tilde on esc
# For tilde-less 60% keyboards (caps = esc, esc = backtick/tilde)
xmodmap -e 'keycode  9 = grave asciitilde grave asciitilde'
