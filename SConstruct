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
          help='type of build, options: debug (default), opt',
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
INSTALL_DIR = os.path.join(env.Dir('#').abspath, "install")
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
        INSTALL_DIR,
        PathVariable.PathIsDirCreate))
vars.AddVariables(
    PathVariable(
        'INSTALL_HEADERS_DIR',
        'install headers directory',
        os.path.join(INSTALL_DIR, "includes"),
        PathVariable.PathIsDirCreate))
vars.AddVariables(
    PathVariable(
        'INSTALL_LIB_DIR',
        'install libs directory',
        os.path.join(INSTALL_DIR, "libs"),
        PathVariable.PathIsDirCreate))
vars.AddVariables(
    PathVariable(
        'BUILD_SCRIPTS_DIR',
        'site_scons directory',
        os.path.join(env.Dir('#').abspath, "site_scons"),
        PathVariable.PathIsDirCreate))

vars.Update(env)

# Add the script paths so is easier to find the py modules
sys.path.append(env['BUILD_SCRIPTS_DIR'])

# Some environment tunnings so this runs faster
env.Decider( 'MD5-timestamp' )
env.SConsignFile()

# Let the default to do nothing
env.Default()

# Compiler options
import compiler
compiler.loadCompilerOptions(env)

# Linker options
import linker
linker.loadLinkOptions(env)

# Include the aliases helper
import helpfromaliases
env.AliasesHelpHead('\nTargets:')
env.AliasesHelpFoot('')
env.AlwaysBuild(env.Alias('targets', [], env.AliasesPrintHelp))

# Wrapper functions to build target types
from SCons.Script.SConscript import SConsEnvironment
import component
SConsEnvironment.CreateProgram = component.CreateProgram
SConsEnvironment.CreateStaticLibrary = component.CreateStaticLibrary
SConsEnvironment.CreateSharedLibrary = component.CreateSharedLibrary
SConsEnvironment.CreateHeaderOnlyLibrary = component.CreateHeaderOnlyLibrary
SConsEnvironment.CreateTest = component.CreateTest
SConsEnvironment.CreateAutoToolsProject = component.CreateAutoToolsProject
SConsEnvironment.AddComponent = component.AddComponent
SConsEnvironment.CreateDoc = component.CreateDoc

import recursive_install
SConsEnvironment.RecursiveInstall = recursive_install.RecursiveInstall
# Register builders
# Register tools
env.Tool('doxygen')
env.Tool('makebuilder')

# Create a builder for tests
import builders
bld = Builder(action = builders.runTest)
configure = Builder(action = builders.configure)
env.Append(BUILDERS = {'Test':  bld, 'Configure': configure})

# Add Qt
import qtutil
qtutil.preDetectQt(env)
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
env.cprint = termcolor.cprint

# call to fudepan.py where
import fudepan
fudepan.setDefines(env)

env.cprint('Install information:', 'green')
env.cprint('    bin dir    : ' + env['INSTALL_BIN_DIR'], 'green')
env.cprint('    lib dir    : ' + env['INSTALL_LIB_DIR'], 'green')
env.cprint('    headers dir: ' + env['INSTALL_HEADERS_DIR'], 'green')

# Walk over the tree finding components
from component import WalkDirsForComponents
WalkDirsForComponents(env, topdir = env['WS_DIR'],
                      ignore = [
                               'gmock/scons',
                               # The following exclusions are used when testing the build environment
                               # previously, the user copies from #/test the buildtest folder inside
                               # projects so scons can detect it
                               'projects/buildtest/test_doc',
                               'projects/buildtest/test_program',
                               'projects/buildtest/test_program/test_ut',
                               'projects/buildtest/test_qt',
                               'projects/buildtest/test_shared',
                               'projects/buildtest/test_static',
                               'projects/buildtest/test_ut',
                               'projects/buildtest/test_ut/test_ut'
                               ])

component.initializeDependencies(env)

for target in list(component.components): #make a copy
    component.process(env, target)

