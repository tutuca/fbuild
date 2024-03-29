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


"""
    This module contains all fudepan-build customized builders.
"""


import fnmatch
import subprocess
import os.path
import shutil
import os
import utils
import re
from SCons.Defaults import Delete
from SCons.Builder import Builder
from SCons.Action import Action
from core_components import HEADERS_FILTER
from xml.dom import minidom
from utils import ChainCalls, FindSources, CheckPath, WaitProcessExists, RemoveDuplicates, DeleteLinesInFile


HEADERS = [".h", ".hpp"]
SOURCES = [".c", ".cpp"]
# Return status of a builder.
EXIT_SUCCESS = 0
EXIT_ERROR = 1
# Constat to repsent spaces between options.
SPACE = ' '
# The first element of an iterable object.
FIRST_ELEMENT = 0
# This is for RTC target
CPPCHECK_CONFIG_RESULT = 0


def init(env):
    bldRUT = Builder(action=Action(RunUnittest, PrintDummy))
    env.Append(BUILDERS={'RunUnittest': bldRUT})
    #-
    bldInitLcov = Builder(action=Action(InitLcov, PrintDummy))
    env.Append(BUILDERS={'InitLcov': bldInitLcov})
    #-
    bldRLcov = Builder(action=Action(RunLcov, PrintDummy))
    env.Append(BUILDERS={'RunLcov': bldRLcov})
    #-
    bldDoxygen = Builder(action=Action(RunDoxygen, PrintDummy))
    env.Append(BUILDERS={'RunDoxygen': bldDoxygen})
    env['DEFAULT_DOXYFILE'] = env.File('#/conf/doxygenTemplate').abspath
    #-
    # bldAStyleCheck = Builder(action=Action(AStyleCheck, PrintDummy))
    # env.Append(BUILDERS={'RunAStyleCheck': bldAStyleCheck})
    #-
    # bldAStyle = Builder(action=Action(AStyle, PrintDummy))
    # env.Append(BUILDERS={'RunAStyle': bldAStyle})
    #-
    bldPdfLatex = Builder(action=Action(RunPdfLatex, PrintDummy))
    env.Append(BUILDERS={'RunPdfLatex':  bldPdfLatex})
    env['PDFLATEX_OPTIONS'] = ''
    #-
    bldValgrind = Builder(action=Action(RunValgrind, PrintDummy))
    env.Append(BUILDERS={'RunValgrind': bldValgrind})
    env['VALGRIND_OPTIONS'] = ['--leak-check=full', '--show-reachable=yes',
                               '--error-limit=no', '--track-origins=yes']
    #-
    bldCCCC = Builder(action=Action(RunCCCC, PrintDummy))
    env.Append(BUILDERS={'RunCCCC':  bldCCCC})
    env['CCCC_OPTIONS'] = []
    #-
    bldCLOC = Builder(action=Action(RunCLOC, PrintDummy))
    env.Append(BUILDERS={'RunCLOC':  bldCLOC})
    env['CLOC_OUTPUT_FORMAT'] = 'txt'  # txt | sql | xml
    env['CLOC_OPTIONS'] = []
    #-
    env['CPPCHECK_OPTIONS'] = ['-f', '--enable=all']
    #-
    bldMocko = Builder(action=Action(RunMocko, PrintDummy))
    env.Append(BUILDERS={'RunMocko': bldMocko})
    env['MOCKO_OPTIONS'] = []
    #-
    bldReadyToCommit = Builder(action=Action(RunReadyToCommit, PrintDummy))
    env.Append(BUILDERS={'RunReadyToCommit': bldReadyToCommit})
    #-
    bldInfo = Builder(action=Action(RunInfo, PrintDummy))
    env.Append(BUILDERS={'RunInfo': bldInfo})
    #-
    bldStaticAnalysis = Builder(action=Action(RunStaticAnalysis, PrintDummy))
    env.Append(BUILDERS={'RunStaticAnalysis': bldStaticAnalysis})
    #-
    bldAddressSanitizer = Builder(action=Action(RunASan, PrintDummy))
    env.Append(BUILDERS={'RunASan': bldAddressSanitizer})
    #-
    bldNamecheck = Builder(action=Action(RunNamecheck, PrintDummy))
    env.Append(BUILDERS={'RunNamecheck': bldNamecheck})


