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
import os.path
import shutil
import os
from SCons.Builder import Builder
from SCons.Action import Action

from utils import ChainCalls


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
    env['VALGRIND_OPTIONS'] = ' --leak-check=full --show-reachable=yes ' + \
                              '--error-limit=no --track-origins=yes'
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
    bldCppCheck = Builder(action=Action(RunCppCheck, PrintDummy))
    env.Append(BUILDERS={'RunCppCheck': bldCppCheck})
    env['CPPCHECK_OPTIONS'] = [' --enable=all ']
    #-
    bldMocko = Builder(action=Action(RunMocko, PrintDummy))
    env.Append(BUILDERS={'RunMocko': bldMocko})
    #-
    bldReadyToCommit = Builder(action=Action(RunReadyToCommit, PrintDummy))
    env.Append(BUILDERS={'RunReadyToCommit': bldReadyToCommit})
    #-
    bldInfo = Builder(action=Action(RunInfo, PrintDummy))
    env.Append(BUILDERS={'RunInfo': bldInfo})
	#-
    bldStaticAnalysis = Builder(action=Action(RunStaticAnalysis, PrintDummy))
    env.Append(BUILDERS={'RunStaticAnalysis': bldStaticAnalysis})


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
        cmd = "cd %s; gdb -x mocko_bind.gdb %s" % (test_dir, test_program)
    else:
        cmd = "cd %s; ./%s --gtest_filter=%s" % (test_dir, test_program, test_suite)
    # Execute the test.
    test_proc = subprocess.Popen(cmd, shell=True)
    if test_proc.wait():
        env.cerror('\n\nTest result: *** FAILED ***\n\n')
    else:
        env.Cprint('\n\nTest result: *** PASSED ***\n\n', 'green')
    return test_proc.wait()


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
    return result


