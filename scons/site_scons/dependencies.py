# fudepan-build: The build system for FuDePAN projects 
#
# Copyright (C) 2011 Esteban Papp, Hugo Arregui FuDePAN
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

# FuDePan Bolierplate

import os.path
import sys
import subprocess
from termcolor import cprint, ask_user

class BasePrjDownload(object):
    def __init__(self, name, env, config):
        self.name = name
        self.url = config.url
        self.executeAfter = config.get("executeAfter")
        self.env = env
        self.username = config.get("username")

    def download(self, target):
        s = self.fetch(target) and self.afterFetch()
        if s:
            self.target = target
        return s

    def afterFetch(self):
        if self.executeAfter:
            cmds = [self.executeAfter] if isinstance(self.executeAfter, str) else self.executeAfter
            for cmd in cmds:
                if not self.executeCmd(cmd):
                    return False
        return True
                
    def executeCmd(self, cmd):
        cmd = cmd.replace('#external', self.env.Dir('#/site_scons/external').abspath)\
                 .replace('#projects',self.env['WS_DIR'])\
                 .replace('#',self.env.Dir('#').abspath)
        print cmd
        cprint('About to execute: %s' % cmd, 'purple')
        rc = subprocess.call(cmd.split(' '))
        success = rc == 0
        if not success:
            cprint('failed to execute post command: %s' % cmd, 'red')
            cprint('error: %s' % rc, 'red')
        return success

class HG(BasePrjDownload):
    def fetch(self, target):
        cprint('[hg] checkout %s => %s' % (self.url, target), 'purple')
        rc = subprocess.call(['hg', 'clone', self.url, target])
        if rc != 0 :
            cprint('hg failed to retrieve target %s from %s' % (target, self.url), 'red')
            cprint('error: %s' % rc, 'red')
            return False
        return True

class SVN(BasePrjDownload):
    def fetch(self, target):
        cprint('[svn] checkout %s => %s' % (self.url, target), 'purple')
        cmd = ['svn', 'checkout'] + (['--username', self.username] if self.username else []) +  [self.url, target]
        rc = subprocess.call(cmd)
        if rc != 0 :
            cprint('svn failed to retrieve target %s from %s' % (target, self.url), 'red')
            cprint('error: %s' % rc, 'red')
            return False
        return True

class WGET(BasePrjDownload):
    def fetch(self, target):
        cprint('[wget] %s => %s' % (self.url, target), 'purple')
        rc = subprocess.call(['wget', self.url, '-P', target])
        if rc != 0 :
           cprint('wget failed to retrieve target %s from %s' % (target, self.url), 'red')
           cprint('error: %s' % rc, 'red')
           return False
        return True

def downloadDependency(env, dep):
    if dep:
        ## ask the user if he wants to download it
        userResponse = ask_user("""\
I found the dependency %s located at %s
Do you want me to download it?""" % (dep.name, dep.url), 'blue', ['y', 'n'])
        if userResponse == 'y':
            compTarget = os.path.join(env['WS_DIR'], dep.name)
            return dep.download(compTarget)
    return False

def findLoadableDependencies(env):
    from config import Config, ConfigMerger
    cfg = Config(env.File('#/../conf/projects').abspath)
    cfg.addNamespace(sys.modules[SVN.__module__])

    localCfgPath = env.File('#/../conf/projects.local').abspath
    if os.path.exists(localCfgPath):
        localCfg = Config(localCfgPath)
        localCfg.addNamespace(sys.modules[SVN.__module__])
        ConfigMerger(lambda local, cfg, key: "overwrite").merge(cfg, localCfg)
    return dict([(prj, prjCfg.type(prj, env, prjCfg)) for prj, prjCfg in cfg.iteritems()])

