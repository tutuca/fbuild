#!/bin/sh

# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011 Esteban Papp, Hugo Arregui FuDePAN
# 
# This file is part of the fudepan-build build system.
# 
# fudepan-build is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# fudepan-build is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with fudepan-build.  If not, see <http://www.gnu.org/licenses/>.

# Insert FuDePan boilerplate

# This file was written in shell scripting because we could not have python at this point
# After the first check that python is there, we jump to env.py to ensure we support as
# many platforms as we can. If another platform besides *nix is required, a different
# "shell env script" should be created.
# i.e. for windows a env.bat should be created.

if [ -z "${PYTHON_BIN_PATH+x}" ]; then
  export PYTHON_BIN_PATH=/usr/bin/python
fi

#hg pull -u

sh bin/init.sh

source bin/system.sh

if [ -e bin/local.sh ]; then
  source bin/local.sh
fi
