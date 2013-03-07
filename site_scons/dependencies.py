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
    This file contains all the dependencies parse/checkout/update.
"""


import os
import os.path
import subprocess
from xml.dom import minidom
from SCons.Script import Builder
import SCons
from termcolor import cformat
from termcolor import cprint
import utils


# Constants for the createDependency() function.
DEP_PROJECT = 'project'
DEP_EXTERNAL = 'external dependency'
# Stores the distribution name. It's set within the init() function.
DISTRO = None
# Dictionary with the projects from 'conf/projects.xml'
projects = {}
# Dictionary with the components from 'conf/external_dependencies.xml'
external_dependencies = {}
# A C template file for the internal function _CheckLibInstall().
C_TEMPLATE_CODE = """int main(){return 0;}"""
# The C template file name for the internal function _CheckLibInstall().
C_TEMPLATE_FILE = '_chklib_'
# A command-line template for the internal function _CheckLibInstall().
CMD_TEMPLATE = 'gcc -o _chklib_ _chklib_.c -l%s'


def init(env):
    # Sets a list that will store calls to CreateExternalLibraryComponent().
    env.ExternalDependenciesCreateComponentsList = []
    # We try to get in which distro we are.
    try:
        global DISTRO
        DISTRO = utils.get_distro()
    except utils.DistroError:
        env.cprint('[warn] unsupported distribution.', 'yellow')
    # Create a builder for the checkout of the dependencies.
    coDep = SCons.Action.Action(CheckoutDependency, CheckoutDependencyMessage)
    checkoutBuilder = Builder(action = coDep)
    env.Append(BUILDERS={'CheckoutDependency': checkoutBuilder})
    # Create a builder for the update of the dependencies.
    upDep = SCons.Action.Action(UpdateDependency, UpdateDependencyMessage)
    updateBuilder = Builder(action = upDep)
    env.Append(BUILDERS={'UpdateDependency': updateBuilder})
    # Creates projects targets.
    createProjectsDependenciesTargets(env)
    # Create external dependencies targets.
    createExternalDependenciesTargets(env)
    # Puts a public function within the enviroment.
    env.CheckoutDependencyNow = CheckoutDependencyNow


def createProjectsDependenciesTargets(env):
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
        localProjectElements = projectsDom.getElementsByTagName('project')
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
    """
    """
    # Path to the Configuration Directory.
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
            dep = None
            # Parse installers.
            installers = componentElement.getElementsByTagName('installer')
            for installer in installers:
                distro = installer.getAttribute('distro')
                if distro==DISTRO or distro=='*':
                    componentTarget = installer.getAttribute('target')
                    componentType = installer.getAttribute('manager')
                    dep = createDependency(env,
                                        componentName,
                                        componentType,
                                        componentElement,
                                        componentTarget,
                                        DEP_EXTERNAL)
                    break
            if not dep is None:
                external_dependencies[componentName] = dep
    # Check if each component is already installed.
    for component in external_dependencies.keys():
        if not external_dependencies[component].checkInstall():
            tgt = '%s:install' % component
            checkoutAction = env.CheckoutDependency(tgt,'SConstruct')
            alias = env.Alias(tgt,
                              checkoutAction,
                              'Install external component [%s]' % component)
            env.AlwaysBuild(alias)
        else:
            st = external_dependencies[component].create_ext_lib_component
            env.ExternalDependenciesCreateComponentsList.append(st)


class Dependencies(object):
    
    def __init__(self, name, target, node, env):
        self.env = env
        self.name = name
        self.type = node.tagName
        self.username = node.getAttribute('username')
        self.url = node.getAttribute('repository_url')
        self.target = target
        self.component_type = node.getAttribute('type')
        # Here we are assuming that the contents of the execute_after node
        # would be of type TEXT_NODE, otherwise, it would cause an error.
        elems = node.getElementsByTagName('execute_after')
        if elems != []:
            self.executeAfter = elems[0].childNodes[0].data
        else:
            self.executeAfter = ''
        # Here we are assuming that the contents of the install_checker node
        # would be of type TEXT_NODE, otherwise, it would cause an error.
        elems = node.getElementsByTagName('install_checker')
        if elems != []:
           self.inatllChecker = ((elems[0]).childNodes[0]).data
        else:
            self.inatllChecker = ''
        # Here we are assuming that the contents of the create_ext_lib_comp node
        # would be of type TEXT_NODE, otherwise, it would cause an error.
        elems = node.getElementsByTagName('create_ext_lib_comp')
        if elems != []:
           self.create_ext_lib_component = ((elems[0]).childNodes[0]).data
        else:
            self.create_ext_lib_component = ''

    def afterCheckout(self):
        if len(self.executeAfter) > 0:
            cmds = self.executeAfter.split('\n')
            for cmd in cmds:
                if cmd:
                    cmd = cmd.replace('{WS_DIR}', self.env['WS_DIR'])
                    cmd = cmd.replace('#', self.env.Dir('#').abspath)
                    #cprint('[info] execute post-checkout command: %s' % cmd, 'purple')
                    rc = subprocess.call(cmd, shell=True)
                    if rc != 0:
                        return cformat('[error] failed to execute post-checkout command: %s, error: %s' % (cmd, rc), 'red')
        return 0
    
    def checkInstall(self):
        """
            Description:
                This method check if the component is installed or not.
            Arguments:
                None.
            Exceptions:
                None.
            Return:
                True if the component is installed.
                False otherwise.
        """
        # If a checker was provided, we use it.
        if len(self.inatllChecker) > 0:
            # A shortcut for subprocess.PIPE
            PIPE = subprocess.PIPE
            cmds = self.inatllChecker.split('\n')
            for cmd in cmds:
                cmd = cmd.replace('{WS_DIR}', self.env['WS_DIR'])
                cmd = cmd.replace('#', self.env.Dir('#').abspath)
                rc = subprocess.call(cmd, shell=True, stdout=PIPE, stderr=PIPE)
                result = rc==0
        elif self.component_type == 'LIB':
            result = _CheckLibInstall(self.name)
        elif self.component_type == 'PRO':
            result = _CheckProgInstall(self.name)
        else:
            result = False
        return result


class HG(Dependencies):
    
    def __init__(self, name, target, node, env):
        Dependencies.__init__(self, name, target, node, env)
        if self.type == 'component':
            self.url = target
            self.target = os.path.join(env['WS_DIR'], name)
    
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
    
    def __init__(self, name, target, node, env):
        Dependencies.__init__(self, name, target, node, env)
        if self.type == 'component':
            self.url = target
            self.target = os.path.join(env['WS_DIR'], name)
    
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
    
    def __init__(self, name, target, node, env):
        Dependencies.__init__(self, name, target, node, env)
        if self.type == 'component':
            self.url = target
            self.target = os.path.join(env['WS_DIR'], name)
    
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
        cprint('[packer] installing %s ' % self.name, 'purple')
        rc = subprocess.call('sudo packer -S %s' % self.target, shell=True)
        if rc != 0 :
           return cprint('[error] pacman failed to installing %s, error: %s' 
                          % (self.target, rc), 'red')
        return self.afterCheckout()


class PACMAN(Dependencies):
    
    def checkout(self):
        cprint('[pacman] installing %s ' % self.name, 'purple')
        rc = subprocess.call('sudo pacman -S %s' % self.target, shell=True)
        if rc != 0 :
           return cprint('[error] pacman failed to installing %s, error: %s' 
                          % (self.target, rc), 'red')
        return self.afterCheckout()


class APT_GET(Dependencies):
    
    def checkout(self):
        cprint('[apt-get] installing %s ' % self.name, 'purple')
        rc = subprocess.call('sudo apt-get install %s' % self.target, shell=True)
        if rc != 0 :
           return cprint('[error] apt-get failed to installing %s, error: %s' 
                          % (self.target, rc), 'red')
        return self.afterCheckout()


class APTITUDE(Dependencies):
    
    def checkout(self):
        cprint('[aptitude] installing %s ' % self.name, 'purple')
        rc = subprocess.call('sudo aptitude install %s' % self.target, shell=True)
        if rc != 0 :
           return cprint('[error] aptitude failed to installing %s, error: %s' 
                          % (self.target, rc), 'red')
        return self.afterCheckout()


def createDependency(env, name, type, node, target=None, dep_type=DEP_PROJECT):
    if target is None:
        target = os.path.join(env['WS_DIR'], name)
    if type == 'HG':
        return HG(name, target, node, env)
    elif type == 'SVN':
        return SVN(name, target, node, env)
    elif type == 'WGET':
        return WGET(name, target, node, env)
    elif type == 'APTITUDE':
        return APTITUDE(name, target, node, env)
    elif type == 'APT-GET':
        return APT_GET(name, target, node, env)
    elif type == 'PACMAN':
        return PACMAN(name, target, node, env)
    elif type == 'PACKER':
        return PACKER(name, target, node, env)
    else:
        cprint('[error] %s %s has repository %s which is not supported' 
               % (dep_type, name, type), 'red')
        return None


def CheckoutDependencyMessage(env, source, target):
    return ''


def CheckoutDependency(env, source, target):
    dep = str(target[0]).split(':')[0]
    if dep in external_dependencies.keys():
        dep = external_dependencies[dep]
    else:
        dep = projects[dep]
    result = dep.checkout()
    if dep.create_ext_lib_component:
        st = dep.create_ext_lib_component
        env.ExternalDependenciesCreateComponentsList.append(st)
    return result


def CheckoutDependencyNow(dep, env):
    if dep in external_dependencies.keys():
        dep = external_dependencies.get(dep)
    else:
        dep = projects.get(dep)
    if dep:
        result = dep.checkout()==0
        if dep.create_ext_lib_component:
            st = dep.create_ext_lib_component
            env.ExternalDependenciesCreateComponentsList.append(st)
    else:
        result = False
    return result


def UpdateDependencyMessage(env, source, target):
    return ''


def UpdateDependency(env, source, target):
    dep = str(target[0]).split(':')[0]
    return projects[dep].update()


def _CheckLibInstall(lib):
    """
        Description:
            This is an internal function that checks if a library is installed or
            not.
        Arguments:
            lib  -  A string with the name of the library. This should not 
                    contain the 'lib' prefix or extension.
        Exceptions:
            None.
        Return:
            True if the library exists.
            False otherwise.
    """
    # A shortcut for subprocess.PIPE
    PIPE = subprocess.PIPE
    # Create the C file
    f = open(C_TEMPLATE_FILE+'.c', 'w')
    f.write(C_TEMPLATE_CODE)
    f.close()
    # Create the command line
    cmd = CMD_TEMPLATE % lib
    # Check if the library except
    rc = subprocess.call(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    # Delete the files.
    os.remove(C_TEMPLATE_FILE+'.c')
    os.remove(C_TEMPLATE_FILE)
    return rc == 0


def _CheckProgInstall(prog):
    """
        Description:
            This is an internal function that checks if a program is installed or
            not.
        Arguments:
            prog  -  A string with the name of the program.
        Exceptions:
            None.
        Return:
            True if the program exists.
            False otherwise.
    """
    # A shortcut for subprocess.PIPE
    PIPE = subprocess.PIPE
    # Create the command line
    cmd = 'which %s' % lib
    # Check if the program except
    return subprocess.call(cmd, shell=True, stdout=PIPE, stderr=PIPE) == 0