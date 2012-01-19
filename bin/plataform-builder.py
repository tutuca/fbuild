# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2012 Hugo Arregui FuDePAN
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
from os.path import join

BASE_PATH = 'projects'
set_name = None

def write_sconscript(path, data):
    data['ext_inc'] = ('\next_inc = ' + data['ext_inc']) if 'ext_inc' in data else ''
    scons_data = """\
Import ('env')

name = %(name)s
inc = %(inc)s %(ext_inc)s
src = %(src)s
deps = %(deps)s

%(command)s
""" % data
    sconscript = open(path, 'w')
    sconscript.write(set_name(scons_data))
    sconscript.close()

def setupCore(project_dir):
    os.makedirs(join(project_dir, 'core', set_name('${project}-core')))
    os.makedirs(join(project_dir, 'core', 'src'))
    write_sconscript(join(project_dir, 'core', 'SConscript'), {
        'name'   : '${project}-core', 
        'inc'    : "env.Dir('.')", 
        'ext_inc': "env.Dir('${project}-core')", 
        'src'    : "env.Glob('src/*.cpp')", 
        'deps'   : "['mili', 'unplugged']", 
        'command': 'env.CreateSharedLibrary(name, inc, ext_inc, src, deps)'
        })

def setupFrontend(project_dir):
    os.makedirs(join(project_dir, 'frontend'))

def setupSDK(project_dir):
    os.makedirs(join(project_dir, 'sdk', 'libplugin', set_name('libplugin${project}')))
    os.makedirs(join(project_dir, 'sdk', 'libplugin', 'src'))
    write_sconscript(join(project_dir, 'sdk', 'libplugin', 'SConscript'), {
        'name'   : 'libplugin${project}',
        'inc'    : "env.Dir('.')", 
        'ext_inc': "env.Dir('libplugin${project}')",
        'src'    : "env.Glob('src/*.cpp')", 
        'deps'   : "['mili', '${project}-core']",
        'command': 'env.CreateSharedLibrary(name, inc, ext_inc, src, deps)'
        })
    os.makedirs(join(project_dir, 'sdk', 'plugin_example'))
    write_sconscript(join(project_dir, 'sdk', 'plugin_example', 'SConscript'), {
        'name'   : '${project}-example-plugin',
        'inc'    : "env.Dir('.')", 
        'src'    : "env.Glob('src/*.cpp')", 
        'deps'   : "['mili', 'libplugin${project}']",
        'command': 'env.CreateSharedLibrary(name, inc, [], src, deps)'
        })

def main():
    import argparse
    parser = argparse.ArgumentParser(description="plataform project builder for fudepan-build system")
    parser.add_argument('project', type=str, metavar='project', help="project name")
    args = parser.parse_args()

    project = args.project
    project_dir = join(BASE_PATH, project)
    if not os.path.exists(project_dir):
        global set_name
        set_name = lambda t: t.replace('${project}', project)
        setupCore(project_dir)
        setupFrontend(project_dir)
        setupSDK(project_dir)
    else:
        print "%s already exists" % project_dir

if __name__ == "__main__":
    main()
