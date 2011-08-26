# FuDePan boilerplate required here

import os
import platform
import sys
import SCons

env = Environment()
Export('env')

# SCons configuration options
# Add parallelism to the build system
from multiprocessing import cpu_count
SetOption('num_jobs', cpu_count() + 1)

# Add options
AddOption('--type',
          dest='type', 
          type='string',
          nargs=1,
          action='store',
          help='type of build, options: dbg (default), opt',
          default='debug')

(arch,binType) = platform.architecture()
# Specific linux options
if binType == 'ELF':
	AddOption('--effective',
			  dest='effective',
	          action='store_true',
	          help='Sets the effective C++ mode',
	          default=False)
	AddOption('--gprofile',
	          dest='gprofile',
	          action='store_true',
	          help='Sets the -pg flag to enable gprof',
	          default=False)
	AddOption('--gcoverage',
	          dest='gcoverage',
	          action='store_true',
	          help='Sets the required flags to enable gcov',
	          default=False)

# Add variables, this variables can be introduced through a file or
# can be introduced via command line
vars = Variables('SConfig')
# Get the scons root path, this can be tricky because 
# scons can be ran with the -v option
vars.AddVariables(
    PathVariable(
        'WS_DIR',
        'workspace directory',
        env.Dir('#/projects').abspath,
        PathVariable.PathIsDirCreate))
vars.AddVariables(
    PathVariable(
        'BUILD_DIR',
        'build directory',
        os.path.join(env.Dir('#').abspath, "build"),
        PathVariable.PathIsDirCreate))
vars.AddVariables(
    PathVariable(
        'INSTALL_BIN_DIR',
        'install bin directory',
        os.path.join(env.Dir('#').abspath, "install"),
        PathVariable.PathIsDirCreate))
vars.AddVariables(
    PathVariable(
        'INSTALL_HEADERS_DIR',
        'install headers directory',
        os.path.join(env.Dir('#').abspath, "install/includes"),
        PathVariable.PathIsDirCreate))
vars.AddVariables(
    PathVariable(
        'INSTALL_LIB_DIR',
        'install libs directory',
        os.path.join(env.Dir('#').abspath, "install/libs"),
        PathVariable.PathIsDirCreate))

vars.AddVariables(
    PathVariable(
        'BUILD_SCRIPTS_DIR',
        'site_scons directory',
        os.path.join(env.Dir('#').abspath, "site_scons"),
        PathVariable.PathIsDirCreate))

vars.Update(env)

print "install bin dir    : " + env['INSTALL_BIN_DIR']
print "install lib dir    : " + env['INSTALL_LIB_DIR']
print "install headers dir: " + env['INSTALL_HEADERS_DIR']

# Add the script paths so is easier to find the py modules
sys.path.append(env['BUILD_SCRIPTS_DIR'])

# Some environment tunnings so this runs faster
env.Decider( 'MD5-timestamp' )
env.SConsignFile()

# Compiler options
import compiler
compiler.loadCompilerOptions(env)

# Linker options
import linker
linker.loadLinkOptions(env)

# Wrapper functions to build target types
from SCons.Script.SConscript import SConsEnvironment
import component
SConsEnvironment.CreateProgram = component.CreateProgram
SConsEnvironment.CreateStaticLibrary = component.CreateStaticLibrary
SConsEnvironment.CreateSharedLibrary = component.CreateSharedLibrary
SConsEnvironment.CreateHeaderOnlyLibrary = component.CreateHeaderOnlyLibrary
SConsEnvironment.CreateTest = component.CreateTest
SConsEnvironment.AddComponent = component.AddComponent

# Register builders
# Register tools
env.Tool('doxygen')
env.Tool('makebuilder')

# Create a builder for tests
import builders
bld = Builder(action = builders.runTest)
env.Append(BUILDERS = {'Test' :  bld})

# Add Qt
import qtutil
env.Tool('qt')
qtutil.addQtComponents(env)
import boostutil
boostutil.addBoostComponents(env)

# Add OS Components
import linux
linux.addOSComponents(env)

# Color pretty printing
import termcolor
if ARGUMENTS.get('VERBOSE') != '1':
    termcolor.prettyMessages(env)

# call to fudepan.py where 
import fudepan
fudepan.setDefines(env)

# Walk over the tree finding components
from component import WalkDirsForComponents
WalkDirsForComponents(env, topdir = env['WS_DIR'], 
                      ignore = [
                               'gmock/scons',
                               'buildtest/test_doc',
                               'buildtest/test_program',
                               'buildtest/test_program/test_ut',
                               'buildtest/test_qt',
                               'buildtest/test_shared',
                               'buildtest/test_static',
                               'buildtest/test_ut',
                               'buildtest/test_ut/test_ut'
                               ])

component.initializeDependencies(env)

for target in list(component.components): #make a copy
    component.process(env, target)
