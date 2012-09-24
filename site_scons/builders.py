# fudepan-build: The build system for FuDePAN projects
#
# Copyright (C) 2011 Esteban Papp, Hugo Arregui, Alejandro Kondrasky FuDePAN
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

#from SCons.Script.SConscript import SConsEnvironment
from SCons.Script import *
import SCons.Builder
import platform
import shutil
import subprocess
import utils
import os
from utils import findFiles, chain_calls

def init(env):
    from SCons.Script import Builder

    bldRUT = Builder(action = SCons.Action.Action(RunUnittest, PrintDummy))
    env.Append(BUILDERS = {'RunUnittest' : bldRUT})

    bldInitLcov = Builder(action = SCons.Action.Action(InitLcov, PrintDummy))
    env.Append(BUILDERS = {'InitLcov' : bldInitLcov })

    bldRLcov= Builder(action = SCons.Action.Action(RunLcov, PrintDummy))
    env.Append(BUILDERS = {'RunLcov' : bldRLcov})

    bldDoxygen = Builder(action = SCons.Action.Action(RunDoxygen, PrintDummy))
    env.Append(BUILDERS = {'RunDoxygen' : bldDoxygen})
    env['DEFAULT_DOXYFILE'] = env.File('#/conf/doxygenTemplate').abspath

    bldAStyle = Builder(action = SCons.Action.Action(AStyle, PrintDummy))
    env.Append(BUILDERS = {'RunAStyle' : bldAStyle})

    env.Tool('makebuilder')
    makeBuilder = Builder(action = SCons.Action.Action(MakeTool, PrintDummy))
    env.Append(BUILDERS = {'RunMakeTool' : makeBuilder})

    bldPdfLatex = Builder(action = SCons.Action.Action(RunPdfLatex, PrintDummy))
    env.Append(BUILDERS = {'RunPdfLatex':  bldPdfLatex})
    env['PDFLATEX_OPTIONS'] = ''

    bldValgrind = Builder(action = SCons.Action.Action(RunValgrind, PrintDummy))
    env.Append(BUILDERS = {'RunValgrind':  bldValgrind})
    env['VALGRIND_OPTIONS'] = ''

def PrintDummy(env, source, target):
    return ""

def RunUnittest(env, source, target):
    rc = 0
    tindex = 0
    for s in source:
        t = target[tindex].abspath;
        app = s.abspath
        (dir, appbin) = os.path.split(app)
        cmd = "cd %s; ./%s > %s" % (dir, appbin, t)
        rc = subprocess.call(cmd, shell=True)
        if env.GetOption('printresults'):
            subprocess.call("cat %s" % t, shell=True)
        if rc:
            env.cerror('[failed] %s, error: %s' % (t, rc))
        else:
            env.cprint('[passed] %s' % t, 'green')
        tindex = tindex + 1
    return rc

def InitLcov(env, source, target):
    from os.path import dirname, join
    test_executable = source[0].abspath
    indexFile = target[0].abspath
    data = {
            'coverage_file': join(dirname(dirname(indexFile)), 'coverage_output.dat'),
            'output_dir'   : dirname(indexFile)
            }

    r = chain_calls(env, [
        'lcov --zerocounters --directory . -b .',
        'lcov --capture --initial --directory . -b . --output-file %(coverage_file)s' % data,
        ])
    return r

def RunLcov(env, source, target):
    from os.path import dirname, join
    test_executable = source[0].abspath
    indexFile = target[0].abspath
    data = {
            'coverage_file': join(dirname(dirname(indexFile)), 'coverage_output.dat'),
            'output_dir'   : dirname(indexFile)
            }

    r = chain_calls(env, [
        'lcov --no-checksum --directory . -b . --capture --output-file %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*usr/include*" -o %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*gtest*" -o %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*gmock*" -o %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*install/*" -o %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*/tests/*" -o %(coverage_file)s' % data,
        'genhtml --highlight --legend --output-directory %(output_dir)s %(coverage_file)s' % data,
        ])
    if r == 0:
        env.cprint('lcov report in: %s' % indexFile, 'green')
    return r

