# Introduction

Fudepan-build's concept is to provide dependency handling and build uniformity using scons. It can be used as a minimalistic build environment to provide personalized build commands. 

# Fudepan-build's structure


  fudepan-build/
        projects/
        conf/
          projects.xml
        install/
        start.sh


* `projects/` is the directory where the code of each project will be stored. 
* `conf/` configuration files.
* `conf/projects.xml` contains each project's configuration, download url and other necessary information.
* `install/` the default installation directory.
* `start.sh` Must be run before using Fbuild. This script set the work environment.

# Usage

The first step must always be to run start.sh at Fbuild's root folder. 

    $ source start.sh

To download a project (listed in projects.xml):

    $ fbuild <nombre-proyecto>:checkout

This will download all project folders and files into projects.

To build the project:

    $ fbuild <nombre-proyecto> 

To run a project's tests:

    $ fbuild <nombre-proyecto>:test 

By default, fudepan-build uses install as its reduced environment, so all libs, binaries, includes and any other generated files should be installed there, avoiding the pollution of the projects directory.

    $ fbuild install <nombre-proyecto> 

You may redefine the installation directories, for instance:

    $ fbuild INSTALL_HEADERS_DIR=/usr/local/include/ INSTALL_BIN_DIR=/usr/local/bin/ INSTALL_LIB_DIR=/usr/local/lib/ 

To clean all files generated during a target's build:

    $ fbuild -c <target>

To see all available targets:

    $ fbuild targets

To get a test coverage report:

    $ fbuild <proyecto>:coverage

To see scons help:

    $ fbuild --help

To see how the target is built:

    $ fbuild --verbose <target>

# "Sconscifying" a project

There are 5 basic types of builders:

* Header only
* Static Library
* Shared Library
* Program
* Test

In general, and to be structured, a project will has the following structure:

    project-name/
      project-name/         <--- will has the project headers.
      src/
      tests/
          SConscript
      SConscript

Examples of every project's type:

* Header Only: [mili](http://code.google.com/p/mili/)
* Static Library: [getoptpp](http://code.google.com/p/getoptpp/)
* Shared Library: [biopp](http://code.google.com/p/biopp/)
* Program: [backbones-generator](http://code.google.com/p/backbones-generator/)

# Environment variables

Some environment variables to consider:

Qt (Arch example, for Ubuntu this is not necessary):

    export QT_INCLUDE_ROOT=/usr/include
    export QT_INCLUDE=/usr/include/Qt

# Tips

Edit your .bashrc file (located in /home/YOUR_USERNAME) with an alias such as this:

    alias go-fbuild='cd /home/YOUR_USERNAME/PATH_TO_FBUILD/; source start.sh; export LDFLAGS="-L/usr/local/$(uname -m)-linux-gnu" '
