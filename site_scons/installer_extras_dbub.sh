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

# This file provides differents installer implementation for Debian/Ubuntu systems.

TMP_DIR="_tmp_download/"

function check_build_essential {
    if [ ! "$(dpkg -s build-essential | grep -e 'Status: install ok installed')" ]; then
        echo -e "\e[0;33m[warn] A problem with 'build-essential' had been found.\e[0m"
        echo "info: 'sudo apt-get install build-essential' should solve this, do you want"
        echo "       me to do it? (your password could be required)"
        
        REPLY="extremelyLongStringUnlikelyToBeUsed"
        
        while [[ "$REPLY" != "y" && "$REPLY" != "n" && "$REPLY" != "" ]]; do
            read -p "Install ([y]/n)?" REPLY
            if [[ "$REPLY" != "y" && "$REPLY" != "n" && "$REPLY" != "" ]]; then
                echo -e "\e[0;31mID-10-T Error: please insert 'y' or 'n' or nothing. \e[0m"
            fi
        done
        if [[ "$REPLY" = "y" || "$REPLY" = "" ]]; then
            sudo apt-get install build-essential
            if [ "$?" -ne "0" ]; then
                echo -e "\e[0;31m[error] 'build-essential' it is required and could not be installed, exiting\e[0m"
                return 1
            fi
        else
            echo -e "\e[0;31m[error] 'build-essential' required, exiting\e[0m"
            return 1
        fi
    fi
    return 0
}
function install_namecheck {
    NAMECHECK='/usr/lib/libnamecheck.so'
    OLDPWD=`pwd` 
    TEMPDIR='/tmp/namecheck'
    if [ ! -f "$NAMECHECK" ]; then
        if [ -n `dpkg -l | grep libboost-regex-dev -c` ]; then 
            echo "Installing boost-regex headers for gcc version 4.6"
            sudo apt-get install libboost-regex-dev
        fi
        if [ -n `q ` ]; then
            #determine the gcc version:
            if [ -n `gcc --version | head -n 1| grep 4.6 -c` ]; then
                echo "Installing gcc plugins headers for gcc version 4.6"
                sudo apt-get install gcc-4.6-plugin-dev
            elif [ `gcc --version | head -n 1| grep 4.7 -c` ]; then
                echo "Installing gcc plugins headers for gcc version 4.7"
                sudo apt-get install gcc-4.7-plugin-dev
            else
                echo -e "\e[0;31m[error] gcc version not supported.\e[0m"
                echo -e "\e[0;31m[error] Install gcc-plugin-dev package manually.\e[0m"
                exit 1
            fi
        fi
        if !(dpkg -l | grep gettext -c >>/dev/null); then 
            sudo apt-get install gettext
        fi
        echo -e "\e[0;33mInstalling Namecheck GCC Plugin\e[0m"
        if [ ! -d "$TEMPDIR" ]; then
            mkdir $TEMPDIR
        fi
        cd $TEMPDIR
        wget http://web20.tallertechnologies.com/sites/all/modules/pubdlcnt/pubdlcnt.php?file=/sites/default/files/namecheck-1.2.tar.gz -O namecheck.tar.gz
        tar xf namecheck.tar.gz
        make
        sudo mv libnamecheck.so /usr/lib/
        cd $OLDPWD
    fi
}
function check_astyle_2_03 {
    ASTYLE_URL="http://downloads.sourceforge.net/project/astyle/astyle/astyle%202.03/astyle_2.03_linux.tar.gz?r=&ts=1373513007&use_mirror=ufpr"
    ASTYLE_TAR="astyle_2_03.tar.gz"
    ASTYLE_PATH_INSTALL="astyle/build/gcc"
    
    if [[ ! "$(which astyle)" || "$(echo $(astyle -V 2>&1 | cut -f4 -d' ') '< 2.03' | bc -l)" != 0 ]]; then
        echo -e "\e[0;33m[warn] AStyle version should be at least 2.03\e[0m"
        echo "info: Do you want me to install it? (your password could be required)"
            
        REPLY="extremelyLongStringUnlikelyToBeUsed"
        while [[ "$REPLY" != "y" && "$REPLY" != "n" && "$REPLY" != "" ]]; do
            read -p "Install ([y]/n)?" REPLY
            if [[ "$REPLY" != "y" && "$REPLY" != "n" && "$REPLY" != "" ]]; then
                echo -e "\e[0;31mID-10-T Error: please insert 'y' or 'n' or nothing. \e[0m"
            fi
        done
        if [[ "$REPLY" = "y" || "$REPLY" = "" ]]; then
            wget -O $ASTYLE_TAR $ASTYLE_URL
            if [ "$?" -ne "0" ]; then
                echo -e "\e[0;31m[error] 'astyle 2.03' could not be downloaded\e[0m"
                return 1
            fi
            tar -xvzf $ASTYLE_TAR >& /dev/null
            if [ "$?" -ne "0" ]; then
                echo -e "\e[0;31m[error] 'astyle 2.03' could not be extracted\e[0m"
                return 1
            fi
            rm -rf $ASTYLE_TAR
            pushd $ASTYLE_PATH_INSTALL >& /dev/null
            make release  >& /dev/null
            if [ "$?" -ne "0" ]; then
                echo -e "\e[0;31m[error] 'astyle 2.03' could not be installed\e[0m"
                return 1
            fi
            echo -e "\e[0;32m[Installing] Installing in /usr/bin/astyle \e[0m"
            sudo cp bin/astyle /usr/bin/astyle
            popd >& /dev/null

            rm -rf astyle*
        else
            echo -e "\e[0;31m[error] 'astyle' it is required and could not be installed, exiting\e[0m"
            return 1
        fi
    fi
}