def PrintDummy(env, target, source):
    return ""


def RunNamecheck(env, target, source):
    env.Cprint('\n==== Running NameCheck ====\n', 'green')
    includes = env['INC_PATHS']
    includes = SPACE.join(['-I%s' % x.abspath for x in includes])
    cpp_files = FindSources(source, ['.cpp', '.cc'])
    c_files = FindSources(source, ['.c'])
    namecheck = '/usr/lib/libnamecheck.so'
    namecheck_conf = os.path.join(os.getcwd(), "conf", "namecheck-conf.csv")
    if os.path.exists(namecheck) and os.path.exists(namecheck_conf):
        # Add the flags to the compiler if the plug-in is present.
        plugin = '-fplugin=%s' % namecheck
        conf = '-fplugin-arg-libnamecheck-path=%s' % namecheck_conf
    else:
        env.cerror(
            'Please check if you have isntalled Namecheck and the configuration file.')
        return EXIT_SUCCESS
    if cpp_files:
        _ExecuteNamecheck(env, cpp_files, plugin, conf, includes)
    if c_files:
        _ExecuteNamecheck(env, c_files, plugin, conf, includes)
    return EXIT_SUCCESS


def RunUnittest(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running TESTS ===\n', 'green')
    # Get the test directory and the test executable.
    test_dir, test_program = os.path.split(source[0].abspath)
    # Get the test suite to be executed.
    test_suite = env.GetOption('testsuite')
    # Check if a report file is needed.
    if env.NEED_TEST_REPORT:
        os.environ['GTEST_OUTPUT'] = env.test_report
    # Check if the test uses mocko or not.
    if env._USE_MOCKO:
        cmd = "cd %s; gdb -x mocko_bind.gdb %s" % (test_dir, test_program)  # NOTE: The mocko_bind.gdb is hardcode here!
    else:
        cmd = "cd %s; ./%s --gtest_filter=%s" % (test_dir, test_program, test_suite)
    if env.GetOption('verbose'):
        env.Cprint('>> %s\n' % cmd, 'end')
    # Execute the test.
    test_proc = subprocess.Popen(cmd, shell=True)
    if test_proc.wait():
        env.cerror('\n\nTest result: *** FAILED ***\n\n')
    else:
        env.Cprint('\n\nTest result: *** PASSED ***\n\n', 'green')
    return EXIT_SUCCESS


def InitLcov(env, target, source):
    indexFile = target[0].abspath
    silent = env.GetOption('verbose')
    data = {
        'coverage_file': os.path.join(os.path.dirname(os.path.dirname(indexFile)), 'coverage_output.dat'),
        'output_dir': env.Dir('INSTALL_METRICS_DIR'),
        'project_dir': env['PROJECT_DIR']
    }
    result = utils.ChainCalls(env, [
        'lcov --zerocounters --directory %(project_dir)s -b .' % data,
        'lcov --capture --initial --directory %(project_dir)s -b . --output-file %(coverage_file)s' % data,
    ], silent)
    if result:
        env.cerror('\n\n[ERROR] Failed initializing Lcov, error: %s\n\n' % result)
    return EXIT_SUCCESS


def RunLcov(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running COVERAGE ===\n', 'green')
    indexFile = target[0].abspath
    output_dir = os.path.dirname(indexFile)
    data = {
        'coverage_file': os.path.join(os.path.dirname(output_dir), 'coverage_output.dat'),
        'output_dir': output_dir,
        'project_dir': env['PROJECT_DIR']
    }
    commands_list = [
        'rm -f %(coverage_file)s' % data,
        'lcov --no-checksum --directory %(project_dir)s -b . --capture --ignore-error source --output-file %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*usr/include*" -o %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*/tests/*" -o %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*/install/*" -o %(coverage_file)s' % data
    ]
    for dep in env['PROJECT_DEPS']:
        data['project_dep'] = dep
        cmd = 'lcov --remove %(coverage_file)s "*%(project_dep)s*" -o %(coverage_file)s' % data
        commands_list.append(cmd)
    commands_list.append('genhtml --highlight --legend --output-directory %(output_dir)s %(coverage_file)s' % data)
    result = utils.ChainCalls(env, commands_list, env.GetOption('verbose'))
    if result:
        env.cerror('\n\n[ERROR] Failed running Lcov, error: %s\n\n' % result)
    elif not os.path.exists(indexFile):
        env.cerror('\n\n[ERROR] Failed to create report file.\n\n')
    else:
        env.Cprint('lcov report in: %s' % indexFile, 'green')
    return EXIT_SUCCESS


def RunDoxygen(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running DOXYGEN ===\n', 'green')
    # Path to the doxygen template file.
    doxyTamplate = source[0].abspath
    # Path to the doc/project directory.
    target = target[0].abspath
    targetName = os.path.basename(target)
    # Create the doc/project directory.
    os.mkdir(target)
    # Path to the project directory.
    projectDir, __ = os.path.split(source[1].abspath)
    # Path yo doxygen file for thise project.
    projectDoxyFile = projectDir + '/__tmp_doxyfile'

    # Copy the doxygen file template to the project directory.
    with open(doxyTamplate, 'r') as fsrc:
        doxygenSrc = fsrc.read()
    with open(projectDoxyFile, "w") as ftgt:
        ftgt.write(doxygenSrc.replace('$PROJECT_NAME', targetName)
                             .replace('$OUTPUT_DIR', target))
    # Create the command to be executed.
    output_file = os.path.join(target, 'doxyfile_generation.output')
    doxygen_proc = subprocess.Popen("doxygen %s > %s" % (projectDoxyFile, output_file), 
        shell=True, cwd=projectDir)
    rc = doxygen_proc.wait()
    if rc:
        env.cerror('[FAILED] %s, error: %s' % (target, rc))
    else:
        env.Cprint('[GENERATED] %s/html/index.html\n' % target, 'green')
    if env.GetOption('verbose'):
        doxygen_results_proc = subprocess.Popen("cat %s" % output_file, shell=True)
        doxygen_results_proc.wait()
    os.remove(projectDoxyFile)
    return EXIT_SUCCESS


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
    pdflates_proc = subprocess.Popen('cd ' + pathHead + ' ; pdflatex ' + env['PDFLATEX_OPTIONS']
        + ' -output-directory "' + tmpPdf2TexDir + '" ' + pathTail, shell=True)
    shutil.move(targetDir, tmpPdf2TexDir + pathTail[:-4] + ".pdf")
    shutil.rmtree(tmpPdf2TexDir)
    if pdflates_proc.wait():
        env.cerror('\n\n[ERROR] Failed running PDFLatex, error: %s\n\n' % pdflates_proc.wait())
    return EXIT_SUCCESS


def RunValgrind(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running VALGRIND ===\n', 'green')
    # Constants to access the sources list.
    TEST_EXEC = 0
    # Get the test executable file.
    test_file = source[TEST_EXEC].abspath
    # Get the test executable directory.
    test_dir = source[TEST_EXEC].dir.abspath
    # Get the current directory.
    cwd = os.getcwd()
    # Change to the test directory.
    os.chdir(test_dir)
    # Command to execute valgrind.
    env_var = 'GTEST_DEATH_TEST_USE_FORK=1'  # Environment variable for gtest.
    val_opt = SPACE.join(env['VALGRIND_OPTIONS'])  # Options passed to valgrind.
    testsuite = env.GetOption('testsuite')  # The test suite to execute.
    cmd = '%s valgrind %s %s --gtest_filter=%s' % (env_var, val_opt, test_file, testsuite)
    if env.GetOption('verbose'):
        env.Cprint('>> %s\n' % cmd, 'end')
    # Execute the command.
    valgrind_proc = subprocess.Popen(cmd, shell=True)
    # Check if the test uses mocko.
    if env._USE_MOCKO:
        _RunValgrindWithMocko(env, test_file, valgrind_proc)
    # Get back to the previous directory.
    os.chdir(cwd)
    # Wait valgrind to terminate.
    if valgrind_proc.wait():
        env.cerror('\n\n[ERROR] Failed running Valgrind, error: %s\n\n' % valgrind_proc.wait())
    return EXIT_SUCCESS


def _RunValgrindWithMocko(env, test_file, valgrind_proc):
    # Command to execute the test with gdb.
    gdb_cmd = "gdb --batch -x mocko_bind_valgrind.gdb %s" % test_file  # NOTE: The mocko_bind_valgrind.gdb is hardcode here!
    if env.GetOption('verbose'):
        env.Cprint('>> %s' % gdb_cmd, 'end')
    # Wait until valgrind start.
    utils.WaitProcessExists(valgrind_proc.pid)
    # Execute the test with gdb.
    gdb_proc = subprocess.Popen(gdb_cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # Read standard output and error, and wait until the test terminate.
    gdb_stdout, gdb_stderr = gdb_proc.communicate()
    if env.GetOption('verbose') and gdb_stdout:
        env.Cprint('=== GDB STDOUT ==', 'end')
        env.Cprint(gdb_stdout, 'end')
    if env.GetOption('verbose') and gdb_stderr:
        env.Cprint('=== GDB STDERR ==', 'end')
        env.Cprint(gdb_stderr, 'end')
    if gdb_proc.wait():
        env.cerror('\n[ERROR] Failed running gdb_proc, error: %s\n' % gdb_proc.wait())


def RunASan(env, target, source):
    env.Cprint('\n=== Running Address Sanitizer ===\n', 'green')
    # Get the test directory and the test executable.
    test_dir, test_program = os.path.split(source[0].abspath)
    asan_cmd = './%s' % test_program
    # Execute Address Sanitizer
    asan_proc = subprocess.Popen(asan_cmd, cwd=test_dir, shell=True,
                                 stderr=subprocess.PIPE,
                                 stdout=subprocess.PIPE)
    # Read the asan output in the stderr
    err = asan_proc.stderr.read()
    if asan_proc.wait():
        env.Cprint('This error was found:\n', 'yellow')
        env.Cprint(err, 'end')
        env.CprintSameLine([('Address Sanitizer result: ','end'),('--- ERROR ---\n', 'red')])
    else:
        env.CprintSameLine([('Address Sanitizer result: ','end'),('--- PASSED ---', 'green')])
        env.Cprint('No output generated.\n', 'end')
    return EXIT_SUCCESS


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
    env.Append(CCCC_OPTIONS='--outdir=%s' % output_directory)
    # Check if the output directory directory already exists.
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    # Create a string with the options for cccc.
    options = SPACE.join([opt for opt in env['CCCC_OPTIONS']])
    # Create a string with the file names for cccc.
    files = SPACE.join([f.abspath for f in source])
    # Create the command to be executed.
    cmd = 'cccc %s %s' % (options, files)
    cccc_proc = subprocess.Popen(cmd, shell=True)
    if cccc_proc.wait():
        env.cerror('\n\n[ERROR] Failed running CCCC, error: %s\n\n' % cccc_proc.wait())
    return EXIT_SUCCESS


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
        env.Cprint('[ERROR] %s : %s' % (error_msg, value))
    # Set the type of the report file.
    env.Append(CLOC_OPTIONS=output_option)
    # Get the output directory.
    output_directory = os.path.split(report_file)[0]
    # Check if the output directory directory already exists.
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    # Create a string with the options for cloc.
    options = SPACE.join([opt for opt in env['CLOC_OPTIONS']])
    # Create a string with the file names for cloc.
    files = SPACE.join([f.abspath for f in source])
    # Create the command to be executed.
    cmd = 'cloc %s %s' % (options, files)
    cloc_proc = subprocess.Popen(cmd, shell=True)
    if cloc_proc.wait():
        env.cerror('\n\n[ERROR] Failed running CLOC, error: %s\n\n' % cloc_proc.wait())
    return EXIT_SUCCESS


def RunStaticAnalysis(env, target, source):
    '''
    Decide wether to run cppcheck or splint based on the kind of 
    source files we have.

    :param env: The excecution environment.
    :param target: The compilation target.
    :param source: The list of source files.

    '''
    cppcheck_rc = False
    splint_rc = False
    target = target.pop()
    env.Cprint('\n=== Running Static Code Analysis ===\n', 'green')
    cppcheck_options = SPACE.join([opt for opt in env['CPPCHECK_OPTIONS']])
    includes = env['INC_PATHS']
    cpp_files = utils.FindSources(source, ['.cpp', '.cc'])
    cppcheck_dir = target.Dir('cppcheck')
    splint_dir = target.Dir('splint')
    c_files = utils.FindSources(source, ['.c'])
    headers = includes
    if cpp_files:
        utils.CheckPath(cppcheck_dir.abspath)
        cppcheck_rc = _RunCppCheck(cppcheck_dir, cpp_files, includes, 
            cppcheck_options, env)
    if c_files:
        utils.CheckPath(splint_dir.abspath)
        splint_rc = _RunSplint(splint_dir, c_files, includes, env)
    if headers and not (cpp_files or c_files):
        utils.CheckPath(cppcheck_dir.abspath)
        cppcheck_rc = _RunCppCheck(cppcheck_dir, utils.FindSources(source, 
            ['.h', '.hh', '.hpp']), headers, cppcheck_options, env)
    # Return the output of both builders
    if cppcheck_rc or splint_rc:
        env.cerror('\n\n[ERROR] Failed running Static Analysis\n\n')
    return EXIT_SUCCESS


def RunMocko(env, target, source):
    if env.GetOption('verbose'):
        # Print message on the screen.
        env.Cprint('\n=== Running MOCKO ===\n', 'green')
    # Constants to access the sources list
    MOCKO_LIST = 0; MOCKO_EXEC = 1
    # Constants to access the targets list.
    # Get the file list.mocko.
    mocko_list = source[MOCKO_LIST].abspath
    # Get the tests directory, which is the same as the list.mocko directory.
    directory = source[MOCKO_LIST].dir.abspath
    # Get the mocko executable file.
    mocko = source[MOCKO_EXEC].abspath
    # Get current directory.
    cwd = env.Dir('#').abspath
    # Change to the test's directory.
    os.chdir(directory)
    if env.GetOption('verbose'):
        env.Cprint('>> chdir %s' % directory, 'end')
    # Running mocko.
    # NOTE: Do not change the order of these function calls!
    _RunMockoVGDB(env, mocko, mocko_list)
    _RunMockoGDB(env, mocko, mocko_list)
    # Return to previous directory.
    os.chdir(cwd)
    if env.GetOption('verbose'):
        env.Cprint('>> chdir %s' % cwd, 'end')
    return EXIT_SUCCESS


def _RunMockoGDB(env, mocko, mocko_list):
    cmd_gdb = '%s -f %s' % (mocko, mocko_list)
    if env.GetOption('verbose'):
        env.Cprint('>> %s' % cmd_gdb, 'end')
    mocko_gdb_proc = subprocess.Popen(
        cmd_gdb,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    mocko_gdb_proc_stdout, mocko_gdb_proc_stderr = mocko_gdb_proc.communicate()
    if env.GetOption('verbose') and mocko_gdb_proc_stdout:
        env.Cprint(mocko_gdb_proc_stdout, 'end')
    if env.GetOption('verbose') and mocko_gdb_proc_stderr:
        env.Cprint(mocko_gdb_proc_stderr, 'end')
    if mocko_gdb_proc.wait():
        env.cerror('\n[ERROR] Failed running Mocko (mocko_gdb_proc), error: %s\n' % mocko_gdb_proc.wait())


def _RunMockoVGDB(env, mocko, mocko_list):
    cmd_vgdb = '%s -f %s -v' % (mocko, mocko_list)
    if env.GetOption('verbose'):
        env.Cprint('>> %s' % cmd_vgdb, 'end')
    mocko_vgdb_proc = subprocess.Popen(
        cmd_vgdb,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    mocko_vgdb_proc_stdout, mocko_vgdb_proc_stderr = mocko_vgdb_proc.communicate()
    if env.GetOption('verbose') and mocko_vgdb_proc_stdout:
        env.Cprint(mocko_vgdb_proc_stdout, 'end')
    if env.GetOption('verbose') and mocko_vgdb_proc_stderr:
        env.Cprint(mocko_vgdb_proc_stderr, 'end')
    os.system('mv mocko_bind.gdb mocko_bind_valgrind.gdb')
    if env.GetOption('verbose'):
        env.Cprint('mv mocko_bind.gdb mocko_bind_valgrind.gdb', 'end')
    if mocko_vgdb_proc.wait():
        env.cerror('\n[ERROR] Failed running Mocko (mocko_vgdb_proc), error: %s\n' % mocko_vgdb_proc.wait())


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
        env.Cprint('STATIC-ANALYSIS : [OK]', 'green')
    else:
        env.Cprint('STATIC-ANALYSIS : [ERROR]', 'red')
    # Check for tests.
    if _RTCCheckTests(env):
        env.Cprint('TESTS    : [OK]', 'green')
    else:
        env.Cprint('TESTS    : [ERROR]', 'red')
    # Check for valgrind.
    if _RTCCheckValgrind(env):
        env.Cprint('VALGRIND : [OK]', 'green')
    else:
        env.Cprint('VALGRIND : [ERROR]', 'red')
    env.Cprint("", 'end')  # Just an empty line.
    return EXIT_SUCCESS


def RunInfo(env, target, source):
    #Take project info
    name = target[0].name
    project_type = env['PROJECT_TYPE']
    # Print the project info
    env.Cprint("\n----------- %s -----------\n" % name, "blue")
    env.CprintSameLine([("The Project type is: ", "end"), ("%s \n" % project_type, "green")])
    # Separate sources and headers

    headers_list, sources_list = map(
        lambda FILTER: sorted(
            utils.RemoveDuplicates(x 
                for x in source for y in FILTER 
                if x.name.endswith(y))
            ), 
        [SOURCES, HEADERS]
    )

    # Print headers and sources
    if headers_list:
        env.Cprint("List of headers:", "end")
        for hdr in headers_list:
            env.Cprint(hdr, "cyan")
        # New line at the end of the headers
        env.Cprint("","end")
    if sources_list:
        env.Cprint("List of sources:", "end")
        for src in sources_list:
            env.Cprint(src, "purple")
        # New line at the end of the sources
        env.Cprint("","end")
    return EXIT_SUCCESS


def _RunCppCheck(report_dir, files, includes, options, env):
    report_file = os.path.join(report_dir.abspath, 'static-analysis-report')
    success = False
    to_include = None
    if 'xml' in options:
        report_file = report_file+'.xml'
    else:
        report_file = report_file+'.txt'
    to_include = SPACE.join(['-I%s' % x.abspath for x in includes])
    cmd = "cppcheck %s %s %s" % (options, files, to_include)
    env['CPPCHECK_CONFIG_RESULT'] = _CheckCppCheckConfig(env, cmd)
    # Create the suppression list.
    name = '.suppression_list.txt'
    _CreateSuppressionList(name, includes, env)
    cmd = '%s --suppressions %s' % (cmd, name)
    if env.GetOption('verbose'):
        env.Cprint('>>> %s' % cmd, 'end')
    env.Cprint('Running...', 'green')
    with open(report_file, 'w+') as rf:
        pipe = subprocess.Popen(
            cmd,
            shell=True,
            stderr=rf
        )
    success = pipe.wait()
    re = r'unmatchedSuppression|cppcheckError|Unmatched suppression'
    utils.DeleteLinesInFile(re, report_file)
    # Delete the suppression list created
    try:
        os.remove(name)
    except OSError:
        pass
    return env['CPPCHECK_CONFIG_RESULT'] == success

def _CheckCppCheckConfig(env, cmd):
    """
    Description: CppCheck has the --check-config flag to check if 
    everything is OK to run CppCheck in the files.
    Arguments:
        - env: the current environment
        - cmd: the command to append the flag.
    Return: EXIT_SUCCESS or EXIT_ERROR.
    """
    result = EXIT_SUCCESS
    env.Cprint('Checking the files', 'green')
    check = subprocess.Popen(
        '%s --check-config' % cmd,
        shell=True,
        stderr=subprocess.PIPE
    )
    error = check.stderr.read()
    check.wait()
    if 'error' in error:
        env.cerror('[ERROR] Cannot run Cppcheck. Error: %s' % error)
        result = EXIT_ERROR
    return result


def _CreateSuppressionList(name, includes, env):

    include_list = [x.abspath for x in includes if not '/usr/' in x.abspath]
    headers_list = []
    for x in include_list:
        headers_list.extend(_FindHeadersPath(x))
    # Libraries from /usr/include can be needed.
    headers_list.append('/usr/include')
    headers_list.append('/usr/local/include')
    # Check if the user defined a suppression-list.
    user_sup = env.get('CPPCHECK_SUPPRESSION')
    if user_sup:
        with open(user_sup, 'r') as sup:
            sup_to_append = sup.read()
    with open(name, 'w+') as f:
        # Add suppression for unnecessaries errors.
        f.write('unmatchedSuppression\n') 
        f.write('cppcheckError\n')
        for x in set(headers_list):
            f.write('*:%s/*\n' % x)
        if user_sup:
            f.write(sup_to_append)


def _FindHeadersPath(path):
    """
    Description:
        Find headers into directories and if find one, take the directory.
    Arguments:
        - path: The path that will be walked.
    Return:
        A list with all the paths found.
    """
    filters = HEADERS_FILTER
    paths = []
    for root, dirnames, names in os.walk(path):
        for name in names:
            if any([fnmatch.fnmatch('%s/%s' % (root, name), filter) for filter in filters]):
                if not root in paths:
                    paths.append(root)
    return paths

def _RunSplint(report_dir, files, includes, env):
    report_file = os.path.join(report_dir.abspath, 'static-analysis-report')
    includes += [env.Dir('/usr/include')]
    headers = SPACE.join(['-I%s ' % x for x in includes])
    flags = env.get('SPLINT_FLAGS', [])
    cmd = "splint %s %s %s > %s.txt" % (files, headers, 
        SPACE.join(flags), report_file)
    if env.GetOption('verbose'):
        env.Cprint(cmd, 'end')
    splint_proc = subprocess.Popen(cmd, shell=True)
    return splint_proc.wait()

def _RTCCheckAstyle(env):
    # Path to the report file.
    report_file = os.path.join(env['INSTALL_REPORTS_DIR'], 'astyle-check')
    report_file = os.path.join(report_file, env['PROJECT_NAME'])
    report_file = os.path.join(report_file, 'AstyleCheckReport.diff')
    # Command to be executed.
    cmd = "grep -E '^\+' %s| grep -v +++ " % report_file
    # Execute the command.
    astyle_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    # Read the output of the process.
    astyle_proc.stdout.read()
    # Wait until process terminates and return the status.
    # grep returns 1 if the line is not found
    return astyle_proc.wait()


def _RTCCheckCppcheck(env):
    # Path to the report file.
    report_file = os.path.join(env['INSTALL_REPORTS_DIR'], 'static-analysis')
    report_file = os.path.join(report_file, env['PROJECT_NAME'])
    report_file = os.path.join(report_file, 'cppcheck')
    report_file = os.path.join(report_file, 'static-analysis-report.xml')
    # Commands to be executed.
    cmd_error = 'grep severity=\\"error\\" %s' % report_file
    cmd_warning = 'grep severity=\\"warning\\" %s' % report_file
    # Execute the commands.
    errors_proc = subprocess.Popen(cmd_error, shell=True, stdout=subprocess.PIPE)
    warnings_proc = subprocess.Popen(cmd_warning, shell=True, stdout=subprocess.PIPE)
    # Read the output of the processes.
    errors_proc.stdout.read()
    warnings_proc.stdout.read()
    # Wait until the processes terminate.
    errors = errors_proc.wait()
    warnings = warnings_proc.wait()
    # grep returns 1 if the line is not found
    return errors and warnings and not env['CPPCHECK_CONFIG_RESULT']


def _RTCCheckTests(env):
    # Path to the report file.
    report_file = os.path.join(env['INSTALL_REPORTS_DIR'], 'test')
    report_file = os.path.join(report_file, env['PROJECT_NAME'])
    report_file = os.path.join(report_file, 'test-report.xml')
    result = os.path.exists(report_file)
    # Commands to be executed.
    cmd_failures = 'grep "<testsuites" %s | grep -v "failures=\\"0\\""' % report_file
    cmd_errors = 'grep "<testsuites" %s | grep -v "errors=\\"0\\""' % report_file
    # Execute the commands.
    if result:
        failures_proc = subprocess.Popen(cmd_failures, shell=True, stdout=subprocess.PIPE)
        errors_proc = subprocess.Popen(cmd_errors, shell=True, stdout=subprocess.PIPE)
        # Read the output of the processes.
        failures_proc.stdout.read()
        errors_proc.stdout.read()
        # Wait until the processes terminate.
        failures = failures_proc.wait()
        errors = errors_proc.wait()
        # grep returns 1 if the line is not found
        result = bool(failures and errors)
    return result


def _RTCCheckValgrind(env):
    # Path to the valgrind report.
    report_file = os.path.join(env['INSTALL_REPORTS_DIR'], 'valgrind')
    report_file = os.path.join(report_file, env['PROJECT_NAME'])
    report_file = os.path.join(report_file, 'valgrind-report.xml')
    # Open the report
    xml_report = minidom.parse(report_file)
    # Take the tag <errorcounts>.
    element = xml_report.getElementsByTagName('errorcounts')[FIRST_ELEMENT]
    # Take the unicode element.
    element = element.childNodes[FIRST_ELEMENT]
    element = element.nodeValue
    # If the element is empty, there aren't valgrind errors.
    return not element.strip()


def _ExecuteNamecheck(env, files, plugin, conf, includes):
    reg = '(/%s/).*(\[namecheck\])' % env['PROJECT_NAME']
    for x in files.split(SPACE):
        if x.endswith('cpp') or x.endswith('cc'):
            cmd = 'g++'
        elif x.endswith('c'):
            cmd = 'gcc'
        env.Cprint('\nAnalyzing %s...\n' % os.path.basename(x), 'yellow')
        cmd += ' %s %s -c %s %s' % (plugin, conf, x, includes)
        if env.GetOption('verbose'):
            env.Cprint('>>>%s' % cmd, 'end')
        pipe = subprocess.Popen(cmd, stderr=subprocess.PIPE, shell=True)
        for line in pipe.stderr:
            # Check if the project name is into the path of the warning.
            is_there = re.search(reg, line)
            if is_there:
                env.Cprint('%s' % line.strip(), 'end')
        pipe.wait()
        if x.endswith('cpp'):
            try:
                Delete(x.replace('cpp', 'o'))
            except:
                pass
        elif x.endswith('.cc'):
            try:
                os.remove(x.replace('cc', 'o'))
            except:
                pass
        elif x.endswith('.c'):
            try:
                os.remove(x.replace('c', 'o'))
            except:
                pass