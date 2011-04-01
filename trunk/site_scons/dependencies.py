# FuDePan Bolierplate

import os.path
import sys
import subprocess

def SVNGetDownload(target, source):
    print '[svn] checkout %s => %s' % (source,target)
    rc = subprocess.call(['svn', 'checkout', source, target])
    if rc != 0 :
        print "svn failed to retrieve target %s from %s" % (target,source)
        print "error: %s" % rc
        return False
    return True


def WGetDownload(target, source):
    print '[wget] %s => %s' % (source,target)
    rc = subprocess.call(['wget', '-O', target, source])
    if rc != 0 :
       print "wget failed to retrieve target %s from %s" % (target,source)
       print "error: %s" % rc
       return False
    return True

def downloadDependency(env,name):
    found = False
    projectsFile = os.path.join(env['WS_DIR'],'projects')
    f = open(projectsFile,'r')
    for line in f:
        (compname, repoType, url) = line.split('|')
        url = url.rstrip()
        print '%s, %s, %s' % (compname, repoType, url)
        print 'dep: %s' % name  
        if compname == name:
            print 'found dep: %s' % compname
            compTarget = os.path.join(env['WS_DIR'],compname)
            # ask the user if he wants to download it
            print 'I found the dependency %s located at %s' % (name,url)
            userResponse = raw_input('Do you want me to download it? ')
            userResponse = userResponse.lower()
            if userResponse == 'y' or userResponse == 'yes' or userResponse == 'yeap' or userResponse == 'ok' or userResponse == 'yeah':
                result = False
                if repoType == 'wget':
                    result = WGetDownload(compTarget,url)
                elif repoType == 'svn':
                    result = SVNGetDownload(compTarget,url)
                else:
                    raise Exception('Unknown protocol type to download component %s' % name)
                if result:
                   found = True
            break
    f.close()
    return found
