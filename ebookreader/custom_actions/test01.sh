#!/usr/bin/bash

# ret=`curl dict://dict.org/d:"$@"`

ret=`wn "$@" -over`
echo "$ret"

echo "$ret" | yad --text-info --wrap --width=600 --height=600 &