from core_components import Component

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
    def __init__(self, componentGraph, env, name, compDir, configurationFile, aliasGroups):
        Component.__init__(self, componentGraph, env, name, compDir, [], aliasGroups)
        self.configurationFile = configurationFile

    def Process(self):
        Component.Process(self)
        targetMake = self.env.Dir(self.env['INSTALL_LIB_DIR']).Dir(self.name)
        make = self.env.RunMakeTool(targetMake, self.configurationFile)
        self.env.Clean(make, targetMake)
        self.env.Alias(self.name, make, 'Make ' + self.name)

        for alias in self.aliasGroups:
            self.env.Alias(alias, make, "Build group " + alias)

