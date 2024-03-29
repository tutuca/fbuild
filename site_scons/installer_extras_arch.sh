#!/bin/bash

# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011-2012 Esteban Papp, Hugo Arregui,
#               2013 Gonzalo Bonigo, Gustavo Ojeda, Matias Iturburu,
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

# This file provides differents installer implementation for Arch systems.

TMP_DIR="_tmp_downloads/"
function check_build_essential {
    if [ ! "$(pacman -Q -s base-devel | grep -e 'The GNU Compiler Collection - C and C++ frontends')" ]; then
        echo -e "\e[0;33m[warn] A problem with 'base-devel' had been found.\e[0m"
        echo "info: 'pacman -S base-devel' should solve this, do you want"
        echo "       me to do it? (your password could be required)"
        
        REPLY="Null"
        
        while [[ "$REPLY" != "y" && "$REPLY" != "n" && "$REPLY" != "" ]]; do
            read -p "Install ([y]/n)?" REPLY
            if [[ "$REPLY" != "y" && "$REPLY" != "n" && "$REPLY" != "" ]]; then
                echo -e "\e[0;31mID-10-T Error: please insert 'y' or 'n' or nothing. \e[0m"
            fi
        done
        if [[ "$REPLY" = "y" || "$REPLY" = "" ]]; then
            pacman -S base-devel
            if [ "$?" -ne "0" ]; then
                echo -e "\e[0;31m[error] 'base-devel' it is required and could not be installed, exiting\e[0m"
                return 1
            fi
        else
            echo -e "\e[0;31m[error] 'base-devel' required, exiting\e[0m"
            return 1
        fi
    fi
    return 0
}

function check_astyle_2_03 {
    ASTYLE_URL="http://downloads.sourceforge.net/project/astyle/astyle/astyle%202.03/astyle_2.03_linux.tar.gz?r=&ts=1373513007&use_mirror=ufpr"
    ASTYLE_TAR="astyle_2_03.tar.gz"
    ASTYLE_PATH_INSTALL="astyle/build/gcc"
    
    if [[ ! "$(which astyle)" || "$(echo $(astyle -V 2>&1 | cut -f4 -d' ') '< 2.03' | bc -l)" != 0 ]]; then
        echo -e "\e[0;33m[Warning] AStyle version should be at least 2.03\e[0m"
        echo "info: Do you want me to install it? (your password could be required)"
            
        REPLY="extremelyLongStringUnlikelyToBeUsed"
        while [[ "$REPLY" != "y" && "$REPLY" != "n" && "$REPLY" != "" ]]; do
            read -p "Install (y/[n])?" REPLY
            if [[ "$REPLY" != "y" && "$REPLY" != "n" && "$REPLY" != "" ]]; then
                echo -e "\e[0;31mID-10-T Error: please insert 'y' or 'n' or nothing. \e[0m"
            fi
        done
        if [ "$REPLY" = "y" ]; then
            if [[ ! "$(ls $TMP_DIR)" ]]; then
                mkdir $TMP_DIR
            fi
            wget -O $TMP_DIR$ASTYLE_TAR $ASTYLE_URL
            if [ "$?" -ne "0" ]; then
                echo -e "\e[0;31m[error] 'astyle 2.03' could not be downloaded\e[0m"
                return 1
            fi
            pushd $TMP_DIR >& /dev/null
            tar -xvzf $ASTYLE_TAR >& /dev/null
            if [ "$?" -ne "0" ]; then
                echo -e "\e[0;31m[error] 'astyle 2.03' could not be extracted\e[0m"
                popd >& /dev/null
                rm -rf $TMP_DIR
                return 1
            fi
            rm -rf $ASTYLE_TAR
            pushd $ASTYLE_PATH_INSTALL >& /dev/null
            make release  >& /dev/null
            if [ "$?" -ne "0" ]; then
                echo -e "\e[0;31m[error] 'astyle 2.03' could not be installed\e[0m"
                popd >& /dev/null
                popd >& /dev/null
                rm -rf $TMP_DIR
                return 1
            fi
            echo -e "\e[0;32m[Installing] Installing in /usr/bin/astyle \e[0m"
            sudo cp bin/astyle /usr/bin/astyle
            popd >& /dev/null
            popd >& /dev/null
            rm -rf $TMP_DIR
        else
            echo -e "\e[0;31m[error] 'astyle' it is required and could not be installed, exiting\e[0m"
            return 1
        fi
    fi
}
