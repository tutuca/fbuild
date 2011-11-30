# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011 Esteban Papp FuDePAN
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
import os.path
import subprocess

def runDoxygen(target, source, env):
    (pathHead, pathTail) = os.path.split(source[0].abspath)
    if pathTail == 'SConscript':
        fsrc = open(os.path.abspath(env['DEFAULT_DOXYFILE']), 'r')
        doxygenSrc = fsrc.read()
        fsrc.close()
    else:
        fsrc = open(source[0].abspath, 'r')
        doxygenSrc = fsrc.read()
        fsrc.close()
    
    tmpdoxyFile = pathHead + '/tmp_doxyfile'
    targetName = os.path.basename(target[0].abspath)[:-4]
    targetDir = env['INSTALL_DOC_DIR'] + '/' + targetName
    
    ftgt = open(tmpdoxyFile, "w")
    ftgt.write(doxygenSrc.replace('$PROJECT_NAME', targetName)\
                         .replace('$OUTPUT_DIR', targetDir))
    ftgt.flush()
    ftgt.close()
    subprocess.call('cd ' + pathHead + ' ; doxygen ' + tmpdoxyFile, shell=True)
    os.remove(tmpdoxyFile)

