# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011 Hugo Arregui FuDePAN
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
import sys

BUILD_SCRIPTS_DIR = os.path.join(os.getcwd(), "scons/site_scons")
sys.path.append(BUILD_SCRIPTS_DIR)

import argparse
from subprocess import call
from termcolor import cprint
from tasks import tasks

def invoke_scons(args):
    if args:
        cmd = 'cd scons; scons ' + ' '.join(args)
        call(cmd, shell=True)

def parse_project_arg(arg):
    splitted = arg.split(':')
    return (arg, splitted[0], splitted[1] if len(splitted) > 1 else None)

def find_installed_projects():
    return os.listdir('projects')

parser = argparse.ArgumentParser(description="invokes the fudepan-build system")
parser.add_argument('--type', dest='type', nargs=1, action='store', help='type of build, options: dbg, opt')
parser.add_argument('--efective', dest='commands', help="adds -Weffc flag", action='append_const', const='efective')
parser.add_argument('-l', '--list', dest='commands', help="list projects", action='append_const', const='projects')
parser.add_argument('project', nargs='*', help="use project[:task]. Possibles tasks are: test, clear, clear-test, " + ", ".join(tasks.keys()))
args = parser.parse_args()

missing_args = True

from dependencies import downloadDependency, findLoadableDependencies
deps = findLoadableDependencies({}, "conf")

scons_args = set()

if args.type:
    scons_args.add('--type=%s' % args.type[0])

for command in args.commands or []:
    if command in ['effective']:
        scons_args.add(command)
    if command == 'projects':
        missing_args = False
        print " ".join(deps.keys())

scons_targets = []
env = dict(projects=deps)
for arg in args.project or []:
    missing_args = False
    original, project_name, task = parse_project_arg(arg)
    for project in ([project_name] if project_name != 'all' else find_installed_projects()):
        if task in tasks:
            env['original'] = original
            tasks[task](project, task, env)
        elif task == 'clear':
            scons_args.add('-c')
            scons_targets.append(project)
        elif task == 'clear-test':
            scons_args.add('-c')
            scons_targets.append(project + ':test')
        elif task == 'test':
            if os.path.exists('projects/%s/tests/SConscript' % project):
                scons_targets.append(project + ':test')
        else:
            cmd = original.replace(project_name, project)
            scons_targets.append(cmd)

invoke_scons(list(scons_args) + scons_targets)

if missing_args:
    parser.print_help()
