# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011 Esteban Papp, Hugo Arregui, 2013 Gonzalo Bonigo, FuDePAN
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
    This file contains color settings, pretty messages.

    http://www.scons.org/wiki/ColorBuildMessages
"""


import sys
import os


colors = {}
colors['cyan']   = '\033[96m'
colors['purple'] = '\033[95m'
colors['blue']   = '\033[94m'
colors['green']  = '\033[92m'
colors['yellow'] = '\033[93m'
colors['red']    = '\033[91m'
colors['end']    = '\033[0m'

#If the output is not a terminal, remove the colors
if not sys.stdout.isatty():
   for key, value in colors.iteritems():
      colors[key] = ''

copy_message = '%s[copy] $SOURCES to $TARGETS%s' % (colors['blue'], colors['end'])
compile_source_message = '%s[compiling] $SOURCE%s' % (colors['blue'], colors['end'])
link_program_message = '%s[linking program] $TARGET%s' % (colors['cyan'], colors['end'])
link_library_message = '%s[linking static] $TARGET%s' % (colors['cyan'], colors['end'])
link_shared_library_message = '%s[linking shared] $TARGET%s' % (colors['cyan'], colors['end'])
ranlib_library_message = '%s[indexing] $TARGET%s' % (colors['purple'], colors['end'])
install_message = '%s[installing] $SOURCE => $TARGET%s' % (colors['green'], colors['end'])
qtuic_message = '%s[uic] $SOURCE%s' % (colors['blue'], colors['end'])
qtmoc_message = '%s[moc] $SOURCE%s' % (colors['blue'], colors['end'])


def init(env, args):
    if args.get('VERBOSE') != '1':
        prettyMessages(env)
    env.Cprint = Cprint
    env.cdebug = lambda m: Cprint(m, 'green')
    env.cwarn = lambda m: Cprint(m, 'yellow')
    env.cerror = lambda m: Cprint(m, 'red')
    env.Cformat = Cformat


def ask_user(message, color, alternatives):
    message += ' (' + '/'.join(alternatives) + ')'
    userResponse = None
    while userResponse not in alternatives:
        Cprint(message, color)
        userResponse = raw_input().lower()
    return userResponse


def Cprint(msg, color):
    print(Cformat(msg,color))


def Cformat(msg, color):
    return '%s%s%s' % (colors[color], msg, colors['end'])


def prettyMessages(env):
    # TODO: find a way to change the "Removed" message
    env['COPYSTR'] = copy_message
    env['CCCOMSTR'] = compile_source_message
    env['CXXCOMSTR'] = compile_source_message
    env['SHCCCOMSTR'] = compile_source_message
    env['SHCXXCOMSTR'] = compile_source_message
    env['ARCOMSTR'] = link_library_message
    env['RANLIBCOMSTR'] = ranlib_library_message
    env['SHLINKCOMSTR'] = link_shared_library_message
    env['LINKCOMSTR'] = link_program_message
    env['INSTALLSTR'] =  install_message
    # Qt3
    env['QT_UICCOMSTR'] = qtuic_message
    #env['QT_RCCCOMSTR'] = rcc
    env['QT_MOCFROMHCOMSTR'] = qtmoc_message
    env['QT_MOCFROMCXXCOMSTR'] = qtmoc_message
    #env['QT_LUPDATECOMSTR'] = ts
    #env['QT_LRELEASECOMSTR'] = qm
    # Qt4
    env['QT4_MOCFROMHCOMSTR'] = qtmoc_message
    env['QT4_MOCFROMCXXCOMSTR'] = qtmoc_message
    env['QT4_UICCOMSTR'] = qtuic_message
