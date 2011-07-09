# FuDePan Bolierplate

import os.path
import sys
import subprocess
from termcolor import cprint

class BasePrjDownload(object):
    def __init__(self, env, config):
        self.name = config.path
        self.url = config.url
        self.executeAfter = config.get("executeAfter")
        self.env = env

    def download(self, target):
        return self.fetch(target) and self.afterFetch()

    def afterFetch(self):
        if self.executeAfter:
            executeAfter = self.executeAfter.replace('#', self.env.Dir('#').abspath)
            cprint('About to execute: %s' % executeAfter, 'purple')
            rc = subprocess.call(executeAfter.split(' '))
            if rc != 0 :
                cprint('failed to execute post command: %s' % executeAfter, 'red')
                cprint('error: %s' % rc, 'red')
                return False
        return True

class HG(BasePrjDownload):
    def __init__(self, env, config):
        super(HG, self).__init__(env, config)

    def fetch(self, target):
        cprint('[hg] checkout %s => %s' % (self.url, target), 'purple')
        rc = subprocess.call(['hg', 'clone', self.url, target])
        if rc != 0 :
            cprint('hg failed to retrieve target %s from %s' % (target, self.url), 'red')
            cprint('error: %s' % rc, 'red')
            return False
        return True

class SVN(BasePrjDownload):
    def __init__(self, env, config):
        super(SVN, self).__init__(env, config)

    def fetch(self, target):
        cprint('[svn] checkout %s => %s' % (self.url, target), 'purple')
        rc = subprocess.call(['svn', 'checkout', self.url, target])
        if rc != 0 :
            cprint('svn failed to retrieve target %s from %s' % (target, self.url), 'red')
            cprint('error: %s' % rc, 'red')
            return False
        return True

class WGET(BasePrjDownload):
    def __init__(self, env, config):
        super(WGET, self).__init__(env, config)

    def fetch(self, target):
        cprint('[wget] %s => %s' % (self.url, target), 'purple')
        rc = subprocess.call(['wget', self.url])
        if rc != 0 :
           cprint('wget failed to retrieve target %s from %s' % (target, self.url), 'red')
           cprint('error: %s' % rc, 'red')
           return False
        return True

def downloadDependency(env, name):
    cfg = _loadConfig(env)
    cfg.addNamespace(sys.modules[SVN.__module__])
    prjs = dict([(prj, prjCfg.type(env, prjCfg)) for prj, prjCfg in cfg.iteritems()])
    prj = prjs.get(name)
    if prj:
        ## ask the user if he wants to download it
        cprint('I found the dependency %s located at %s' % (name, prj.url), 'blue')
        cprint('Do you want me to download it? ', 'blue')
        userResponse = raw_input()
        userResponse = userResponse.lower()
        if userResponse in ['y', 'yes', 'yeap', 'ok', 'yeah']:
            compTarget = os.path.join(env['WS_DIR'], name)
            return prj.download(compTarget)
    return False

def _loadConfig(env):
    from config import Config, ConfigMerger
    cfg = Config(os.path.join(env['WS_DIR'], 'projects'))
    cfg.addNamespace(sys.modules[SVN.__module__])

    localCfgPath = os.path.join(env['WS_DIR'], 'projects.local')
    if os.path.exists(localCfgPath):
        localCfg = Config(localCfgPath)
        localCfg.addNamespace(sys.modules[SVN.__module__])
        ConfigMerger(lambda local, cfg, key: "overwrite").merge(cfg, localCfg)
    return cfg

