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

#
# Description: this file contains all the dependencies parse/checkout/update
#

import os
import os.path
import subprocess
from xml.dom import minidom
from SCons.Script import Builder
import SCons
from termcolor import cformat
from termcolor import cprint


projects = {}
external_dependencies = {}


def init(env):
    coDep = SCons.Action.Action(CheckoutDependency, CheckoutDependencyMessage)
    checkoutBuilder = Builder(action = coDep)
    env.Append(BUILDERS={'CheckoutDependency': checkoutBuilder})
    upDep = SCons.Action.Action(UpdateDependency, UpdateDependencyMessage)
    updateBuilder = Builder(action = upDep)
    env.Append(BUILDERS={'UpdateDependency': updateBuilder})
    createDependenciesTargets(env)
    createExternalDependenciesTargets(env)
    env.CheckoutDependencyNow = CheckoutDependencyNow
    

def createDependenciesTargets(env):
    confDir = os.path.join(env.Dir('#').abspath,'conf')
    projectsFile = os.path.join(confDir, 'projects.xml')
    
    projectsDom = minidom.parse(projectsFile)
    projectElements = projectsDom.getElementsByTagName('project') 
    for projectElement in projectElements:
        projectName = projectElement.getAttribute('name')
        if projects.has_key(projectName) > 0:
            env.cprint (
                '[warn] project '+projectName+' information is duplicated in'+\
                ' the projects.xml file',
                'yellow'
            )
        else:
            projectType = projectElement.getAttribute('repository_type')
            project = createDependency(env,projectName,projectType,projectElement)
            if project:
                projects[projectName] = project
        
    localProjectsFile = os.path.join(confDir, 'projects_local.xml') 
    if os.path.exists(localProjectsFile):
        localProjectElements = projectsDom.getElmentsByTagName('project')
        for localProjectElment in localProjectElements:
            projectType = projectElement.getAttribute('repository_type')
            project = createDependency(env,projectName,projectType,projectElement)
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


def createExternalDependenciesTargets(env):
    # Path to the Configuration Directorie.
    confDir = os.path.join(env.Dir('#').abspath,'conf')
    # Path to the 'external_dependencies.xml' file.
    extDepsFile = os.path.join(confDir, 'external_dependencies.xml')
    # Parse the xml file and loads all the external dependencies in the 
    # external_dependencies dictionary.
    extDepsDom = minidom.parse(extDepsFile)
    componentElements = extDepsDom.getElementsByTagName('component')
    for componentElement in componentElements:
        componentName = componentElement.getAttribute('name')
        # If the component name already exists within the external dependencies
        # dictionary, we have duplicated information into the external_dependencies
        # xml file.
        if external_dependencies.has_key(componentName) > 0:
            env.cprint('[warn] component ' + componentName + \
                       ' information is duplicated in the ' + \
                       'external_dependencies.xml file', 'yellow')
        else:
            # Check the 'repository_type' attribute.
            componentType = componentElement.getAttribute('repository_type')
            # If it's 'PACKAGE', we look for a package manager.
            if componentType == 'PACKAGE':
                pkgPrority = componentElement.getAttribute('pkg_manager_prority')
                componentType = _getPackageManager(pkgPrority)
            dep = createDependency(
                    env,
                    componentName,
                    componentType,
                    componentElement,
                    'external dependencie'
            )
            if not dep is None:
                external_dependencies[componentName] = dep
    # Check if each component is already installed.
    for component in external_dependencies.keys():
        if not external_dependencies[component].checkInstall():
            tgt = '%s:install' % component
            checkoutAction = env.CheckoutDependency(tgt,'SConstruct')
            alias = env.Alias(tgt, checkoutAction, 'Install %s' % component)
            env.AlwaysBuild(alias)


