# fudepan-build: The build system for FuDePAN projects
#
# Copyright (C) 2011 Esteban Papp, Hugo Arregui, Alejandro Kondrasky,
#               2013 Gonzalo Bonigo, Gustavo Ojeda, FuDePAN
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


"""
    Add description here!
"""


import subprocess
import platform
import os.path
import shutil
import os

from SCons.Script import *
import SCons.Builder

from utils import findFiles
from utils import chain_calls
import utils


def init(env):
    bldRUT = Builder(action = SCons.Action.Action(RunUnittest, PrintDummy))
    env.Append(BUILDERS = {'RunUnittest' : bldRUT})
    #-
    bldInitLcov = Builder(action = SCons.Action.Action(InitLcov, PrintDummy))
    env.Append(BUILDERS = {'InitLcov' : bldInitLcov })
    #-
    bldRLcov= Builder(action = SCons.Action.Action(RunLcov, PrintDummy))
    env.Append(BUILDERS = {'RunLcov' : bldRLcov})
    #-
    bldDoxygen = Builder(action = SCons.Action.Action(RunDoxygen, PrintDummy))
    env.Append(BUILDERS = {'RunDoxygen' : bldDoxygen})
    env['DEFAULT_DOXYFILE'] = env.File('#/conf/doxygenTemplate').abspath
    #-
    bldAStyleCheck = Builder(action = SCons.Action.Action(AStyleCheck, PrintDummy))
    env.Append(BUILDERS = {'RunAStyleCheck' : bldAStyleCheck})
    #-
    bldAStyle = Builder(action = SCons.Action.Action(AStyle, PrintDummy))
    env.Append(BUILDERS = {'RunAStyle' : bldAStyle})
    #-
    bldPdfLatex = Builder(action = SCons.Action.Action(RunPdfLatex, PrintDummy))
    env.Append(BUILDERS = {'RunPdfLatex':  bldPdfLatex})
    env['PDFLATEX_OPTIONS'] = ''
    #-
    bldValgrind = Builder(action = SCons.Action.Action(RunValgrind, PrintDummy))
    env.Append(BUILDERS = {'RunValgrind':  bldValgrind})
    env['VALGRIND_OPTIONS'] = ' --leak-check=full --show-reachable=yes --error-limit=no '
    #-
    bldCCCC = Builder(action = SCons.Action.Action(RunCCCC, PrintDummy))
    env.Append(BUILDERS = {'RunCCCC':  bldCCCC})
    env['CCCC_OPTIONS'] = []
    #-
    bldCLOC = Builder(action = SCons.Action.Action(RunCLOC, PrintDummy))
    env.Append(BUILDERS = {'RunCLOC':  bldCLOC})
    env['CLOC_OUTPUT_FORMAT'] = 'txt' # txt | sql | xml
    env['CLOC_OPTIONS'] = []
    #-
    bldCppCheck = Builder(action = SCons.Action.Action(RunCppCheck, PrintDummy))
    env.Append(BUILDERS = {'RunCppCheck':bldCppCheck})
    env['CPPCHECK_OPTIONS'] = []


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
    test_executable = source[0].abspath
    indexFile = target[0].abspath
    data = {
            'coverage_file': os.path.join(os.path.dirname(os.path.dirname(indexFile)), 'coverage_output.dat'),
            'output_dir'   : env.Dir('INSTALL_METRICS_DIR'),
            'project_dir'  : env['PROJECT_DIR']
            }

    r = chain_calls(env, [
        'lcov --zerocounters --directory %(project_dir)s -b .' % data,
        'lcov --capture --initial --directory %(project_dir)s -b . --output-file %(coverage_file)s' % data,
        ])
    return r


