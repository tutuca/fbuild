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


""".
    The qt settings and modules loading
"""


import os


def HasQt(env):
    hasQt = False
    moc4 = env.WhereIs('moc-qt4') or env.WhereIs('moc4')
    if moc4:
        os.environ['QT4DIR'] = '/usr/share/qt4/'
        hasQt = True
    else:
        moc = env.WhereIs('moc')
        if moc:
            qtdir = os.path.split(os.path.split(moc)[0])[0]
            os.environ['QTDIR'] = qtdir
            hasQt = True
    return hasQt

def detectPkgconfigPath():
    pkgpath = '/usr/lib/x86_64-linux-gnu/pkgconfig'
    if os.path.exists(os.path.join(pkgpath,'QtCore.pc')):
        return pkgpath

    return ""
        
def init(env):
    # This is a base component, it will include the qt base include path
    QT_INCLUDE_ROOT = os.getenv(
        "QT_INCLUDE_ROOT",
        '/usr/include/qt4/'
    )
    env['QT4_GOBBLECOMMENTS']=1
    env['ENV']['PKG_CONFIG_PATH'] = detectPkgconfigPath()
    env.CreateExternalComponent(
        'QtInc',
        [env.Dir(os.getenv("QT_INCLUDE", QT_INCLUDE_ROOT))],
        env.Dir('/usr/lib/x86_64-linux-gnu'),
        [],
        False
    )

    validModules = [
        'QtCore',
        'QtGui',
        'QtOpenGL',
        'Qt3Support',
        #'QtAssistant',  # deprecated
        #'QtMultimedia', # deprecated
        #'QtAssistantClient', # deprecated
        'QtScript',
        'QtDBus',
        'QtSql',
        'QtSvg',
        # The next modules have not been tested yet so, please
        # maybe they require additional work on non Linux platforms
        'QtNetwork',
        'QtTest',
        'QtXml',
        'QtXmlPatterns',
        'QtUiTools',
        'QtDesigner',
        'QtDesignerComponents',
        'QtWebKit',
        'QtHelp',
        'QtScriptTools',
    ]
    for module in validModules:
        env.CreateExternalComponent(
            module,
            [env.Dir(os.path.join(QT_INCLUDE_ROOT, module))],
            env.Dir('/usr/lib/x86_64-linux-gnu'),
            ['QtInc'],
            True
        )
    env.EnableQt4Modules(validModules)