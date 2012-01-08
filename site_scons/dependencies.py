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

# FuDePAN Bolierplate

import os.path
import SCons
import sys
import subprocess
from termcolor import cprint, ask_user

projects = {}

def init(env):
    from SCons.Script import Builder
    checkoutBuilder = Builder(action = SCons.Action.Action(CheckoutDependency, CheckoutDependencyMessage))
    env.Append(BUILDERS = {'CheckoutDependency': checkoutBuilder})
    updateBuilder = Builder(action = SCons.Action.Action(UpdateDependency, UpdateDependencyMessage))
    env.Append(BUILDERS = {'UpdateDependency': updateBuilder})
    createDependenciesTargets(env)
    
def createDependenciesTargets(env):
    confDir = os.path.join(env.Dir('#').abspath,'conf')
    projectsFile = os.path.join(confDir, 'projects.xml')
    
    from xml.dom.minidom import parse
    projectsDom = parse(projectsFile)
    projectElements = projectsDom.getElementsByTagName('project') 
    for projectElement in projectElements:
        projectName = projectElement.getAttribute('name')
        if projects.has_key(projectName) > 0:
            env.cprint('[warn] project ' + projectName 
                       + ' informatino is duplicated in the projects.xml file', 'yellow')
        else:
            projectType = projectElement.getAttribute('repository_type')
            project = createDependency(env, projectName, projectType, projectElement)
            if project:
                projects[projectName] = project
        
    localProjectsFile = os.path.join(confDir, 'projects_local.xml') 
    if os.path.exists(localProjectsFile):
        localProjectsDom = parse(localProjectsFile)
        localProjectElements = projectsDom.getElmentsByTagName('project')
        for localProjectElment in localProjectElements:
            localProjectName = projectElement.getAttribute('name')
            projectType = projectElement.getAttribute('repository_type')
            project = createDependency(env, projectName, projectType, projectElement)
            if project:
                projects[projectName] = project
    
    for project in projects.keys():
        # Check if the project was already checked out
        projectDir = os.path.join(env['WS_DIR'],project)
        if env.Dir(projectDir).exists():
            tgt = project + ':update'
            updateAction = env.UpdateDependency(tgt,'SConstruct')
            env.AlwaysBuild( env.Alias(tgt, updateAction, 'update ' + project))
            env.Alias('all:update', tgt, 'updates all checked-out projects')
        else:
            tgt = project + ':checkout'
            checkoutAction = env.CheckoutDependency(tgt,'SConstruct')
            env.AlwaysBuild( env.Alias(tgt, checkoutAction, 'checkout ' + project))

class Dependencies(object):
    def __init__(self, name, target, node):
        self.name = name
        self.target = target
        self.url = node.getAttribute('repository_url')
        if len(node.childNodes) > 0:
            self.executeAfter = node.childNodes[0].nodeValue
        else:
            self.executeAfter = ''
        if node.hasAttribute('username'):
            self.username = node.getAttribute('username')
        else:
            self.username = ''

    def afterCheckout(self):
        if len(self.executeAfter):
            cmds = self.executeAfter.split('\n')
            for cmd in cmds:
                cmd = cmd.replace('#', self.env['ROOT'])
                cprint('[info] execute post-checkout command: %s' % cmd, 'purple')
                rc = subprocess.call(cmd.split(' '))
                if rc != 0:
                    cprint('[error] failed to execute post-checkout command: %s, error: %s' % (cmd, rc), 'red')
                    return False

class HG(Dependencies):
    def checkout(self):
        cprint('[hg] checkout %s => %s' % (self.url, self.target), 'purple')
        rc = subprocess.call(['hg', 'clone', self.url, self.target])
        if rc != 0:
            cprint('[error] hg failed to checkout target %s from %s, error: %s' 
                   % (self.target, self.url, rc), 'red')
            return False
        return self.afterCheckout()

    def update(self):
        cprint('[hg] updating %s => %s' % (self.url, self.target), 'purple')
        rc = subprocess.call("cd %s; hg pull -u" % self.target, shell=True)
        if rc != 0:
            cprint('[error] hg failed to update target %s from %s, error: %s' 
                   % (self.target, self.url, rc), 'red')
            return False
        return True

class SVN(Dependencies):
    def checkout(self):
        cprint('[svn] checkout %s => %s' % (self.url, self.target), 'purple')
        cmd = ['svn', 'checkout'] + (['--username', self.username] if self.username else []) + [self.url, self.target]
        rc = subprocess.call(cmd)
        if rc != 0 :
            cprint('[error] svn failed to checkout target %s from %s, error: %s' 
                   % (self.target, self.url, rc), 'red')
            return False
        return self.afterCheckout()

    def update(self):
        cprint('[svn] uafterCheckoutpdating %s => %s' % (self.url, self.target), 'purple')
        rc = subprocess.call("cd %s; svn update" % self.target, shell=True)
        if rc != 0 :
            cprint('[error] svn failed to update target %s from %s, error: %s' 
                   % (self.target, self.url, rc), 'red')
            return False
        return True

class WGET(Dependencies):
    def checkout(self):
        cprint('[wget] downloading %s => %s' % (self.url, self.target), 'purple')
        rc = subprocess.call(['wget', self.url, '-P', self.target])
        if rc != 0 :
           cprint('[error] wget failed to download target %s from %s, error: %s' 
                  % (self.target, self.url, rc), 'red')
           return False
        return self.afterCheckout()
    
    def update(self):
        #TODO: this is not supported, should be? should we download the version
        # again an update? that will be time consuming and update should be
        # fast.
        return True

def createDependency(env, name, type, node):
    target = os.path.join(env['WS_DIR'], name)
    if type == 'HG':
        return HG(name, target, node)
    elif type == 'SVN':
        return SVN(name, target, node)
    elif type == 'WGET':
        return WGET(name, target, node)
    else:
        cprint('[error] project %s has repository %s which is not supported' 
               % (name, type), 'red')
        return None
        
def CheckoutDependencyMessage(env, source, target):
    return ""

def CheckoutDependency(env, source, target):
    dep = str(target[0]).split(':')[0]
    return projects[dep].checkout()

def UpdateDependencyMessage(env, source, target):
    return ""

def UpdateDependency(env, source, target):
    dep = str(target[0]).split(':')[0]
    return projects[dep].update()
