import os
import sys
import glob
import component
            
def addQtComponents(env):
    # This is a base component, it will include the qt base include path
    QT_INCLUDE_ROOT = os.path.join( env['QTDIR'], 'include', 'qt4')
    component.AddComponent(env, 'QtInc', env.Dir(QT_INCLUDE_ROOT), [], True)
    validModules = [
        'QtCore',
        'QtGui',
        'QtOpenGL',
        'Qt3Support',
        'QtAssistant', # deprecated
        'QtAssistantClient',
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
        'QtMultimedia',
        ]
    for module in validModules:
        component.AddComponent(env, module, env.Dir(os.path.join(QT_INCLUDE_ROOT,module)), ['QtInc'], True)

