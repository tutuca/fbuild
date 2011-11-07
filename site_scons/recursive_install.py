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

# based on: http://xtargets.com/2010/04/21/recursive-install-builder-for-scons/

import os

def recursive_install(env, path ):
    nodes = env.Glob(os.path.join(path, '*'), strings=False)
    nodes.extend(env.Glob(os.path.join(path, '*.*'), strings=False))
    out = []
    for n in nodes:
        if n.isdir():
            out.extend( recursive_install(env, n.abspath ))
        else:
            out.append(n)

    return out

def RecursiveInstall(env, target, dir):
    nodes = recursive_install(env, dir)

    dir = os.path.split(env.Dir(dir).abspath)[0]
    target = env.Dir(target).abspath

    l = len(dir) + 1
    relnodes = [ n.abspath[l:] for n in nodes ]

    for n in relnodes:
        t = os.path.join(target, n)
        s = os.path.join(dir, n)
        env.Alias('install', env.InstallAs(env.File(t), env.File(s)))
