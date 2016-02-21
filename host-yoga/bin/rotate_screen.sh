#!/bin/bash

rangex=( 0 3408 )
rangey=( 0 1872 )
torotate=( "ELAN21EF:00 04F3:21EF" )

xrandrout="$(xrandr |grep eDP1 | sed -e 's/^eDP1 [a-z]* [0-9x+]* \(right\|left\|inverted\|\) \?(.*$/\1/')"
if [[ x"$xrandrout" == x"" ]]; then
  xrandrout=normal
fi

if [[ x"$1" == x"cycle" ]]; then
case $xrandrout in
 normal ) target=right;;
 right ) target=inverted;;
 inverted ) target=left;;
 left ) target=normal;;
esac
fi

if [[ x"$1" == x"countercycle" ]]; then
case $xrandrout in
 normal ) target=left;;
 right ) target=normal;;
 inverted ) target=right;;
 left ) target=inverted;;
esac
fi

if [[ x"$1" == x"reflect" ]]; then
case $xrandrout in
 normal ) target=inverted;;
 right ) target=left;;
 inverted ) target=normal;;
 left ) target=right;;
esac
fi

target=${target:-$1}

case $target in
 normal ) cal=( ${rangex[@]} ${rangey[@]} ); swap=0; invertx=0; inverty=0; pos=normal;;
 right ) cal=( ${rangex[@]} ${rangey[@]} ); swap=1; invertx=0; inverty=1; pos=right;;
 inverted ) cal=( ${rangex[@]} ${rangey[@]} ); swap=0; invertx=1; inverty=1; pos=inverted;;
 left ) cal=( ${rangex[@]} ${rangey[@]} ); swap=1; invertx=1; inverty=0; pos=left;;
esac

#xrandr -o $(( rotate * 3 ))
xrandr --output eDP1 --rotate $pos
for input in "${torotate[@]}"; do
 xinput set-prop "$input" "Evdev Axes Swap" $swap
 xinput set-prop "$input" "Evdev Axis Inversion" $invertx, $inverty
 xinput set-prop "$input" "Evdev Axis Calibration" ${cal[@]}
done