class Dependencies(object):
    
    def __init__(self, name, target, node, env):
        self.name = name
        self.target = target
        self.url = node.getAttribute('repository_url')
        self.package = node.getAttribute('package_name')
        if len(node.childNodes) > 0:
            # we need to get the text contained in execute_after, to do so, we
            # get the execute_after node, then we get the child node (the text
            # contained in the execute_after node), and then we get the text.
            # Here we are assuming that the contents of the execute_after node
            # would be of type TEXT_NODE, otherwise, it would cause an error.
            elem = node.getElementsByTagName('execute_after')
            if elem != []:
                self.executeAfter = elem[0].childNodes[0].data
            else:
                self.executeAfter = ''
            elem = node.getElementsByTagName('install_checker')
            if elem != []:
                self.inatllChecker = ((elem[0]).childNodes[0]).data
            else:
                self.inatllChecker = ''
        else:
            self.executeAfter = ''
            self.inatllChecker = ''
        if node.hasAttribute('username'):
            self.username = node.getAttribute('username')
        else:
            self.username = ''
        self.env = env

    def afterCheckout(self):
        if len(self.executeAfter) > 0:
            cmds = self.executeAfter.split('\n')
            for cmd in cmds:
                cmd = cmd.replace('{WS_DIR}', self.env['WS_DIR'])
                cmd = cmd.replace('#', self.env.Dir('#').abspath)
                cprint('[info] execute post-checkout command: %s' % cmd, 'purple')
                rc = subprocess.call(cmd, shell=True)
                if rc != 0:
                    return cformat('[error] failed to execute post-checkout command: %s, error: %s' % (cmd, rc), 'red')
        return 0
    
    def checkInstall(self):
        result = False
        if len(self.inatllChecker) > 0:
            cmds = self.inatllChecker.split('\n')
            for cmd in cmds:
                cmd = cmd.replace('{WS_DIR}', self.env['WS_DIR'])
                cmd = cmd.replace('#', self.env.Dir('#').abspath)
                rc = subprocess.call(cmd, shell=True)
                if rc == 0:
                    result = True
        return result


class HG(Dependencies):
    
    def checkout(self):
        cprint('[hg] checkout %s => %s' % (self.url, self.target), 'purple')
        rc = subprocess.call(['hg', 'clone', self.url, self.target])
        if rc != 0:
            return cformat('[error] hg failed to checkout target %s from %s, error: %s' 
                           % (self.target, self.url, rc), 'red')
        return self.afterCheckout()

    def update(self):
        cprint('[hg] updating %s => %s' % (self.url, self.target), 'purple')
        rc = subprocess.call("cd %s; hg pull -u" % self.target, shell=True)
        if rc != 0:
            return cformat('[error] hg failed to update target %s from %s, error: %s' 
                           %(self.target, self.url, rc), 'red')
        return 0


class SVN(Dependencies):
    
    def checkout(self):
        cprint('[svn] checkout %s => %s' % (self.url, self.target), 'purple')
        cmd = ['svn', 'checkout'] + (['--username', self.username] if self.username else []) + [self.url, self.target]
        rc = subprocess.call(cmd)
        if rc != 0 :
            return cformat('[error] svn failed to checkout target %s from %s, error: %s' 
                           % (self.target, self.url, rc), 'red')
        return self.afterCheckout()

    def update(self):
        cprint('[svn] updating %s => %s' % (self.url, self.target), 'purple')
        rc = subprocess.call("cd %s; svn update" % self.target, shell=True)
        if rc != 0 :
            return cformat('[error] svn failed to update target %s from %s, error: %s' 
                           % (self.target, self.url, rc), 'red')
        return 0


class WGET(Dependencies):
    
    def checkout(self):
        cprint('[wget] downloading %s => %s' % (self.url, self.target), 'purple')
        rc = subprocess.call(['wget', self.url, '-P', self.target])
        if rc != 0 :
           return cformat('[error] wget failed to download target %s from %s, error: %s' 
                          % (self.target, self.url, rc), 'red')
        return self.afterCheckout()
    
    def update(self):
        # this is not supported, should be? should we download the version
        # again an update? that will be time consuming and update should be
        # fast. This should be supported once we mark the version and there
        # is a way to know that the version didn't changed from last download
        return 0


