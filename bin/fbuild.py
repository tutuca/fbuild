# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011 Hugo Arregui FuDePAN
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

import os
import sys

BUILD_SCRIPTS_DIR = os.path.join(os.getcwd(), "scons/site_scons")
sys.path.append(BUILD_SCRIPTS_DIR)

import argparse
from subprocess import call

def invoke_scons(args):
    cmd = 'cd scons; scons ' + ' '.join(args)
    print cmd
    call(cmd, shell=True)

def parse_arg(arg):
    splitted = arg.split(':')
    return (arg, splitted[0], splitted[1] if len(splitted) > 1 else None)

parser = argparse.ArgumentParser(description="invokes the fudepan-build system")
parser.add_argument('-c', dest='commands', help="clear", action='append_const', const='clear')
parser.add_argument('project', nargs='*', help="use project[:task]")
args = parser.parse_args()

scons_args = []
for command in args.commands:
    if command == 'clear':
        scons_args.append('-c')

scons_targets = []
for arg in args.project:
    original, project, task = parse_arg(arg)
    scons_targets.append(original)

invoke_scons(scons_args + scons_targets)

##from dependencies import dependency
#import dependencies
