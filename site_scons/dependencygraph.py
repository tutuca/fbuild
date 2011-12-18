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
# Description: this file contains a graph with dependencies between the
#              components to better solve include paths and library linking
#
import fnmatch
import os
from SCons.Script.SConscript import SConsEnvironment

isPreProcessing = False

def init(env):
    isPreProcessing = True
    SConsEnvironment.CreateProgram = CreateProgram
    SConsEnvironment.CreateStaticLibrary = CreateStaticLibrary
    SConsEnvironment.CreateSharedLibrary = CreateSharedLibrary
    SConsEnvironment.CreateHeaderOnlyLibrary = CreateHeaderOnlyLibrary
    SConsEnvironment.CreateTest = CreateTest
    SConsEnvironment.CreateAutoToolsProject = CreateAutoToolsProject
    #env.AddComponent = AddComponent
    SConsEnvironment.CreateDoc = CreateDoc

class ComponentDictionary:
    def __init__(self):
        components = {}
    
    def add(self, env, component):
        if not component.name.lower() == component.name:
            env.cprint('[warn] modules names should be lower case: ' + name, 'yellow')
        self.components[component.name] = component
    
    def get(self, name):
        return self.components[name]
componentGraph = ComponentDictionary()

class Component(object):
    def __init__(self, name):
        self.name = name

def CreateHeaderOnlyLibrary(env, name, inc, ext_inc, deps):
    if isPreProcessing:
        componentGraph.add(env, Component(name))
    else:
        install = env.Install(env['INSTALL_HEADERS_DIR'],ext_inc)
        env.Alias(name, install, 'Install ' + name + ' headers')

def CreateProgram(env, name, inc, src, deps):
    if isPreProcessing:
        componentGraph.add(env, Component(name))
    
def CreateTest(env, name, inc, src, deps):
    if isPreProcessing:
        componentGraph.add(env, Component(name))
    
def CreateStaticLibrary(env, name, inc, ext_inc, src, deps):
    if isPreProcessing:
        componentGraph.add(env, Component(name))
    
def CreateSharedLibrary(env, name, inc, ext_inc, src, deps):
    if isPreProcessing:
        componentGraph.add(env, Component(name))
    
def CreateAutoToolsProject(env, name, libfile, configureFile, ext_inc):
    if isPreProcessing:
        componentGraph.add(env, Component(name))
    
def CreateDoc(env, name, doxyfile=None):
    if isPreProcessing:
        componentGraph.add(env, Component(name))

def WalkDirsForSconscripts(env, topdir, ignore = []):
    for root, dirnames, filenames in os.walk(topdir):
        if ignore.count(os.path.relpath(root, topdir)) == 0:
            for filename in fnmatch.filter(filenames, 'SConscript'):
                pathname = os.path.join(root, filename)
                env.SConscript(pathname, exports='env')
