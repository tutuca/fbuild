#!/bin/bash

# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011-2012 Esteban Papp, Hugo Arregui,
#               2013 Gonzalo Bonigo, Gustavo Ojeda, Matías Iturburu,
#                    Leandro Moreno, FuDePAN
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

# Install section: this section install all the pre-requisites of the 
# environment. If other installers are supported they should maintain the
# function interface

if [ "$FBUILD_ENV_STARTED" != "true" ]; then
    echo -e "\e[0;31m[error] Use 'source start.sh' instead of 'source env.sh'\e[0m";
    return 1
else
    export FBUILD_ENV_STARTED=false
fi

if [ "$(which apt-get 2>/dev/null)" ]; then
    source ./site_scons/installer_aptget.sh
    source ./site_scons/installer_extras_dbub.sh
elif [ "$(which packer)" ]; then
    source ./site_scons/installer_packer.sh
    source ./site_scons/installer_extras_dbub.sh
else
    function check_install {
        if [ "$3" ]; then     
           echo -e "\e[0;31m[error] $2 not found, need to install it to continue\e[0m"
        fi
    }
fi
# We need to check if build essential is installed
check_build_essential
if [ "$?" -ne "0" ]; then return $?; fi
# three parameters: 
# 1) binary to check for existance
# 2) required?
check_install make true
if [ "$?" -ne "0" ]; then return $?; fi
check_install python true
if [ "$?" -ne "0" ]; then return $?; fi
check_install scons true
if [ "$?" -ne "0" ]; then return $?; fi
check_install g++ true
if [ "$?" -ne "0" ]; then return $?; fi
check_install moc
if [ "$?" -ne "0" ]; then return $?; fi
check_install doxygen
if [ "$?" -ne "0" ]; then return $?; fi
check_install dot
if [ "$?" -ne "0" ]; then return $?; fi
check_astyle_2_03
if [ "$?" -ne "0" ]; then return $?; fi
check_install svn true 
if [ "$?" -ne "0" ]; then return $?; fi
check_install wget true 
if [ "$?" -ne "0" ]; then return $?; fi
check_install cccc false
if [ "$?" -ne "0" ]; then return $?; fi
check_install cloc false
if [ "$?" -ne "0" ]; then return $?; fi
check_install valgrind true
if [ "$?" -ne "0" ]; then return $?; fi
check_install cppcheck false
if [ "$?" -ne "0" ]; then return $?; fi
check_install lcov false
if [ "$?" -ne "0" ]; then return $?; fi
check_install clang false
if [ "$?" -ne "0" ]; then return $?; fi


# Backward compatibility
alias fbuild=scons

echo -e "FuDePAN-build 2.0"
echo -e "Copyright (C) 2011-2012 Esteban Papp and Hugo Arregui, 2013 Gonzalo Bonigo and Gustavo Ojeda, FuDePAN"
echo -e "This program comes with ABSOLUTELY NO WARRANTY; for details see http://www.gnu.org/licenses/gpl-3.0.html"
echo -e "FuDePAN-build is free software, and you are welcome to redistribute it under certain conditions; for more information visit http://www.gnu.org/licenses/gpl-3.0.html\n"

echo -e "\e[0;32mWelcome to the FuDePAN console environment\e[0m"

return 0
