#!/bin/bash

# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2013 Gonzalo Bonigo, FuDePAN
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

# This file was written in shell scripting because we do not have python at 
# this point.
# After the first check that python is there, we jump to a python environment 
# to ensure we support as many platforms as we can. If another platform 
# besides *nix is required, a different "shell env script" should be created. 
# i.e. for windows a env.bat should be created.

# Please try not to much too much logic here, we should maintain this file 
# as simple as possible.

# Detect internet connectivity
if [ -z "$(ip r | grep default | cut -d ' ' -f 3)" ]; then
    internet_connection="error"
else
    echo ping -q -w 1 -c 1 `ip r | grep default | cut -d ' ' -f 3` > /dev/null && internet_connection="ok" || internet_connection="error"
fi

# Update the fudepan environment
if [[ "$(which hg)" && -z $FBUILD_NO_UPDATE ]]; then
    if [ $internet_connection = "ok" ]; then
        echo -e "\e[0;35mChecking for updates in the environment\e[0m"
        hg pull -u
        source env.sh
    else
        echo -e "\e[0;33m[warn] FuDePan environment not updated since there is no internet connection\e[0m"
    fi
fi
