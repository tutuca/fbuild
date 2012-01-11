# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011 Alejandro Kondrasky FuDePAN
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

import os.path
import shutil
import subprocess

def runPdfLatex(target, source, env):
    (pathHead, pathTail) = os.path.split(source[0].abspath)
    
    tmpPdf2TexDir = pathHead + '/tmp_Pdf2Texfile/'
    if not os.path.exists(tmpPdf2TexDir):
        os.makedirs(tmpPdf2TexDir)

    targetName = os.path.basename(target[0].abspath)[:-4]
    targetDir = env['INSTALL_DOC_DIR'] + '/' + targetName +'/pdf/'
    if not os.path.exists(targetDir):
        os.makedirs(targetDir)
    
    subprocess.call('cd ' + pathHead + ' ; pdflatex ' + env['PDFLATEX_OPTIONS'] + 
        ' -output-directory "' + tmpPdf2TexDir + '" ' + pathTail, shell=True)
    shutil.copy2(tmpPdf2TexDir + pathTail[:-4] +".pdf", targetDir)
    shutil.rmtree(tmpPdf2TexDir, ignore_errors=True)
