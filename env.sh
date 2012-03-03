#!/bin/bash

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

# This file was written in shell scripting because we do not have python at 
# this point.
# After the first check that python is there, we jump to a python environment 
# to ensure we support as many platforms as we can. If another platform 
# besides *nix is required, a different "shell env script" should be created. 
# i.e. for windows a env.bat should be created.

# Please try not to much too much logic here, we should maintain this file 
# as simple as possible

# Update the fudepan environment
if [ "$(which hg)" ]; then
    echo -e "\e[0;35mChecking for updates in the environment\e[0m"
    hg pull -u
fi

# Install section: this section install all the pre-requisites of the 
# environment. If other installers are supported they should maintain the
# function interface
if [ "$(which apt-get)" ]; then
    source ./site_scons/installer_aptget.sh
fi

# three parameters: 
# 1) binary to check for existance
# 2) package to install
# 3) required?
check_install make build-essential true
if [ "$?" -ne "0" ]; then return $?; fi
check_install python python true
if [ "$?" -ne "0" ]; then return $?; fi
check_install scons scons true
if [ "$?" -ne "0" ]; then return $?; fi
check_install moc qt4-dev-tools
if [ "$?" -ne "0" ]; then return $?; fi
check_install doxygen doxygen
if [ "$?" -ne "0" ]; then return $?; fi
check_install dot graphviz
if [ "$?" -ne "0" ]; then return $?; fi
check_install astyle astyle true 

if [ "$(astyle -V 2>&1 | cut -f4 -d' ' | bc | sed 's/\.//')" -lt "124" ]; then
    echo -e "\e[0;31m[error] AStyle version should be >= 1.24\e[0m"
    return 1
fi

# Backward compatibility
alias fbuild=scons

echo -e "\e[0;32mWelcome to the FuDePAN console environment\e[0m"
return 0
