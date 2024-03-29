# fudepan-build: The build system for FuDePAN projects
#
# Copyright (C) 2011-2012 Esteban Papp, Hugo Arregui,
#               2013 Gonzalo Bonigo, Gustavo Ojeda, Matias Iturburu,
#                    Leandro Moreno, FuDePAN
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
import platform
import subprocess
from xml.dom import minidom

from SCons.Script import Builder
import SCons

from termcolor import Cformat
from termcolor import Cprint
import utils
import fbuild_exceptions


# Constants for the _CreateDependency() function.
DEP_PROJECT = 'project'
DEP_EXTERNAL = 'external dependency'
# Stores the distribution name. It's set within the init() function.
DISTRO = None
# Default package manager.
MANAGER = None
# Dictionary with the projects from 'conf/projects.xml'
projects = {}
# Dictionary with the components from 'conf/external_dependencies.xml'
external_dependencies = {}
# A C template file for the internal functions _Check*Install().
C_TEMPLATE_CODE = "%sint main(){return 0;}\n"
# The C template file name for the internal function _CheckLibInstall().
C_TEMPLATE_FILE = '_chklib_'
# A command-line template for the internal function _CheckLibInstall().
CMD_TEMPLATE_LIB = 'gcc -o _chklib_ _chklib_.c -l%s'
# A command-line template for the internal function _CheckHLibInstall().
CMD_TEMPLATE_HLIB = 'gcc -E _chklib_.c'
# The name of the temporal download directory.
TMP_DIR = '_tmp_downloads'
# A shortcut for subprocess.PIPE
PIPE = subprocess.PIPE


def init(env):
    # Sets a dictionary that will store calls to CreateExternalLibraryComponent().
    env.ExternalDependenciesCreateComponentsDict = {}
    # We try to get in which distro we are.
    try:
        global DISTRO
        global MANAGER
        DISTRO = utils.GetDistro()
        if DISTRO == utils.DISRTO_ARCH:
            MANAGER = 'PACMAN'
        else:
            MANAGER = 'APT-GET'
    except fbuild_exceptions.DistroError:
        env.Cprint('[warn] unsupported distribution.', 'yellow')
    # Create a builder for the checkout of the dependencies.
    coDep = SCons.Action.Action(CheckoutDependency, CheckoutDependencyMessage)
    checkoutBuilder = Builder(action=coDep)
    env.Append(BUILDERS={'CheckoutDependency': checkoutBuilder})
    # Create a builder for the update of the dependencies.
    upDep = SCons.Action.Action(UpdateDependency, UpdateDependencyMessage)
    updateBuilder = Builder(action=upDep)
    env.Append(BUILDERS={'UpdateDependency': updateBuilder})
    # Creates projects targets.
    _CreateProjectsDependenciesTargets(env)
    # Create external dependencies targets.
    _CreateExternalDependenciesTargets(env)
    # Puts a public function within the environment.
    env.CheckoutDependencyNow = CheckoutDependencyNow
    env.GetComponentDeps = GetComponentDeps