def RunLcov(env, source, target):
    test_executable = source[0].abspath
    indexFile = target[0].abspath
    data = {
            'coverage_file': os.path.join(os.path.dirname(os.path.dirname(indexFile)), 'coverage_output.dat'),
            'output_dir'   : os.path.dirname(indexFile),
            'project_dir'  : env['PROJECT_DIR']
            }

    r = chain_calls(env, [
        'rm -f %(coverage_file)s' % data,
        'lcov --no-checksum --directory %(project_dir)s -b . --capture --output-file %(coverage_file)s' % data,
        'lcov --no-checksum --directory %(project_dir)s -b . --capture --output-file %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*usr/include*" -o %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*boost*" -o %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*gtest*" -o %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*gmock*" -o %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*install/*" -o %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*/tests/*" -o %(coverage_file)s' % data,
        'genhtml --highlight --legend --output-directory %(output_dir)s %(coverage_file)s' % data,
        ])
    if r == 0:
        env.cprint('lcov report in: %s' % indexFile, 'green')
    return r


def RunDoxygen(env, source, target):
    # Path to the doxygen template file.
    doxyTamplate = source[0].abspath
    # Path to the doc/project directory.
    target = target[0].abspath
    # Create the doc/project directory.
    os.mkdir(target)
    # Path to the project directory.
    projectDir,_ = os.path.split(source[1].abspath)
    # Path yo doxygen file for thise project.
    projectDoxyFile = projectDir + '/__tmp_doxyfile'
    # Copy the doxygen file template to the project directory.
    fsrc = open(doxyTamplate, 'r')
    doxygenSrc = fsrc.read()
    fsrc.close()
    targetName = os.path.basename(target)
    ftgt = open(projectDoxyFile, "w")
    ftgt.write(doxygenSrc.replace('$PROJECT_NAME', targetName)\
                         .replace('$OUTPUT_DIR', target))
    ftgt.flush()
    ftgt.close()
    # Create the command for the subprocess.call()
    cmdOutput = os.path.join(target,'doxyfile_generation.output')
    cmd = "cd %s; doxygen %s > %s" % (projectDir, projectDoxyFile, cmdOutput)
    rc = subprocess.call(cmd, shell=True)
    if env.GetOption('printresults'):
        subprocess.call("cat %s" % cmdOutput, shell=True)
    os.remove(projectDoxyFile)
    if rc:
        env.cerror('[failed] %s, error: %s' % (target, rc))
    else:
        env.cprint('[generated] %s' % target, 'green')
    return rc


def AStyleCheck(env, source, target):
    # We use the target as a temporary directory.
    targetDir = target[0]
    target = str(target[0].abspath)
    # If it doesn't exist we create it.
    if not os.path.exists(target):
        os.makedirs(target)
    for f in source:
        os.system('cp %s %s' % (f.abspath,target))
    # Get the list of copied files.
    files_lis = utils.findFiles(env,targetDir)
    files_str = ' '.join([x.abspath for x in files_lis])
    # Create the command for subprocess.call().
    cmd = 'astyle -k1 --options=none --convert-tabs -bSKpUH %s' % files_str
    # This variable holds if some file needs to be astyled.
    need_astyle = False
    # A list for the files that needs astyle.
    need_astyle_list = []
    # Apply astyle to those files.
    rc = subprocess.call(cmd, shell=True, stdout=subprocess.PIPE)
    if rc != 0:
        return rc
    # Check if astyle did some modifications.
    for f in files_lis:
        # If the '.orig' file exists for the file 'f' then it was modify for 
        # astyle.
        if os.path.exists('%s.orig' % f.abspath):
            # Print the differences between files.
            cmd = 'diff -Nau %s.orig %s' % (f.abspath,f.abspath)
            diff = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            diff_stdout = diff.stdout.read()
            diff.wait()
            need_astyle_list.append((os.path.split(f.abspath)[1],diff_stdout))
            need_astyle = True
    # Remove the '*.orig' files.
    os.system('rm -rf %s/*.orig' % target)
    # Print info.
    if need_astyle:
        env.cprint('[ERROR] The following files need astyle:', 'red')
        for f,info in need_astyle_list:
            env.cprint('====> %s' % f, 'red')
            env.cprint(info,'yellow')
    else:
        env.cprint('[OK] No file needs astyle.', 'green')


