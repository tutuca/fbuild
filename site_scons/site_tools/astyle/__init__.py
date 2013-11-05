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

import SCons.Action
import SCons.Builder
import SCons.Util

class ToolAstyleWarning(SCons.Warnings.Warning):
    pass

class AstyleCompilerNotFound(ToolAstyleWarning):
    pass

SCons.Warnings.enableWarningClass(ToolAstyleWarning)


def _detect(env):
    """ Try to detect the ASTYLE """
    try: 
        return env['ASTYLE']
    except KeyError: 
        pass

    astyle = env.WhereIs('astyle')
    if astyle:
        return astyle

    raise SCons.Errors.StopError(
        AstyleCompilerNotFound,
        "Could not detect ASTYLE") ## surely we could detect the platform and install the package here...
    return None

def _astyle_emitter(target, source, env):
    return target, [f for f in source if 'test/ref' not in f.abspath]

_astyle_builder = SCons.Builder.Builder(
        action = SCons.Action.Action('$ASTYLE_COM','$ASTYLE_COMSTR'),
        emitter = _astyle_emitter)

def generate(env):
    """Add Builders and construction variables to the Environment."""
    env['ASTYLE'] = _detect(env)
    env.SetDefault(
        # ASTYLE command
        ASTYLE_COM = '$ASTYLE -k1 --options=none --convert-tabs -bSKpUH $SOURCES',
        ASTYLE_COMSTR = ''
        )

    env['BUILDERS']['RunAStyle'] = _astyle_builder

def exists(env):
    return _detect(env)