class PACKER(Dependencies):
    
    def checkout(self):
        cprint('[packer] installing %s ' % self.package, 'purple')
        rc = subprocess.call(['sudo packer -S ', self.package])
        if rc != 0 :
           return cformat('[error] packer failed to installing %s, error: %s' 
                          % (self.package, rc), 'red')
        return self.afterCheckout()
    
    def update(self):
        # this is not supported, should be? should we download the version
        # again an update? that will be time consuming and update should be
        # fast. This should be supported once we mark the version and there
        # is a way to know that the version didn't changed from last download
        return 0


class PACMAN(Dependencies):
    
    def checkout(self):
        #
        #
        # DO SOMETHIG!!!!
        #
        #
        return self.afterCheckout()
    
    def update(self):
        # this is not supported, should be? should we download the version
        # again an update? that will be time consuming and update should be
        # fast. This should be supported once we mark the version and there
        # is a way to know that the version didn't changed from last download
        return 0


class APT_GET(Dependencies):
    
    def checkout(self):
        cprint('[apt-get] installing %s ' % self.name, 'purple')
        rc = subprocess.call('sudo apt-get install %s' % self.package, shell=True)
        if rc != 0 :
           return cprint('[error] apt-get failed to installing %s, error: %s' 
                          % (self.package, rc), 'red')
        return self.afterCheckout()
    
    def update(self):
        # this is not supported, should be? should we download the version
        # again an update? that will be time consuming and update should be
        # fast. This should be supported once we mark the version and there
        # is a way to know that the version didn't changed from last download
        return 0


class APTITUDE(Dependencies):
    
    def checkout(self):
        #
        #
        # DO SOMETHIG!!!!
        #
        #
        return self.afterCheckout()
    
    def update(self):
        # this is not supported, should be? should we download the version
        # again an update? that will be time consuming and update should be
        # fast. This should be supported once we mark the version and there
        # is a way to know that the version didn't changed from last download
        return 0


def createDependency(env, name, type, node, dep_type='project'):
    target = os.path.join(env['WS_DIR'], name)
    if type == 'HG':
        return HG(name, target, node, env)
    elif type == 'SVN':
        return SVN(name, target, node, env)
    elif type == 'WGET':
        return WGET(name, target, node, env)
    elif type == 'APTITUDE':
        return APTITUDE(name, name, node, env)
    elif type == 'APT-GET':
        return APT_GET(name, name, node, env)
    elif type == 'PACMAN':
        return PACMAN(name, name, node, env)
    elif type == 'PACKER':
        return PACKER(name, name, node, env)
    else:
        cprint('[error] %s %s has repository %s which is not supported' 
               % (dep_type, name, type), 'red')
        return None


def CheckoutDependencyMessage(env, source, target):
    return ''


def CheckoutDependency(env, source, target):
    dep = str(target[0]).split(':')[0]
    if dep in external_dependencies.keys():
        result = external_dependencies[dep].checkout()
    else:
        result = projects[dep].checkout()
    return result


def CheckoutDependencyNow(dep):
    if dep in external_dependencies.keys():
        d = external_dependencies.get(dep)
    else:
        d = projects.get(dep)
    return d.checkout() == 0 if d else False


def UpdateDependencyMessage(env, source, target):
    return ''


def UpdateDependency(env, source, target):
    dep = str(target[0]).split(':')[0]
    return projects[dep].update()


def _getPackageManager(pkg_manager_prority=None):
    """
        Description:
            This is an internal function that looks for the package manager of the
            current system. It's used by [createDependency()].
            Actually it supports:
                apt-get
                aptitude
                packer
                pacman
        Argument:
            pkg_manager_prority  -  A string (instance of str) with the priority 
                                    list for the package managers.
        Exceptions:
            None:
        Return:
            A str instance with the name of the package manager.
            An empty string is returned if none was found.
    """
    if pkg_manager_prority:
        pkg_priority_list = pkg_manager_prority.split(',')
    else:
        pkg_priority_list = ['APT-GET','APTITUDE','PACKER','PACMAN']
    for pkg in pkg_priority_list:
        if os.system('which %s > /dev/null' % pkg.lower()) == 0:
            return pkg
    return ''
