# fudepan-build: The build system for FuDePAN projects
#
# Copyright (C) 2013 Gonzalo Bonigo, FuDePAN
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

__doc__ = \
"""
    This package contains the classes hierarchy for the components of the system.
"""

__package__ = 'core_components'

__version__ = 1.0

__all__ = [
    "Component",
    "ExternalComponent",
    "ProjectComponent",
    "HeaderOnlyComponent",
    "SourcedComponent",
    "ObjectComponent",
    "LibraryComponent",
    "ProgramComponent",
    "SharedLibraryComponent",
    "StaticLibraryComponent",
    "UnitTestComponent"
]

from component import Component
from external_component import ExternalComponent
from project_component import ProjectComponent
from header_only_component import HeaderOnlyComponent
from sourced_component import SourcedComponent
from object_component import ObjectComponent
from library_component import LibraryComponent
from program_component import ProgramComponent
from shared_library_component import SharedLibraryComponent
from static_library_component import StaticLibraryComponent
from test_component import UnitTestComponent