def AStyle(env, source, target):
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


def RunPdfLatex(env, source, target):
    #Deberiamos usar las env.{operation} ya que son crossplatform.
    (pathHead, pathTail) = os.path.split(source[0].abspath)
    tmpPdf2TexDir = pathHead + '/tmp_Pdf2Texfile/'
    if not os.path.exists(tmpPdf2TexDir):
        #env.Execute(env.Mkdir(tmpPdf2TexDir))
        os.mkdir(tmpPdf2TexDir)
    targetDir = os.path.split(target[0].abspath)[0]
    if not os.path.exists(targetDir):
        #env.Execute(env.Mkdir(targetDir))
        os.mkdir(targetDir)
    rt = subprocess.call('cd ' + pathHead + ' ; pdflatex ' + env['PDFLATEX_OPTIONS']
        + ' -output-directory "' + tmpPdf2TexDir + '" ' + pathTail, shell=True)
    shutil.move(targetDir, tmpPdf2TexDir + pathTail[:-4] + ".pdf")
    shutil.rmtree(tmpPdf2TexDir)
    return rt
    #env.Execute(env.Move(targetDir, tmpPdf2TexDir + pathTail[:-4] +".pdf"))
    #env.Execute(env.Delete(tmpPdf2TexDir))


def RunValgrind(env, source, target):
    cwd = env.Dir('#').abspath
    test_dir = source[0].dir.abspath
    os.chdir(test_dir)
    cmd = 'valgrind %s %s' % (env['VALGRIND_OPTIONS'], source[0].abspath)
    ret_val = subprocess.call(cmd, shell=True)
    os.chdir(cwd)
    return ret_val


def RunCCCC(env, source, target):
    env.cprint('Running cccc...', 'green')
    target = target[0].abspath
    # It tells to cccc the name of the directory that will contain the result.
    env.Append(CCCC_OPTIONS = '--outdir=%s' % target)
    # Check if the install directory for the cccc results already exists.
    if not os.path.exists(target):
        os.makedirs(target)
    # From the env['CCCC_OPTIONS'] we create a string with the options for cccc.
    options = ' '.join([opt for opt in env['CCCC_OPTIONS']])
    # From the 'source' we create a string with the file names for cccc.
    files = ' '.join([f.abspath for f in source])
    # Create the command to be pass to subprocess.call()
    cmd = 'cccc %s %s' % (options, files)
    ret_val = subprocess.call(cmd, shell=True)
    return ret_val


def RunCLOC(env, source, target):
    env.cprint('Running cloc...', 'green')
    target = target[0].abspath
    # Check if the install directory for the cloc results already exists.
    if not os.path.exists(target):
        os.makedirs(target)
    # From the env['CLOC_OPTIONS'] we create a string with the options for cloc.
    options = ' '.join([opt for opt in env['CLOC_OPTIONS']])
    # From the 'source' we create a string with the file names for cloc.
    files = ' '.join([f.abspath for f in source])
    # Create the command to be pass to subprocess.call()
    cmd = 'cloc %s %s' % (options, files)
    return subprocess.call(cmd, shell=True)


def RunCppCheck(env, source, target):
    env.cprint('Running cppcheck...', 'green')
    target = target[0].abspath
    # Check if the install directory for the cppcheck results already exists.
    if not os.path.exists(target):
        os.makedirs(target)
    # We create a string with the options for cppcheck.
    options = ' '.join([opt for opt in env['CPPCHECK_OPTIONS']])
    # We create a string with the files for cppcheck.
    files = ' '.join([f.abspath for f in source])
    # Set the name of the report file.
    outfile = "%s/CppCheckReport.txt" % target
    # Create the command to be pass to subprocess.call()
    cmd = 'cppcheck %s %s > %s' % (options, files, outfile)
    return subprocess.call(cmd, shell=True)