class Dependencies(object):

    def __init__(self, name, target, node, env):
        self.env = env
        self.name = name
        self.type = node.tagName
        self.username = node.getAttribute('username')
        self.url = node.getAttribute('repository_url')
        self.target = target
        self.component_type = node.getAttribute('type')
        self.component_check = node.getAttribute('check')
        if not self.component_check:
            self.component_check = self.name
        self.component_deps = node.getAttribute('deps').split(',')
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
        if self.component_type:
            # Create the cal to 'CreateExternalLibraryComponent()'.
            pcall = "env.CreateExternalComponent('%s',[%s],%s,%s,%s)"
            # External components no need external includes.
            ext = ''
            # External components no need a directory since now they are install
            # in the system.
            path = "env.Dir('.')"
            # Get the dependencies of the component.
            deps = self.component_deps
            # Remove empty strings from the dependency list.
            while '' in deps:
                deps.remove('')
            # Check if the component is linkable library.
            if self.component_type in ['LIB']:
                link = 'True'
            else:
                link = 'False'
            # Create the string that with the python call.
            self.create_ext_lib_component = pcall % (name, ext, path, deps, link)
        else:
            self.create_ext_lib_component = ''

    def AfterCheckout(self):
        """
            Description:
                This method download the component/project and install it.
            Arguments:
                None.
            Exceptions:
                None.
            Return:
                True if the component is installed.
                False otherwise.
        """
        if len(self.executeAfter) > 0:
            commands = _GetExecutableCommands(self.env, self.executeAfter)
            for cmd in commands:
                Cprint('[info] execute post-checkout command: %s' % cmd, 'purple')
                rc = subprocess.call(cmd, shell=True)
                if rc != 0:
                    return Cformat('[error] failed to execute post-checkout command: %s, error: %s' % (cmd, rc),
                                   'red')
        return 0

    def CheckInstall(self):
        """
            Description:
                This method check if the component/project is installed or not.
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
            result = False
            commands = _GetExecutableCommands(self.env, self.inatllChecker)
            for cmd in commands:
                rc = subprocess.call(cmd, shell=True, stdout=PIPE, stderr=PIPE)
                result = (rc == 0)
        elif self.component_type == 'HLIB':
            result = _CheckHLibInstall(self.component_check)
        elif self.component_type == 'LIB':
            result = _CheckLibInstall(self.component_check)
        elif self.component_type == 'PRO':
            result = _CheckProgInstall(self.component_check)
        else:
            result = False
        return result

    def Checkout(self):
        pass


class HG(Dependencies):

    def __init__(self, name, target, node, env):
        super(HG, self).__init__(name, target, node, env)
        if self.type == 'component':
            self.url = target
            self.target = self.env.Dir(os.path.join(TMP_DIR, name)).abspath

    def Checkout(self):
        if not os.path.exists(self.target):
            os.makedirs(self.target)
        Cprint('[hg] Checkout %s => %s' % (self.url, self.target), 'purple')
        rc = subprocess.call(['hg', 'clone', self.url, self.target])
        if rc != 0:
            return Cformat('[error] hg failed to Checkout target %s from %s, error: %s' % (self.target, self.url, rc),
                           'red')
        return self.AfterCheckout()

    def Update(self):
        Cprint('[hg] updating %s => %s' % (self.url, self.target), 'purple')
        rc = subprocess.call("cd %s; hg pull -u" % self.target, shell=True)
        if rc != 0:
            return Cformat('[error] hg failed to update target %s from %s, error: %s' % (self.target, self.url, rc),
                           'red')
        return 0


class SVN(Dependencies):

    def __init__(self, name, target, node, env):
        super(SVN, self).__init__(name, target, node, env)
        if self.type == 'component':
            self.url = target
            self.target = self.env.Dir(os.path.join(TMP_DIR, name)).abspath

    def Checkout(self):
        if not os.path.exists(self.target):
            os.makedirs(self.target)
        Cprint('[svn] Checkout %s => %s' % (self.url, self.target), 'purple')
        cmd = ['svn', 'checkout'] + (['--username', self.username] if self.username else []) + [self.url, self.target]
        rc = subprocess.call(cmd)
        if rc != 0:
            
            return Cformat(
                '[error] svn failed to checkout target %s from %s, error: %s'
                % (self.target, self.url, rc),
                'red'
            )
        return self.AfterCheckout()

    def Update(self):
        Cprint('[svn] updating %s => %s' % (self.url, self.target), 'purple')
        rc = subprocess.call("cd %s; svn update" % self.target, shell=True)
        if rc != 0:

            return Cformat(
                '[error] svn failed to update target %s from %s, error: %s'
                % (self.target, self.url, rc),
                'red'
            )
        return 0


class WGET(Dependencies):

    def __init__(self, name, target, node, env):
        super(WGET, self).__init__(name, target, node, env)
        if self.type == 'component':
            self.url = target
            self.target = self.env.Dir(os.path.join(TMP_DIR, name)).abspath

    def Checkout(self):
        if not os.path.exists(self.target):
            os.makedirs(self.target)
        Cprint('[wget] downloading %s => %s' % (self.url, self.target), 'purple')
        rc = subprocess.call(['wget', self.url, '-P', self.target])
        if rc != 0:
            return Cformat(
                '[error] wget failed to download target %s from %s, error: %s'
                % (self.target, self.url, rc),
                'red'
            )
        return self.AfterCheckout()

    def Update(self):
        # this is not supported, should be? should we download the version
        # again an update? that will be time consuming and update should be
        # fast. This should be supported once we mark the version and there
        # is a way to know that the version didn't changed from last download
        return 0


class PACKER(Dependencies):

    def Checkout(self):
        Cprint('[packer] installing %s ' % self.name, 'purple')
        rc = subprocess.call('sudo packer -S %s' % self.target, shell=True)
        if rc != 0:
            return Cprint(
                '[error] pacman failed to installing %s, error: %s'
                % (self.target, rc),
                'red'
            )
        return self.AfterCheckout()


class PACMAN(Dependencies):

    def Checkout(self):
        Cprint('[pacman] installing %s ' % self.name, 'purple')
        rc = subprocess.call('sudo pacman -S %s' % self.target, shell=True)
        if rc != 0:
            return Cprint(
                '[error] pacman failed to installing %s, error: %s'
                % (self.target, rc),
                'red'
            )
        return self.AfterCheckout()


class APT_GET(Dependencies):

    def Checkout(self):
        Cprint('[apt-get] installing %s ' % self.name, 'purple')
        rc = subprocess.call('sudo apt-get install -y %s' % self.target, shell=True)
        if rc != 0:
            return Cprint(
                '[error] apt-get failed to installing %s, error: %s'
                % (self.target, rc),
                'red'
            )
        return self.AfterCheckout()


class APTITUDE(Dependencies):

    def Checkout(self):
        Cprint('[aptitude] installing %s ' % self.name, 'purple')
        rc = subprocess.call('sudo aptitude install %s' % self.target, shell=True)
        if rc != 0:
            return Cprint(
                '[error] aptitude failed to installing %s, error: %s'
                % (self.target, rc),
                'red'
            )
        return self.AfterCheckout()


def _CreateProjectsDependenciesTargets(env):
    """
        Description:
            This function parse the projects.xml file, creates the dependencies
            between projects and the targets for those not being checked-out.
        Arguments:
            env  -  An SCons environment.
        Exceptions:
            None.
        Return:
            None.
    """
    confDir = os.path.join(env.Dir('#').abspath, 'conf')
    projectsFile = os.path.join(confDir, 'projects.xml')
    projectsDom = minidom.parse(projectsFile)
    projectElements = projectsDom.getElementsByTagName('project')
    for projectElement in projectElements:
        projectName = projectElement.getAttribute('name')
        if projectName in projects > 0:
            env.Cprint(
                '[warn] project ' + projectName + ' information is duplicated in'
                + ' the projects.xml file',
                'yellow'
            )
        else:
            projectType = projectElement.getAttribute('repository_type')
            project = _CreateDependency(
                env,
                projectName,
                projectType,
                projectElement
            )
            if project:
                projects[projectName] = project
    localProjectsFile = os.path.join(confDir, 'projects_local.xml')
    if os.path.exists(localProjectsFile):
        localProjectElements = projectsDom.getElementsByTagName('project')
        for localProjectElment in localProjectElements:
            projectType = localProjectElment.getAttribute('repository_type')
            project = _CreateDependency(
                env,
                projectName,
                projectType,
                localProjectElment
            )
            if project:
                projects[projectName] = project
    for project in projects.keys():
        # Check if the project was already checked out
        projectDir = os.path.join(env['WS_DIR'], project)
        if env.Dir(projectDir).exists():
            tgt = project + ':update'
            updateAction = env.UpdateDependency(tgt, 'SConstruct')
            env.AlwaysBuild(
                env.Alias(tgt, updateAction, 'Update ' + project)
            )
            env.Alias('all:update', tgt, 'updates all checked-out projects')
        else:
            tgt = project + ':checkout'
            checkoutAction = env.CheckoutDependency(tgt, 'SConstruct')
            env.AlwaysBuild(
                env.Alias(tgt, checkoutAction, 'Checkout ' + project)
            )


def _CreateExternalDependenciesTargets(env):
    """
        Description:
            This function parse the external_dependencies.xml file, creates
            the dependencies and the targets for the not installed component.
        Arguments:
            evn  -  An SCons environment.
        Exceptions:
            None.
        Return:
            None.
    """
    # Path to the Configuration Directory.
    confDir = os.path.join(env.Dir('#').abspath, 'conf')
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
        if componentName in external_dependencies:
            env.Cprint('[warn] component ' + componentName +
                       ' information is duplicated in the ' +
                       'external_dependencies.xml file', 'yellow')
        else:
            componentTarget = ''
            componentType = 'DEP'
            # Parse installers.
            installers = componentElement.getElementsByTagName('installer')
            for installer in installers:
                distro = installer.getAttribute('distro')
                if distro == DISTRO or distro == '*':
                    componentTarget = installer.getAttribute('target')
                    componentType = installer.getAttribute('manager')
                    if componentType == "*":
                        componentType = MANAGER
                    break
            dep = _CreateDependency(
                env,
                componentName,
                componentType,
                componentElement,
                componentTarget,
                DEP_EXTERNAL
            )
            if not dep is None:
                external_dependencies[componentName] = dep
    # Check if each component is already installed.
    for component in external_dependencies.keys():
        if external_dependencies[component].CheckInstall():
            # If it's installed we have to add the component to the graph by
            # adding a call to 'CreateExternalLibraryComponent()'.
            pcall = external_dependencies[component].create_ext_lib_component
            # Add it to the list of calls.
            env.ExternalDependenciesCreateComponentsDict[component] = pcall


def _CreateDependency(env, name, type, node, target=None, dep_type=DEP_PROJECT):
    if target is None:
        target = os.path.join(env['WS_DIR'], name)
    if type == 'DEP':
        return Dependencies(name, target, node, env)
    elif type == 'HG':
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
        Cprint('[error] %s %s has repository %s which is not supported'
               % (dep_type, name, type), 'red')
        return None


def _CheckHLibInstall(include):
    """
        Description:
            This is an internal function that checks if a header only
            library is installed or not.
        Arguments:
            include  -  A string with the name of the main inclued.
        Exceptions:
            None.
        Return:
            True if the library exists.
            False otherwise.
    """
    # Create the C file
    f = open(C_TEMPLATE_FILE + '.c', 'w')
    f.write(C_TEMPLATE_CODE % ('#include <%s>\n' % include))
    f.close()
    # Check if the library except
    rc = subprocess.call(
        CMD_TEMPLATE_HLIB,
        shell=True,
        stdout=PIPE,
        stderr=PIPE
    )
    # Delete the files.
    os.remove(C_TEMPLATE_FILE + '.c')
    return rc == 0


def _CheckLibInstall(lib):
    """
        Description:
            This is an internal function that checks if a library is
            installed or not.
        Arguments:
            lib  -  A string with the name of the library. This should not
                    contain the 'lib' prefix or extension.
        Exceptions:
            None.
        Return:
            True if the library exists.
            False otherwise.
    """
    # Create the C file
    f = open(C_TEMPLATE_FILE + '.c', 'w')
    f.write(C_TEMPLATE_CODE % '')
    f.close()
    # Create the command line
    cmd = CMD_TEMPLATE_LIB % lib
    # Check if the library except
    rc = subprocess.call(cmd, shell=True, stdout=PIPE, stderr=PIPE)
    # Delete the files.
    os.remove(C_TEMPLATE_FILE + '.c')
    if rc == 0:
        os.remove(C_TEMPLATE_FILE)
    return rc == 0


def _CheckProgInstall(prog):
    """
        Description:
            This is an internal function that checks if a program is
            installed or not.
        Arguments:
            prog  -  A string with the name of the program.
        Exceptions:
            None.
        Return:
            True if the program exists.
            False otherwise.
    """
    # Create the command line
    cmd = 'which %s' % prog
    # Check if the program except
    return subprocess.call(cmd, shell=True, stdout=PIPE, stderr=PIPE) == 0


def _GetExecutableCommands(env, string_commands):
    """
        Description:
            Parse a string with multiple shell commands and return a list of
            commands.
        Arguments:
            env              -  A SCons environment.
            string_commands  -  A string with the commands to parse.
        Exceptions:
            None.
        Return:
            A list instance which contains string that represents shell
            commands that be executed.
    """

    (arch, binType) = platform.architecture()
    CXXFLAGS = ''
    CFLAGS = ''
    if arch == '64bit':
        CFLAGS = '"-fPIC"'
        CXXFLAGS = '"-fPIC"'
    result = []
    lines = string_commands.split('\n')
    for line in lines:
        while line and line[0] in [' ', '\t', '\r', '\n']:
            line = line[1:]
        if line:
            line = line.replace('{WS_DIR}', env['WS_DIR'])
            line = line.replace('#', env.Dir('#').abspath)
            line = line.replace('{TMP_DIR}', TMP_DIR)
            line = line.replace('{CFLAGS}', CFLAGS)
            line = line.replace('{CXXFLAGS}', CXXFLAGS)
            result.append(line)
    return result


def CheckoutDependencyMessage(env, source, target):
    return ''


def CheckoutDependency(env, source, target):
    # Crate a temporary directory for download external components.
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)
    depname = str(target[0]).split(':')[0]
    if depname in external_dependencies.keys():
        dep = external_dependencies[depname]
    else:
        dep = projects[depname]
    result = dep.Checkout()
    if dep.create_ext_lib_component:
        st = dep.create_ext_lib_component
        env.ExternalDependenciesCreateComponentsDict[depname] = st
    # Remove the temporary directory.
    os.system('rm -rf %s' % TMP_DIR)
    return result


#
# In this both functions we have to check if the component dependencies are
# installed or not. Also we have to see if we can let only one function
# instead CheckoutDependency() and CheckoutDependencyNow().
#


def CheckoutDependencyNow(depname, env):
    # Crate a temporary directory for download external components.
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)
    if depname in external_dependencies.keys():
        dep = external_dependencies.get(depname)
    else:
        dep = projects.get(depname)
    if dep:
        result = dep.Checkout() == 0
        if dep.create_ext_lib_component:
            st = dep.create_ext_lib_component
            env.ExternalDependenciesCreateComponentsDict[depname] = st
    else:
        result = False
    # Remove the temporary directory.
    os.system('rm -rf %s' % TMP_DIR)
    return result


def UpdateDependencyMessage(env, source, target):
    return ''


def UpdateDependency(env, source, target):
    dep = str(target[0]).split(':')[0]
    return projects[dep].Update()


def GetComponentDeps(component):
    result = []
    if component in external_dependencies.keys():
        dep = external_dependencies.get(component)
    else:
        dep = projects.get(component)
    if dep:
        if dep.component_deps:
            result = dep.component_deps if dep.component_deps[0] is not '' else []
    return result
