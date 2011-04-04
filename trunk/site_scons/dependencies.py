# FuDePan Bolierplate

import os.path
import sys
import subprocess
from termcolor import cprint

def HgGetDownload(target, source):
    cprint('[hg] checkout %s => %s' % (source,target),'purple')
    rc = subprocess.call(['hg', 'clone', source, target])
    if rc != 0 :
        cprint('hg failed to retrieve target %s from %s' % (target,source),'red')
        cprint('error: %s' % rc, 'red')
        return False
    return True

def SVNGetDownload(target, source):
    cprint('[svn] checkout %s => %s' % (source,target),'purple')
    rc = subprocess.call(['svn', 'checkout', source, target])
    if rc != 0 :
        cprint('svn failed to retrieve target %s from %s' % (target,source), 'red')
        cprint('error: %s' % rc, 'red')
        return False
    return True


def WGetDownload(target, source):
    cprint('[wget] %s => %s' % (source,target), 'purple')
    rc = subprocess.call(['wget', source])
    if rc != 0 :
       cprint('wget failed to retrieve target %s from %s' % (target,source), 'red')
       cprint('error: %s' % rc, 'red')
       return False
    return True

def downloadDependency(env,name):
    found = False
    projectsFile = os.path.join(env['WS_DIR'],'projects')
    f = open(projectsFile,'r')
    for line in f:
        (compname, repoType, url, executeAfter) = line.split('|')
        executeAfter = executeAfter.rstrip()
        if compname == name:
            compTarget = os.path.join(env['WS_DIR'],compname)
            # ask the user if he wants to download it
            cprint('I found the dependency %s located at %s' % (name,url),'blue')
            cprint('Do you want me to download it? ','blue')
            userResponse = raw_input()
            userResponse = userResponse.lower()
            if userResponse == 'y' or userResponse == 'yes' or userResponse == 'yeap' or userResponse == 'ok' or userResponse == 'yeah':
                result = False
                if repoType == 'wget':
                    result = WGetDownload(compTarget,url)
                elif repoType == 'svn':
                    result = SVNGetDownload(compTarget,url)
                elif repoType == 'hg':
                    result = HgGetDownload(compTarget,url)
                else:
                    raise Exception('Unknown protocol type to download component %s' % name)
                if result:
                   found = True
                   if executeAfter != '':
                       executeAfter = executeAfter.replace('#',env.Dir('#').abspath)
                       cprint('About to execute: %s' % executeAfter, 'purple')
                       rc = subprocess.call(executeAfter.split(' '))
                       if rc != 0 :
                           cprint('failed to execute post command: %s' % executeAfter, 'red')
                           cprint('error: %s' % rc, 'red')
                           return False
            break
    f.close()
    return found
