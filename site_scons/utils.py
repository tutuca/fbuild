# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011 Esteban Papp, FuDePAN
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

def removeDuplicates(alist):
    if alist and isinstance(alist, list):
        alist.sort()
        last = alist[-1]
        for i in range(len(alist)-2, -1, -1):
            if last == alist[i]:
                del alist[i]
            else:
                last = alist[i]
    return alist

def recursive_flatten(env, path, fileFilter):
    out = []
    fileNodes = []
    if isinstance(fileFilter, list or tuple):
        for ff in fileFilter:
            fileNodes.extend(env.Glob(os.path.join(path, ff), strings=False))
    else:
        fileNodes.extend(env.Glob(os.path.join(path, fileFilter), strings=False))
    for f in fileNodes:
        out.append(f)
    dirNodes = env.Glob(os.path.join(path, '*'), strings=False)
    for n in dirNodes:
        if n.isdir():
            out.extend( recursive_flatten(env, n.abspath, fileFilter ))
    return out

def recursive_dir_flatten(env, path):
    out = []
    dirNodes = env.Glob(os.path.join(path, '*'), strings=False)
    for n in dirNodes:
        if n.isdir():
            out.append( n.abspath )
            out.extend( recursive_dir_flatten(env, n.abspath ))
    return out