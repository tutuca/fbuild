# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011 Esteban Papp, FuDePAN
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
#
# This file was originally taken from the following address:
# http://www.scons.org/wiki/AutomaticHelpFromAliases
# It was modified to suit fudepan-build environment needs

#
# Description: this file does some hooking in the aliasing to create a system
#              of description of the targets
#

from SCons.Script.SConscript import SConsEnvironment
from SCons.Script import *
import SCons.Builder

def addPrintTarget(env, name, action):
    from SCons.Script import Builder
    bld = Builder(action = SCons.Action.Action(action, PrintTargetsDummy))
    builder_name = action.func_name
    env.Append(BUILDERS = {builder_name: bld})
    b = getattr(env, builder_name)('dummy', 'SConstruct')
    env.AlwaysBuild(env.HookedAlias(name, b))

def init(env):
    SConsEnvironment.HookedAlias = env.Alias
    SConsEnvironment.AliasHelpData = AliasHelpData()
    SConsEnvironment.Alias = AliasHelp
    SConsEnvironment.AddAliasDescription = AddAliasDescription
    addPrintTarget(env, 'targets', PrintTargets)
    addPrintTarget(env, 'help', PrintFbuildHelp)

class AliasHelpData:
    mHelpText = {}
    mHelpTextHead = []
    mHelpTextTail = []

def AliasHelp(env, aliasname, tgt, helptext=None):
    env.AddAliasDescription(aliasname, helptext)
    return env.HookedAlias(aliasname, tgt)

def AddAliasDescription(env, aliasname, helptext=None):
    if helptext is None:
        if not env.AliasHelpData.mHelpText.has_key(aliasname):
            env.AliasHelpData.mHelpText[aliasname] = 'No description provided'
    else:
        env.AliasHelpData.mHelpText[aliasname] = helptext

def PrintTargetsDummy(env, source, target):
    return ""

def PrintTargets(env, source, target):
    print 'Targets:'
    keys = env.AliasHelpData.mHelpText.keys()
    keys.sort()
    maxlen = 0
    for a in keys:
        if len(a) > maxlen: maxlen = len(a)
    for a in keys:
        s = ' %-*s : %s' % (maxlen, a, env.AliasHelpData.mHelpText[a])
        print s

def PrintFbuildHelp(env, source, target):
    print """
usage: fbuild [help] [--type TYPE] [--efective] [target [target ...]]

invokes the fudepan-build system

positional arguments:
    target           use project[:task]. Possibles tasks are: test, astyle. Or use 'targets' to list the possible targets

optional arguments:
    help             show this help message and exit
    --type TYPE      type of build, options: dbg, opt
    --efective       adds -Weffc flag
"""
