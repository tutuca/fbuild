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

import os
import shutil

import subprocess

from termcolor import Cprint, Cformat
from SCons.Action import Action
from SCons.Builder import Builder
from SCons.Warnings import Warning, enableWarningClass
from SCons.Errors import StopError


class ToolAstyleWarning(Warning):
    '''Astyle-specific Warnings'''
    pass


class AstyleCompilerNotFound(ToolAstyleWarning):
    '''
    Raise this warning if the astyle excecutable is not found in the system
    '''
    pass

enableWarningClass(ToolAstyleWarning)


def _get_astyle_diff(env, source, output_directory):
    '''
    This runs astyle on a temporary file and prints the diff out to 
    standard output
    '''

    # Create a temporary directory.
    # This variable holds if some file needs astyle.
    need_astyle_list = []
    # The list of copied files.
    files_list = []
    tmp_dir = os.path.join(output_directory, 'tmp')
    if not os.path.exists(tmp_dir):
        os.makedirs(tmp_dir)

    # Copy all sources into the temporary directory.
    for file in source:
        if "tests/ref/" not in file.abspath:  # TODO: Remove this line.
            shutil.copy(file.abspath, tmp_dir)
            f = env.Dir(tmp_dir).File(os.path.split(file.abspath)[1])
            files_list.append(f)
    files_str = ' '.join([x.abspath for x in files_list])
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
            need_astyle_list.append(
                (os.path.split(file.abspath)[1], diff_stdout))
    # Remove the temporary directory.
    os.system('rm -rf %s' % tmp_dir)
    # Return a dictionary.
    return need_astyle_list


def _astyle_check_action(target, source, env):
    '''This prepares the environment for _astyle_check_diff to run'''
    # Get the report file.
    report_file = target[0].abspath
    # Get the output directory.
    output_directory = os.path.split(report_file)[0]
    # Check if the directory exists.
    if not source:
        raise StopError('[ERROR] No source files to check')
    if not os.path.exists(output_directory):
        os.makedirs(output_directory)
    # Check if some file need astyle.
    check_astyle_result = _get_astyle_diff(env, source, output_directory)
    # Check if _get_astyle_diff() fails.
    if check_astyle_result is None:
        raise StopError('[ERROR] Failed running Astyle Check.')
    # Open the report file.
    try:
        report = open(report_file, 'w')
    except IOError:
        raise StopError('[ERROR] No such file or directory.')
    else:
        # If we can open it we truncate it.
        report.truncate(0)
    # If some file needs astyle we print info.
    if check_astyle_result:
        # Print a warning message.
        Cprint('[WARNING] The following files need astyle:', 'yellow')
        # Print what need to be astyled.
        for f, info in check_astyle_result:
            # Write into hte report file.
            report.write(info + '\n\n')
            # Print on the screen.
            Cprint('====> %s' % f, 'yellow')
            Cprint(info, 'yellow')
    else:
        Cprint('[OK] No file needs astyle.', 'green')
    # Close the report file.
    report.close()
    return os.EX_OK


def _detect(env):
    """ Helper function to detect the astyle excecutable."""


    astyle = env.get('ASTYLE', env.WhereIs('astyle'))
    if astyle:
        return astyle
    else:
        raise StopError(
            AstyleCompilerNotFound,
            "Could not detect ASTYLE")  # surely we could detect the platform 
                                        # and install the package here...


def _astyle_emitter(target, source, env):
    '''Helper function to filter out files for testing purposes.'''
    filtered_sources = []
    fs_append = filtered_sources.append
    for f in source:
        if 'test/ref' not in f.abspath:
            f = f.abspath.replace(env['BUILD_DIR'], env['WS_DIR']) 
            if os.path.exists(f):
                fs_append(f)
    return target, filtered_sources

_astyle_builder = Builder(
    action=Action('$ASTYLE_COM', '$ASTYLE_COMSTR'),
    emitter=_astyle_emitter)

_astyle_check_builder = Builder(
    action=Action(_astyle_check_action, '$ASTYLE_CHECK_COMSTR'),
    emitter=_astyle_emitter)


def generate(env):
    """Add Builders and construction variables to the Environment."""
    env['ASTYLE'] = _detect(env)
    env.SetDefault(
        # ASTYLE command
        ASTYLE_COM='$ASTYLE -k1 --options=none --convert-tabs -bSKpUH $SOURCES',
        ASTYLE_COMSTR=Cformat('\n=== Running Astyle ===\n', 'green'),
        ASTYLE_CHECK_COMSTR=Cformat('\n=== Running Astyle Check ===\n', 'green')
    )

    env['BUILDERS']['RunAStyle'] = _astyle_builder
    env.AddMethod(_astyle_check_builder, 'RunAStyleCheck')


def exists(env):
    return _detect(env)
