# fudepan-build: The build system for FuDePAN projects
#
# Copyright (C) 2011-2012 Esteban Papp, Hugo Arregui, 2013 Gonzalo Bonigo, FuDePAN
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
    Add a description here!
"""


import os

from core_components import Component


class PdfLaTeXComponent(Component):

    def __init__(self, componentGraph, env, name, compDir, latexfile, aliasGroups):
        super(PdfLaTeXComponent, self).__init__(componentGraph, env, name, compDir, [], aliasGroups)
        self.latexfile = latexfile

    def Process(self):
        docDir = "/" + self.name.split(':')[0] + ":doc/pdf/"
        targetDir = self._env.Dir(self._env['INSTALL_DOC_DIR']).Dir(docDir, True)
        pdf = self._env.RunPdfLaTeX(targetDir, self.latexfile)
        self._env.Clean(pdf, targetDir)
        self._env.Alias(self.name, pdf, 'Generate pdf from ' +
            os.path.split(self.latexfile)[-1] +
            ' for ' + self.name.split(':')[0])
        for alias in self._alias_groups:
            self._env.Alias(alias, pdf, "Build group " + alias)
