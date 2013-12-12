# fudepan-build: The build system for FuDePAN projects
#
# Copyright (C) 2011-2012 Esteban Papp, Hugo Arregui,
#               2013 Gonzalo Bonigo, Gustavo Ojeda FuDePAN
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


class ComponentsGraph(dict):
    """
    Keeps track of registered components.
    Checks that components are not registered twice.
    There should be only one instance (Singleton).
    """
    def __setitem__(self, key, component, check=True):
        if check:
            if not component.name.islower():
                component.env.Cprint(
                    '[warn] modules names should be lower case: {}'.format(component.name), 
                    'yellow')
        # Its possible that a component is tried to be added twice because a new
        # dependency was downloaded and
        if key not in self:
            self[key] = component
            return component
        else:
            component.env.Cprint(
                '[warn] component tried to be re-added {}'.format(key), 
                'yellow')

DEPENDENCY_GRAPH = {}
COMPONENT_GRAPH = ComponentsGraph()
