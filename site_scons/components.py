# fudepan-build: The build system for FuDePAN projects
#
# Copyright (C) 2011-2012 Esteban Papp, Hugo Arregui FuDePAN
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

from core_components import Component, headersFilter
import os

class PdfLatexComponent(Component):
    def __init__(self, componentGraph, env, name, compDir, latexfile, aliasGroups):
        Component.__init__(self, componentGraph, env, name, compDir, [], aliasGroups)
        self.latexfile = latexfile

    def Process(self):
        Component.Process(self)
        project_name = self.name.split(':')[0]
        targetDocDir = self.env.Dir(self.env['INSTALL_DOC_DIR']).Dir(project_name)
        pdf = self.env.RunPdfLatex(targetDocDir, self.latexfile)
        self.env.Clean(pdf, targetDocDir)
        self.env.Alias(self.name, pdf, 'Generate pdf from ' + self.latexfile
            + ' for ' + project_name)

        for alias in self.aliasGroups:
            self.env.Alias(alias, pdf, "Build group " + alias)

class ValgrindComponent(Component):
    def __init__(self, componentGraph, env, name, compDir, aliasGroups, project_name=""):
        Component.__init__(self, componentGraph, env, name, compDir, [], aliasGroups)
        self.project_name = project_name

    def Process(self):
        Component.Process(self)
        targetExecDir = self.env.Dir(self.env['BUILD_DIR'])\
                                .Dir(self.project_name).Dir("tests")
        txt = self.env.RunValgrind('mili.txt', targetExecDir.abspath + "/" + self.project_name + ":test")
        self.env.Clean(txt, targetExecDir)
        self.env.Alias(self.name, txt, 'Generate ' + self.project_name +
            ' memory report for ' + self.project_name)

        for alias in self.aliasGroups:
            self.env.Alias(alias, txt, "Build group " + alias)

class DocComponent(Component):
    def __init__(self, componentGraph, env, name, compDir, doxyfile, aliasGroups):
        Component.__init__(self, componentGraph, env, name, compDir, [], aliasGroups)
        self.doxyfile = doxyfile

    def Process(self):
        Component.Process(self)
        targetDocDir = self.env.Dir(self.env['INSTALL_DOC_DIR']).Dir(self.name)
        doc = self.env.RunDoxygen(targetDocDir, self.doxyfile)
        self.env.Clean(doc, targetDocDir)
        self.env.Alias(self.name, doc, 'Generate documentation for ' + self.name)

        for alias in self.aliasGroups:
            self.env.Alias(alias, doc, "Build group " + alias)

class AutoToolsProjectComponent(Component):
    def __init__(self, componentGraph, env, name, compDir, ext_dir, libTargets, configurationFile, aliasGroups):
        Component.__init__(self, componentGraph, env, name, compDir, [], aliasGroups)
        self.configurationFile = configurationFile
        self.extDir = os.path.join(self.env['WS_DIR'], self.name, ext_dir)
        self.libTargets = libTargets

    def Process(self):
        libDir = self.env.Dir(self.env['INSTALL_LIB_DIR'])
        incDir = self.env.Dir(self.env['INSTALL_HEADERS_DIR']).Dir(self.name).abspath
        self.env['INSTALL_HEADERS_DIR'] = incDir

        targets = []
        for lib in self.libTargets:
            targets.append(os.path.join(libDir.abspath, lib))

        for filter in headersFilter:
            n = os.path.join(self.extDir, filter)
            for header in self.env.Glob(n):
                filename = header.abspath[len(header.rel_path(self.extDir)) + 1:]
                targets.append(os.path.join(incDir, self.name, filename))

        make = self.env.RunMakeTool(targets, self.configurationFile)
        self.env.Clean(make, libDir.Dir(self.name))
        self.env.Alias(self.name, make, 'Make ' + self.name)

        for alias in self.aliasGroups:
            self.env.Alias(alias, make, "Build group " + alias)

    def _getLibs(self, processedComponents, depth):
        libpaths = []
        libs = []
        if depth > 0:
            libs.append(self.name)
            # For static libraries lookup:
            libpaths.append(self.env['INSTALL_LIB_DIR'])
            # For dynamic libraries lookup:
            libpaths.append(self.env['INSTALL_BIN_DIR'])
        processedComponents.append(self.name)
        return (libs, libpaths, processedComponents)

    def getIncludePaths(self):
        (incs, processedComponents) = self._getIncludePaths([], 0)
        return incs

    def _getIncludePaths(self, processedComponents, depth):
        incs = [os.path.join(self.env['INSTALL_HEADERS_DIR'], self.name)]
        processedComponents.append(self.name)
        return (incs, processedComponents)
