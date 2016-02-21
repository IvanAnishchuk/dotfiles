#!/bin/bash
totoggle=( "AT Translated Set 2 keyboard" "SYNA2B29:00 06CB:77C6" )

for input in "${totoggle[@]}"; do
    status=$(xinput list-props "$input" | awk '/Device Enabled/{print $4}')
    if [ x"$status" == x"0" ]; then
        status=1
    else
        status=0
    fi
    xinput set-int-prop "$input" "Device Enabled" 8 $status
done