def RunLcov(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running COVERAGE ===\n', 'green')
    indexFile = target[0].abspath
    data = {
        'coverage_file': os.path.join(os.path.dirname(os.path.dirname(indexFile)), 'coverage_output.dat'),
        'output_dir': os.path.dirname(indexFile),
        'project_dir': env['PROJECT_DIR']
    }
    commands_list = [
        'rm -f %(coverage_file)s' % data,
        'lcov --no-checksum --directory %(project_dir)s -b . --capture --output-file %(coverage_file)s' % data,
        'lcov --no-checksum --directory %(project_dir)s -b . --capture --output-file %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*usr/include*" -o %(coverage_file)s' % data,
        'lcov --remove %(coverage_file)s "*/tests/*" -o %(coverage_file)s' % data
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
    if not env.GetOption('verbose'):
        doxygen_results_proc = subprocess.Popen("cat %s" % output_file, shell=True)
        doxygen_results_proc.wait()
    os.remove(projectDoxyFile)
    return rc


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
            report.write(info + '\n\n')
            # Print on the screen.
            env.Cprint('====> %s' % f, 'red')
            env.Cprint(info, 'yellow')
    else:
        env.Cprint('[OK] No file needs astyle.', 'green')
    # Close the report file.
    report.close()
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
    file_list = ' '.join([f.abspath.replace(build_dir, ws_dir) for f in source if "tests/ref/" not in f.abspath])
    # Create the command to be executed.
    cmd = "astyle -k1 --options=none --convert-tabs -bSKpUH %s" % file_list
    # Run astyle.
    astyle_proc = subprocess.Popen(cmd, shell=True)
    if astyle_proc.wait() != 0:
        env.cerror('[astyle] ERROR running astyle on: %s' % project_dir)
    else:
        env.Cprint('[astyle] OK on: %s' % project_dir, 'green')
    return astyle_proc.wait()


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
    return pdflates_proc.wait()


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
    valgrind_proc = subprocess.Popen(cmd, shell=True)
    # Get back to the previous directory.
    os.chdir(cwd)
    return valgrind_proc.wait()


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
    options = ' '.join([opt for opt in env['CCCC_OPTIONS']])
    # Create a string with the file names for cccc.
    files = ' '.join([f.abspath for f in source])
    # Create the command to be executed.
    cmd = 'cccc %s %s' % (options, files)
    cccc_proc = subprocess.Popen(cmd, shell=True)
    return cccc_proc.wait()


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
    options = ' '.join([opt for opt in env['CLOC_OPTIONS']])
    # Create a string with the file names for cloc.
    files = ' '.join([f.abspath for f in source])
    # Create the command to be executed.
    cmd = 'cloc %s %s' % (options, files)
    cloc_proc = subprocess.Popen(cmd, shell=True)
    return cloc_proc.wait()


def RunCppCheck(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running CPPCHECK ===\n', 'green')
    # Get the report file name.
    report_file = target[0].abspath
    # Get the output directory.
    output_directory = os.path.dirname(report_file)
    # Check if the output directory for the cppcheck report already exists.
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    # Create a string with the options for cppcheck.
    options = ' '.join([opt for opt in env['CPPCHECK_OPTIONS']])
    # We create a string with the files for cppcheck.
    files = ' '.join([f.abspath for f in source])
    # Create the command to be pass to subprocess.call()
    return _RunCppCheck(target, files, options)

def RunStaticAnalysis(env, target, source):
    # Print message on the screen.
    cppcheck_rc = False
    splint_rc = False
    env.Cprint('\n=== Running Static Code Analysis ===\n', 'green')
    target_name = target[0].name
    cppcheck_report = target_name + '-cpp'
    cppcheck_options = ' '.join([opt for opt in env['CPPCHECK_OPTIONS']])
    splint_report = target_name + '-c'
    cpp_files = _FindSources(source, ['.cpp', '.cc'])
    c_files = _FindSources(source, ['.c'])
    headers = _FindHeaders(source)
    if cpp_files:
        cppcheck_rc = _RunCppCheck(cppcheck_report, cpp_files, headers, 
            cppcheck_options)
    if c_files:
        splint_rc = _RunSplint(splint_report, c_files, headers)
    if headers and not (cpp_files or c_files):
        #headers only
        cppcheck_rc = _RunCppCheck(cppcheck_report, _FindSources(source, 
            ['.h', '.hh', '.hpp']), headers, cppcheck_options)
    # Return the output of both builders
    return cppcheck_rc and splint_rc


def RunMocko(env, target, source):
    # Print message on the screen.
    env.Cprint('\n=== Running MOCKO ===\n', 'green')
    verbose = not env.GetOption('verbose')
    # Get the file list.mocko.
    mocko_list = source[0].abspath
    # Get the tests directory.
    directory = os.path.split(mocko_list)[0]
    # The mocko executable file.
    mocko = env.Dir('$INSTALL_BIN_DIR').File('mocko').abspath
    # Get current directory.
    cwd = env.Dir('#').abspath
    # Print info.
    if verbose:
        print "> chdir", directory
        print '> %s %s' % (mocko, mocko_list)
        print "> chdir", cwd
    # Execute mocko.
    os.chdir(directory)
    mocko_proc = subprocess.Popen('%s %s' % (mocko, mocko_list), shell=True)
    os.chdir(cwd)
    return mocko_proc.wait()


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
    print ""  # Just an empty line.
    return 0

def _RunCppCheck(report_file, files, headers, options):
    if 'xml' in options:
        cmd = "cppcheck --check-config %s %s %s 2> %s.xml" % (options, files, 
            headers, report_file)
    else:
        cmd = "cppcheck %s %s %s 2> %s.txt" % (options, files, 
            headers, report_file)
    print cmd
    cppcheck_proc = subprocess.Popen(cmd, shell=True)
    return cppcheck_proc.wait()

def _RunSplint(report_file, files, headers):
    cmd = "splint %s %s > %s.txt" % (files, headers, report_file)
    splint_proc = subprocess.Popen(cmd, shell=True)
    return splint_proc.wait()

def RunInfo(env, target, source):
    #Take project info
    name = target[0].name
    project_type = env['PROJECT_TYPE']
    # Print the project info
    env.Cprint("\n----------- %s -----------\n" % name, "blue")
    env.CprintSameLine([("The Project type is: ", "end"), ("%s \n" % project_type, "green")])
    # Separate sources and headers
    headers_list = [x.name for x in source for y in HEADERS if x.name.endswith(y)]
    sources_list = [x.name for x in source for y in SOURCES if x.name.endswith(y)]
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
    files_str = ' '.join([x.abspath for x in files_list])
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
    if astyle_proc.wait() != 0:
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
    cmd = "cat %s | grep -E '^\+' | grep -v +++ | grep -v 'for (auto'" % report_file
    # Execute the command.
    astyle_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    # Read the output of the process.
    astyle_proc.stdout.read()
    # Wait until process terminates and return the status.
    return astyle_proc.wait() != 0


def _RTCCheckCppcheck(env):
    # Path to the report file.
    report_file = os.path.join(env['INSTALL_REPORTS_DIR'], 'cppcheck')
    report_file = os.path.join(report_file, env['PROJECT_NAME'])
    report_file = os.path.join(report_file, 'CppcheckReport.xml')
    # Commands to be executed.
    cmd_error = 'cat %s | grep severity=\\"error\\"' % report_file
    cmd_warning = 'cat %s | grep severity=\\"warning\\"' % report_file
    # Execute the commands.
    errors_proc = subprocess.Popen(cmd_error, shell=True, stdout=subprocess.PIPE)
    warnings_proc = subprocess.Popen(cmd_warning, shell=True, stdout=subprocess.PIPE)
    # Read the output of the processes.
    errors_proc.stdout.read()
    warnings_proc.stdout.read()
    # Wait until the processes terminate.
    errors = errors_proc.wait() != 0
    warnings = warnings_proc.wait() != 0
    return errors and warnings


def _RTCCheckTests(env):
    # Path to the report file.
    report_file = os.path.join(env['INSTALL_REPORTS_DIR'], 'test')
    report_file = os.path.join(report_file, env['PROJECT_NAME'])
    report_file = os.path.join(report_file, 'test-report.xml')
    # Commands to be executed.
    cmd_failures = 'cat %s | grep "<testsuites" | grep -v "failures=\\"0\\""' % report_file
    cmd_errors = 'cat %s | grep "<testsuites" | grep -v "errors=\\"0\\""' % report_file
    # Execute the commands.
    failures_proc = subprocess.Popen(cmd_failures, shell=True, stdout=subprocess.PIPE)
    errors_proc = subprocess.Popen(cmd_errors, shell=True, stdout=subprocess.PIPE)
    # Read the output of the processes.
    failures_proc.stdout.read()
    errors_proc.stdout.read()
    # Wait until the processes terminate.
    failures = failures_proc.wait() != 0
    errors = errors_proc.wait() != 0
    return failures and errors


def _RTCCheckValgrind(env):
    # Path to the valgrind report.
    report_file = os.path.join(env['INSTALL_REPORTS_DIR'], 'valgrind')
    report_file = os.path.join(report_file, env['PROJECT_NAME'])
    report_file = os.path.join(report_file, 'valgrind-report.xml')
    # Command to be executed.
    cmd = "cat %s | grep '<error>'" % report_file
    # Execute the command.
    valgrind_proc = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE)
    # Read the output of the process.
    valgrind_proc.stdout.read()
    # Wait until process terminates and return the status.
    return valgrind_proc.wait() != 0

def _FindSources(dirs, extensions, spacer=' '):
    out = []
    
    for source in dirs:
        name, ext = os.path.splitext(source.name)
        if ext in extensions:
            out.append(source.abspath)
    
    return ' '.join(out)

def _FindHeaders(dirs):
    out = []
    for source in dirs:
        name, ext = os.path.splitext(source.name)
        if ext in ['.h', '.hh', '.hpp']:
            dirname = os.path.dirname(source.abspath)
            if dirname not in out:
                out.append(dirname)
    return ''.join('-I%s ' %x for x in out)