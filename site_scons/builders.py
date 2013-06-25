# fudepan-build: The build system for FuDePAN projects
#
# Copyright (C) 2011 Esteban Papp, Hugo Arregui, Alejandro Kondrasky,
#               2013 Gonzalo Bonigo, Gustavo Ojeda, FuDePAN.
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

from utils import FindFiles
from utils import ChainCalls
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
    env['VALGRIND_OPTIONS'] = ' --leak-check=full --show-reachable=yes ' + \
                              '--error-limit=no --track-origins=yes'
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
    env['CPPCHECK_OPTIONS'] = [' --enable=all ']
    #-
    bldMocko = Builder(action = SCons.Action.Action(RunMocko, PrintDummy))
    env.Append(BUILDERS = {'RunMocko':bldMocko})
    #-
    bldReadyToCommit = Builder(action = SCons.Action.Action(RunReadyToCommit, PrintDummy))
    env.Append(BUILDERS = {'RunReadyToCommit':bldReadyToCommit})


def PrintDummy(env, target, source):
    return ""


def RunUnittest(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running TESTS ===\n', 'green')
    rc = 0
    tindex = 0
    for s in source:
        t = target[tindex].abspath
        app = s.abspath
        (dir, appbin) = os.path.split(app)
        # Check if the builder was called for jenkins or ready to commit.
        tmp = target[tindex].abspath.split('.')[0]
        testsuite = env.GetOption('testsuite')
        os.environ['GTEST_OUTPUT'] = env.test_report
        if env.USE_MOCKO:
            cmd = "cd %s; gdb -x mocko_bind.gdb %s > %s" % (dir, appbin, t)
        else:
            cmd = "cd %s; ./%s --gtest_filter=%s > %s" % (dir, appbin, testsuite, t)
        rc = subprocess.call(cmd, shell=True)
        if env.GetOption('printresults'):
            subprocess.call("cat %s" % t, shell=True)
        if rc:
            env.cerror('[failed] %s, error: %s' % (t, rc))
        else:
            env.Cprint('[passed] %s' % t, 'green')
        tindex = tindex + 1
    return 0


def InitLcov(env, target, source):
    test_executable = source[0].abspath
    indexFile = target[0].abspath
    silent = env.GetOption('verbose')
    data = {
        'coverage_file': os.path.join(os.path.dirname(os.path.dirname(indexFile)), 'coverage_output.dat'),
        'output_dir'   : env.Dir('INSTALL_METRICS_DIR'),
        'project_dir'  : env['PROJECT_DIR']
    }
    r = ChainCalls(env, [
        'lcov --zerocounters --directory %(project_dir)s -b .' % data,
        'lcov --capture --initial --directory %(project_dir)s -b . --output-file %(coverage_file)s' % data,
    ], silent)
    return r


def RunLcov(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running COVERAGE ===\n', 'green')
    test_executable = source[0].abspath
    indexFile = target[0].abspath
    data = {
        'coverage_file': os.path.join(os.path.dirname(os.path.dirname(indexFile)), 'coverage_output.dat'),
        'output_dir'   : os.path.dirname(indexFile),
        'project_dir'  : env['PROJECT_DIR']
    }
    commands_list = [
        'rm -f %(coverage_file)s' % data,
        'lcov --no-checksum --directory %(project_dir)s -b . --capture --output-file %(coverage_file)s' % data,
        'lcov --no-checksum --directory %(project_dir)s -b . --capture --output-file %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*/tests/*" -o %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*usr/include*" -o %(coverage_file)s' % data
    ]
    for dep in env['PROJECT_DEPS']:
        data['project_dep'] = dep
        cmd = 'lcov --remove %(coverage_file)s "*%(project_dep)s*" -o %(coverage_file)s' % data
        commands_list.append(cmd)
    commands_list.append('genhtml --highlight --legend --output-directory %(output_dir)s %(coverage_file)s' % data)
    result = ChainCalls(env, commands_list, env.GetOption('verbose'))
    if result == 0:
        env.Cprint('lcov report in: %s' % indexFile, 'green')
    return result


def RunDoxygen(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running DOXYGEN ===\n', 'green')
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
        env.Cprint('[generated] %s' % target, 'green')
    return rc


def AStyleCheck(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running ASTYLE-CHECK ===\n', 'green')
    # The return value.
    result = 0
    # Get the report file.
    report_file = target[0].abspath
    # Get the output directory.
    output_directory = os.path.split(report_file)[0]
    # Check if the directory exists.
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    # Check if some file need astyle.
    check_astyle_result = _CheckAstyle(env, source, output_directory)
    # Check if _CheckAstyle() fails.
    if check_astyle_result is None:
        return 1
    # Open the report file.
    try:
        report = open(report_file, 'w')
    except IOError:
        env.Cprint('No such file or directory:', report_file)
        return 1
    else:
        # If we can open it we truncate it.
        report.truncate(0)
    # If some file needs astyle we print info.
    if check_astyle_result['need_astyle']:
        # Print a warning message.
        env.Cprint('[WARNING] The following files need astyle:', 'red')
        # Print what need to be astyled.
        for f, info in check_astyle_result['need_astyle_list']:
            # Write into hte report file.
            report.write(info+'\n\n')
            # Print on the screen.
            env.Cprint('====> %s' % f, 'red')
            env.Cprint(info,'yellow')
        result = 1
    else:
        env.Cprint('[OK] No file needs astyle.', 'green')
    # Close the report file.
    report.close()
    if check_astyle_result['need_astyle']:
        cmd = 'grep %s %s | grep %s | grep %s | grep %s > /dev/null' % \
            ('-v "^[+-].*for.*:"',report_file,'-v "^---"','-v "^+++"','"^[+-]"')
        if subprocess.call(cmd, shell=True) > 0:
            result = 0
    return 0


def AStyle(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running ASTYLE ===\n', 'green')
    # Get the project directory.
    project_dir = target[0].abspath
    # Generate the list of files to apply astyle.
    #   This is because the files in 'source' point to the build/ directory 
    #   instead of the projects/ directory.
    build_dir = env['BUILD_DIR']
    ws_dir = env['WS_DIR']
    file_list = ' '.join([f.abspath.replace(build_dir,ws_dir) for f in source if "tests/ref/" not in f.abspath])
    # Create the command for subprocess.call().
    cmd = "astyle -k1 --options=none --convert-tabs -bSKpUH %s" % file_list
    # Run astyle.
    result = subprocess.call(cmd, shell=True)
    if result != 0:
        env.cerror('[astyle] ERROR running astyle on: %s' % project_dir)
    else:
        env.Cprint('[astyle] OK on: %s' % project_dir, 'green')
    return result


def RunPdfLatex(env, target, source):
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


def RunValgrind(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running VALGRIND ===\n', 'green')
    # Get the current directory.
    cwd = os.getcwd()
    # Get the test executable file.
    test = source[0].abspath
    # Get the test executable directory.
    test_dir = source[0].dir.abspath
    # Change to the test directory.
    os.chdir(test_dir)
    # Command to execute valgrind.
    env_var = 'GTEST_DEATH_TEST_USE_FORK=1'
    val_opt = env['VALGRIND_OPTIONS']
    testsuite = env.GetOption('testsuite')
    rep = (env_var, val_opt, test, testsuite)
    cmd = '%s valgrind %s %s --gtest_filter=%s' % rep
    # Execute the command.
    ret_val = subprocess.call(cmd, shell=True)
    # Get back to the previous directory.
    os.chdir(cwd)
    return 0


def RunCCCC(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running CCCC ===\n', 'green')
    # Get the report file name.
    report_file_name = target[0].abspath
    # Tell cccc the name of the output file.
    env.Append(CCCC_OPTIONS='--html_outfile=%s' % report_file_name)
    # Get the output directory.
    output_directory = os.path.split(report_file_name)[0]
    # Tell cccc the name of the output directory.
    env.Append(CCCC_OPTIONS = '--outdir=%s' % output_directory)
    # Check if the output directory directory already exists.
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    # Create a string with the options for cccc.
    options = ' '.join([opt for opt in env['CCCC_OPTIONS']])
    # Create a string with the file names for cccc.
    files = ' '.join([f.abspath for f in source])
    # Create the command to be pass to subprocess.call()
    cmd = 'cccc %s %s' % (options, files)
    return subprocess.call(cmd, shell=True)


def RunCLOC(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running CLOC ===\n', 'green')
    # Get the report file name.
    report_file = target[0].abspath
    # Check the type of the report file.
    if env['CLOC_OUTPUT_FORMAT'] == 'txt':
        output_option = '--out=%s.txt' % report_file
    elif env['CLOC_OUTPUT_FORMAT'] == 'sql':
        output_option = '--sql=%s.sql' % report_file
    elif env['CLOC_OUTPUT_FORMAT'] == 'xml':
        output_option = '--xml --out=%s.xml' % report_file
    else:
        error_msg = "Invalid value for the CLOC_OUTPUT_FORMAT flag"
        value = env['CLOC_OUTPUT_FORMAT']
        env.Cprint('[ERROR] %s : %s' % (error_msg,value))
    # Set the type of the report file.
    env.Append(CLOC_OPTIONS = output_option)
    # Get the output directory.
    output_directory = os.path.split(report_file)[0]
    # Check if the output directory directory already exists.
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    # Create a string with the options for cloc.
    options = ' '.join([opt for opt in env['CLOC_OPTIONS']])
    # Create a string with the file names for cloc.
    files = ' '.join([f.abspath for f in source])
    # Create the command to be pass to subprocess.call()
    cmd = 'cloc %s %s' % (options, files)
    return subprocess.call(cmd, shell=True)


def RunCppCheck(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running CPPCHECK ===\n', 'green')
    # Get the report file name.
    report_file = target[0].abspath
    # Get the output directory.
    output_directory = os.path.split(report_file)[0]
    # Check if the output directory for the cppcheck report already exists.
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    # Create a string with the options for cppcheck.
    import ipdb; ipdb.set_trace()
    options = ' '.join([opt for opt in env['CPPCHECK_OPTIONS']])
    # We create a string with the files for cppcheck.
    files = ' '.join([f.abspath for f in source])
    # Create the command to be pass to subprocess.call()
    cmd = "cppcheck %s %s | sed '/files checked /d' > %s" % (options, files, report_file)
    return subprocess.call(cmd, shell=True)


def RunMocko(env, target, source):
    # Get the file list.mocko.
    mocko_list = source[0].abspath
    # Get mocko executable file.
    mocko_exe = source[1].abspath
    # Get the tests directory.
    directory = os.path.split(mocko_list)[0]
    # The mocko executable file.
    mocko = env.Dir('$INSTALL_BIN_DIR').File('mocko').abspath
    # Execute mocko.
    cwd = env.Dir('#').abspath
    os.chdir(directory)
    ret_val = subprocess.call('%s %s' % (mocko, mocko_list), shell=True)
    os.chdir(cwd)
    return ret_val


def RunReadyToCommit(env, target, source):
    # Print message on the screen.
    env.Cprint(
        '\n===== Checking if the project is Ready To be Commited =====\n',
        'green'
    )
    # Check for astyle.
    if _RTCCheckAstyle(env):
        env.Cprint('ASTYLE   : [OK]', 'green')
    else:
        env.Cprint('ASTYLE   : [ERROR]', 'red')
    # Cheeck for cppcheck.
    if _RTCCheckCppcheck(env):
        env.Cprint('CPPCHECK : [OK]', 'green')
    else:
        env.Cprint('CPPCHECK : [ERROR]', 'red')
    # Check for tests.
    if _RTCCheckTests(env):
        env.Cprint('TESTS    : [OK]', 'green')
    else:
        env.Cprint('TESTE    : [ERROR]', 'red')
    # Check for valgrind.
    if _RTCCheckValgrind(env):
        env.Cprint('VALGRIND : [OK]', 'green')
    else:
        env.Cprint('VALGRIND : [ERROR]', 'red')
    print "" # Just an empty line.
    return 0


def _CheckAstyle(env, source, output_directory):
    # Create a temporary directory.
    tmp_dir = os.path.join(output_directory, 'tmp')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    # The list of copied files.
    files_list = []
    # Copy all sources into the temporary directory.
    for file in source:
        if "tests/ref/" not in file.abspath: # TODO: Remove this line.
            os.system('cp %s %s' % (file.abspath, tmp_dir))
            f = env.Dir(tmp_dir).File(os.path.split(file.abspath)[1])
            files_list.append(f)
    files_str = ' '.join([x.abspath for x in files_list])
    # This variable holds if some file needs astyle.
    need_astyle = False
    # A list for the files that needs astyle.
    need_astyle_list = []
    # Create the command for subprocess.call().
    cmd = 'astyle -k1 --options=none --convert-tabs -bSKpUH %s' % files_str
    # To see if a file needs astyle we first apply astyle to the file and
    # check if it suffer some change.
    if subprocess.call(cmd, shell=True, stdout=subprocess.PIPE) != 0:
        # If astyle fails, we fail.
        return None
    # Check if astyle did some modifications.
    for file in files_list:
        # If the '.orig' file exists for the file then it was modify by astyle.
        if os.path.exists('%s.orig' % file.abspath):
            # Print the differences between files.
            cmd = 'diff -Nau %s.orig %s' % (file.abspath,file.abspath)
            diff = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            diff_stdout = diff.stdout.read()
            diff.wait()
            need_astyle_list.append((os.path.split(file.abspath)[1],diff_stdout))
            need_astyle = True
    # Remove the temporary directory.
    os.system('rm -rf %s' % tmp_dir)
    # Return a dictionary.
    return {'need_astyle':need_astyle, 'need_astyle_list':need_astyle_list}


def _RTCCheckAstyle(env):
    # Get astyl-check report file name.
    report_file = os.path.join(env['INSTALL_REPORTS_DIR'], 'astyle-check')
    report_file = os.path.join(report_file, env['PROJECT_NAME'])
    report_file = os.path.join(report_file, 'AstyleCheckReport.diff')
    # Check if the project needs astyle.
    cmd = "cat %s | grep -E '^\+' | grep -v +++ | grep -v 'for (auto'" % report_file
    return subprocess.call(cmd, shell=True, stdout=subprocess.PIPE) != 0


def _RTCCheckCppcheck(env):
    # Get the cppcheck report file name.
    report_file = os.path.join(env['INSTALL_REPORTS_DIR'], 'cppcheck')
    report_file = os.path.join(report_file, env['PROJECT_NAME'])
    report_file = os.path.join(report_file, 'CppCheckReport.xml')
    # Check if the project needs astyle.
    cmd = "cat %s | grep '<error>'" % report_file
    return subprocess.call(cmd, shell=True, stdout=subprocess.PIPE) != 0


def _RTCCheckTests(env):
    return True


def _RTCCheckValgrind(env):
    # Get valgrind report file name.
    report_file = os.path.join(env['INSTALL_REPORTS_DIR'], 'valgrind')
    report_file = os.path.join(report_file, env['PROJECT_NAME'])
    report_file = os.path.join(report_file, 'valgrind-report.xml')
    # Check if the project needs astyle.
    cmd = "cat %s | grep '<error>'" % report_file
    return subprocess.call(cmd, shell=True, stdout=subprocess.PIPE) != 0

