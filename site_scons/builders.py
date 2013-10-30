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
    Add description here!
"""


import subprocess
import os.path
import shutil
import os
from SCons.Builder import Builder
from SCons.Action import Action

from utils import ChainCalls, FindHeaders, FindSources, CheckPath, WaitProcessExists, RemoveDuplicates


HEADERS = [".h", ".hpp"]
SOURCES = [".c", ".cpp"]
# Return status of a builder.
EXIT_SUCCESS = 0
# Constat to repsent spaces between options.
SPACE = ' '
# The first element of an iterable object.
FIRST_ELEMENT = 0


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
    bldAStyleCheck = Builder(action=Action(AStyleCheck, PrintDummy))
    env.Append(BUILDERS={'RunAStyleCheck': bldAStyleCheck})
    #-
    bldAStyle = Builder(action=Action(AStyle, PrintDummy))
    env.Append(BUILDERS={'RunAStyle': bldAStyle})
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
    env['CPPCHECK_OPTIONS'] = ['-f', '--enable=all', '--check-config']
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


def PrintDummy(env, target, source):
    return ""


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
    result = ChainCalls(env, [
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
        'lcov --no-checksum --directory %(project_dir)s -b . --capture --ignore-error source --output-file %(coverage_file)s' % data,
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
    result = ChainCalls(env, commands_list, env.GetOption('verbose'))
    if result:
        env.cerror('\n\n[ERROR] Failed running Lcov, error: %s\n\n' % result)
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


def AStyleCheck(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running ASTYLE-CHECK ===\n', 'green')
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
        env.cerror('\n\n[ERROR] Failed running Check Astyle\n\n')
        return EXIT_SUCCESS
    # Open the report file.
    try:
        report = open(report_file, 'w')
    except IOError:
        env.Cprint('No such file or directory:', report_file)
        return EXIT_SUCCESS
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
            report.write(info + '\n\n')
            # Print on the screen.
            env.Cprint('====> %s' % f, 'red')
            env.Cprint(info, 'yellow')
    else:
        env.Cprint('[OK] No file needs astyle.', 'green')
    # Close the report file.
    report.close()
    return EXIT_SUCCESS


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
    file_list = SPACE.join([f.abspath.replace(build_dir, ws_dir) for f in source if "tests/ref/" not in f.abspath])
    # Create the command to be executed.
    cmd = "astyle -k1 --options=none --convert-tabs -bSKpUH %s" % file_list
    # Run astyle.
    astyle_proc = subprocess.Popen(cmd, shell=True)
    if astyle_proc.wait():
        env.cerror('[astyle] ERROR running astyle on: %s' % project_dir)
    else:
        env.Cprint('[astyle] OK on: %s' % project_dir, 'green')
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
    WaitProcessExists(valgrind_proc.pid)
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
    # Print message on the screen.
    cppcheck_rc = False
    splint_rc = False
    target = target.pop()
    env.Cprint('\n=== Running Static Code Analysis ===\n', 'green')
    cppcheck_options = SPACE.join([opt for opt in env['CPPCHECK_OPTIONS']])
    cpp_files = FindSources(source, ['.cpp', '.cc'])
    cppcheck_dir = target.Dir('cppcheck')
    splint_dir = target.Dir('splint')
    c_files = FindSources(source, ['.c'])
    headers = FindHeaders(source)
    if cpp_files:
        CheckPath(cppcheck_dir.abspath)
        cppcheck_rc = _RunCppCheck(cppcheck_dir, cpp_files, headers, 
            cppcheck_options, env)
    if c_files:
        CheckPath(splint_dir.abspath)
        splint_rc = _RunSplint(splint_dir, c_files, headers)
    if headers and not (cpp_files or c_files):
        CheckPath(cppcheck_dir.abspath)
        cppcheck_rc = _RunCppCheck(cppcheck_dir, FindSources(source, 
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
    MOCKO_BIND_VGDB = 0; MOCKO_BIND_GDB = 1
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
        env.Cprint('TESTE    : [ERROR]', 'red')
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
    headers_list = sorted(RemoveDuplicates([x for x in source for y in HEADERS if x.name.endswith(y)]))
    sources_list = sorted(RemoveDuplicates([x for x in source for y in SOURCES if x.name.endswith(y)]))
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


def _RunCppCheck(report_dir, files, headers, options, env):
    report_file = os.path.join(report_dir.abspath, 'static-analysis-report')
    success = False
    if 'xml' in options:
        report_file = report_file+'.xml'
        cmd = "cppcheck --check-config %s %s %s 2" % (options, files, headers)
    else:
        report_file = report_file+'.txt'
        cmd = "cppcheck %s %s %s" % (options, files, headers)
    if env.GetOption('verbose'):
        env.Cprint('>>> %s' % cmd, 'end')
    import ipdb; ipdb.set_trace()
    with open(report_file, 'w+') as rf:
        pipe = subprocess.Popen(
            cmd, 
            shell=True, 
            stderr=rf
        )
        success = pipe.wait()
    return success

def _RunSplint(report_dir, files, headers):
    report_file = os.path.join(report_dir.abspath, 'static-analysis-report')
    cmd = "splint %s %s > %s.txt" % (files, headers, report_file)
    splint_proc = subprocess.Popen(cmd, shell=True)
    return splint_proc.wait()

def _CheckAstyle(env, source, output_directory):
    # Create a temporary directory.
    tmp_dir = os.path.join(output_directory, 'tmp')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)
    # The list of copied files.
    files_list = []
    # Copy all sources into the temporary directory.
    for file in source:
        if "tests/ref/" not in file.abspath:  # TODO: Remove this line.
            os.system('cp %s %s' % (file.abspath, tmp_dir))
            f = env.Dir(tmp_dir).File(os.path.split(file.abspath)[1])
            files_list.append(f)
    files_str = SPACE.join([x.abspath for x in files_list])
    # This variable holds if some file needs astyle.
    need_astyle = False
    # A list for the files that needs astyle.
    need_astyle_list = []
    # Create the command to be executed.
    cmd = 'astyle -k1 --options=none --convert-tabs -bSKpUH %s' % files_str
    # To see if a file needs astyle we first apply astyle to the file and
    # check if it suffer some change.
    astyle_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    astyle_proc.stdout.read()
    if astyle_proc.wait():
        # If astyle fails, we fail.
        return None
    # Check if astyle did some modifications.
    for file in files_list:
        # If the '.orig' file exists for the file then it was modify by astyle.
        if os.path.exists('%s.orig' % file.abspath):
            # Print the differences between files.
            cmd = 'diff -Nau %s.orig %s' % (file.abspath, file.abspath)
            diff = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
            diff_stdout = diff.stdout.read()
            diff.wait()
            need_astyle_list.append((os.path.split(file.abspath)[1], diff_stdout))
            need_astyle = True
    # Remove the temporary directory.
    os.system('rm -rf %s' % tmp_dir)
    # Return a dictionary.
    return {'need_astyle': need_astyle, 'need_astyle_list': need_astyle_list}


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
    return errors and warnings


def _RTCCheckTests(env):
    # Path to the report file.
    report_file = os.path.join(env['INSTALL_REPORTS_DIR'], 'test')
    report_file = os.path.join(report_file, env['PROJECT_NAME'])
    report_file = os.path.join(report_file, 'test-report.xml')
    # Commands to be executed.
    cmd_failures = 'grep "<testsuites" %s | grep -v "failures=\\"0\\""' % report_file
    cmd_errors = 'grep "<testsuites" %s | grep -v "errors=\\"0\\""' % report_file
    # Execute the commands.
    failures_proc = subprocess.Popen(cmd_failures, shell=True, stdout=subprocess.PIPE)
    errors_proc = subprocess.Popen(cmd_errors, shell=True, stdout=subprocess.PIPE)
    # Read the output of the processes.
    failures_proc.stdout.read()
    errors_proc.stdout.read()
    # Wait until the processes terminate.
    failures = failures_proc.wait()
    errors = errors_proc.wait()
    # grep returns 1 if the line is not found
    return failures and errors


def _RTCCheckValgrind(env):
    # Path to the valgrind report.
    report_file = os.path.join(env['INSTALL_REPORTS_DIR'], 'valgrind')
    report_file = os.path.join(report_file, env['PROJECT_NAME'])
    report_file = os.path.join(report_file, 'valgrind-report.xml')
    # Command to be executed.
    cmd = "grep '<error>' %s " % report_file
    # Execute the command.
    valgrind_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    # Read the output of the process.
    valgrind_proc.stdout.read()
    # Wait until process terminates and return the status.
    # grep returns 1 if the line is not found
    return valgrind_proc.wait()
