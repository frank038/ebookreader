#!/bin/bash

thisdir=$(dirname "$0")
cd $thisdir

python3 ebookreader.py "$1"

cd $HOME
