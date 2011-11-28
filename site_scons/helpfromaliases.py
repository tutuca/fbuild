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

from SCons.Script.SConscript import SConsEnvironment

#-- ------------------
#-- jDataClass holds data for the helper functions
class jDataClass:
    mHelpText = {}
    mHelpTextHead = []
    mHelpTextTail = []
SConsEnvironment.jData = jDataClass()

#-- ------------------
#-- wraps Alias to put the alias name in the help text
def jAlias(self, aliasname, tgt, helptext=None):
    thealias = self.Alias(aliasname, tgt)
    lcaliasname = aliasname.lower()
    if helptext is None:
        if not self.jData.mHelpText.has_key(lcaliasname):
            self.jData.mHelpText[lcaliasname] = '???'
    else:
        self.jData.mHelpText[lcaliasname] = helptext
    return thealias
SConsEnvironment.jAlias = jAlias

#-- ------------------
#-- adds a line of text to the help heading
def jHelpHead(self, msg):
    self.jData.mHelpTextHead.append(msg);
SConsEnvironment.AliasesHelpHead = jHelpHead

#-- ------------------
#-- adds a line of text to the help footing
def jHelpFoot(self, msg):
    self.jData.mHelpTextTail.append(msg);
SConsEnvironment.AliasesHelpFoot = jHelpFoot

#-- ------------------
#-- generates the help
def jGenHelp(self, target, source, env):
    for head in env.jData.mHelpTextHead:
        print head
    keys = env.jData.mHelpText.keys()
    keys.sort()
    maxlen = 0
    for a in keys:
        if len(a) > maxlen: maxlen = len(a)
    for a in keys:
        s = ' %-*s : %s' % (maxlen, a, env.jData.mHelpText[a])
        print s
    for tail in env.jData.mHelpTextTail:
        print tail
SConsEnvironment.AliasesGenHelp = jGenHelp

