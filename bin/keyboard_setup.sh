#1/bin/bash
# Separate script to be called for connected keyboards (I map it to Caps Lock)
# My favorite layout settings at the moment
setxkbmap -layout us -option compose:ralt,caps:none
# For tilde-less 60% keyboards (caps = esc, esc = backtick/tilde)
xmodmap -e 'clear Lock'
xmodmap -e 'keycode  9 = grave asciitilde grave asciitilde'
xmodmap -e 'keycode  66 = Escape NoSymbol Escape'
