#!/bin/bash
# Enable buttons
synclient ClickPad=1
# Tripple-tap
synclient TapButton3=2
# Click areas
synclient \
  RightButtonAreaLeft=800  RightButtonAreaRight=1175 \
  RightButtonAreaTop=450   RightButtonAreaBottom=648 \
  MiddleButtonAreaLeft=443 MiddleButtonAreaRight=780 \
  MiddleButtonAreaTop=450  MiddleButtonAreaBottom=648
# Sometimes that thing above doesn't work
# while this works...
xinput set-prop \
  "SYN1B7D:01 06CB:2991 UNKNOWN" \
  "Synaptics ClickPad" \
  1
xinput set-prop \
  "SYN1B7D:01 06CB:2991 UNKNOWN" \
  "Synaptics Tap Action" \
  2 3 0 0 1 3 2
xinput set-prop \
  "SYN1B7D:01 06CB:2991 UNKNOWN" \
  "Synaptics Soft Button Areas" \
  800  1175  450  648  \
  443  780   450  648