def RunDoxygen(target, source, env):
    rc = 0
    tindex = 0
    for s in source:
        t = target[tindex].abspath;
        os.mkdir(t)
        (pathHead, pathTail) = os.path.split(s.abspath)

        fsrc = open(source[0].abspath, 'r')
        doxygenSrc = fsrc.read()
        fsrc.close()

        tmpdoxyFile = pathHead + '/__tmp_doxyfile'
        targetName = os.path.basename(t)[:-4]

        ftgt = open(tmpdoxyFile, "w")
        ftgt.write(doxygenSrc.replace('$PROJECT_NAME', targetName)\
                             .replace('$OUTPUT_DIR', t))
        ftgt.flush()
        ftgt.close()
        cmdOutput = os.path.join(t,'doxyfile_generation.output')
        cmd = "cd %s; doxygen %s > %s" % (pathHead, tmpdoxyFile, cmdOutput)
        rc = subprocess.call(cmd, shell=True)
        if env.GetOption('printresults'):
            subprocess.call("cat %s" % cmdOutput, shell=True)
        os.remove(tmpdoxyFile)
        if rc:
            env.cerror('[failed] %s, error: %s' % (t, rc))
        else:
            env.cprint('[generated] %s' % t, 'green')
        tindex = tindex + 1
    return rc

def MakeTool(target, source, env):
    s = source[0].abspath;
    (pathHead, pathTail) = os.path.split(s)
    configureOpts = ('--bindir=%(INSTALL_BIN_DIR)s --libdir=%(INSTALL_LIB_DIR)s --includedir=%(INSTALL_HEADERS_DIR)s' % env)
    procEnv = os.environ
    (arch,binType) = platform.architecture()
    if arch == '64bit':
        procEnv["CXXFLAGS"] = str(env["CXXFLAGS"])
        procEnv["CFLAGS"] = '-fPIC'
    return subprocess.call('./configure %s ; make; make install' % configureOpts, cwd=pathHead, shell=True, env=procEnv)

def AStyle(target, source, env):
    rc = 0
    t = target[0].abspath
    cmd = "astyle -k1 --options=none --convert-tabs -bSKpUH %s"
    fileList = ' '.join(s.abspath for s in source)
    rc = subprocess.call(cmd % fileList, shell=True)
    if rc:
        env.cerror('[error] %s, error: %s' % (t, rc))
    else:
        env.cprint('[astyle] %s' % t, 'green')
    return rc

def RunPdfLatex(target, source, env):
    #Deberiamos usar las env.{operation} ya que son crossplatform.
    (pathHead, pathTail) = os.path.split(source[0].abspath)

    tmpPdf2TexDir = pathHead + '/tmp_Pdf2Texfile/'
    if not os.path.exists(tmpPdf2TexDir):
#        env.Execute(env.Mkdir(tmpPdf2TexDir))
        os.mkdir(tmpPdf2TexDir)

    targetDir = os.path.split(target[0].abspath)[0]
    if not os.path.exists(targetDir):
#        env.Execute(env.Mkdir(targetDir))
        os.mkdir(targetDir)

    rt = subprocess.call('cd ' + pathHead + ' ; pdflatex ' + env['PDFLATEX_OPTIONS']
        + ' -output-directory "' + tmpPdf2TexDir + '" ' + pathTail, shell=True)
    shutil.move(targetDir, tmpPdf2TexDir + pathTail[:-4] + ".pdf")
    shutil.rmtree(tmpPdf2TexDir)
    return rt
#    env.Execute(env.Move(targetDir, tmpPdf2TexDir + pathTail[:-4] +".pdf"))
#    env.Execute(env.Delete(tmpPdf2TexDir))

def RunValgrind(target, source, env):

    return subprocess.call(
        'valgrind ' + env['VALGRIND_OPTIONS']
        + '--leak-check=full --show-reachable=yes --error-limit=no ' +
        source[0].abspath + ' > ' + source[0].abspath.split(":")[0] + '.txt', shell=True)
