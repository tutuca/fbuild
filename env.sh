#!/bin/sh
# Insert FuDePan boilerplate

# This file was written in shell scripting because we could not have python at this point
# After the first check that python is there, we jump to env.py to ensure we support as
# many platforms as we can. If another platform besides *nix is required, a different
# "shell env script" should be created.
# i.e. for windows a env.bat should be created.

sh init.sh

# jump to env.py
python env.py

