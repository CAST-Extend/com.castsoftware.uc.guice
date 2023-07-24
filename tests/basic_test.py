"""
Created on Aug 2, 2022

@author: KFU
"""
import unittest
import cast.analysers.test
from cast.application.test import TestKnowledgeBase
from cast.application import KnowledgeBase, create_postgres_engine
from application_level import GuiceApplicationLevel


class GuiceTest(unittest.TestCase):

    def test_01(self):
        analysis = run_analyzer_level(['guice-demo'])
        get_data_created_by_plugin(analysis)
        obj_expected = analysis.get_object_by_name('Guice Module MessageModule', 'Guice_Annotation')
        print('Found: ' + str(obj_expected))
        i = 0
        for o in analysis.get_objects_by_category('Guice_Annotation').values():
            print('Match ' + str(i) + ' : ' + str(o))
            i += 1
        # self.assertTrue(obj_interface)

    def test_application_init(self):
        engine = create_postgres_engine(port=2284)
        cast.application.test.run(kb_name='guice_demo_local', application_name='guice-demo', event='end_application', engine=engine)

    def test_application_level(self):
        engine = create_postgres_engine(port=2284)
        kb = KnowledgeBase('guice_demo_local', engine)
        app = kb.get_application(name='guice-demo')

        extension = GuiceApplicationLevel()
        application = kb.run(extension.end_application)

    def test_guice_localhost(self):
        engine = create_postgres_engine(port=2284)
        kb = KnowledgeBase('guice_demo_local', engine)
        bla = kb.get_application(name='guice-demo')
        objects = bla.objects()
        count = 0
        for object in objects.is_executable().has_type('JV_METHOD'):

            if object.get_fullname().find('com.example.') > -1:
                count += 1
                print(object.get_fullname())
                try:
                    for annotation in object.get_annotations():
                        print('     ' + str(annotation))
                except AttributeError:
                    pass

        print(str(count))


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testRegisterPlugin']
    unittest.main()


# very useful line of code do not remove
# log is located in C:\Users\%username%\AppData\Local\Temp\CAST\CAST\8.3\LTSA\log_default.castlog.tmp
def run_analyzer_level(selectionPath, verbose=False):
    analysis = cast.analysers.test.JEETestAnalysis()
    analysis.pydev_path = '';
    for item in selectionPath:
        analysis.add_selection(item)
    analysis.add_dependency(r"C:\CAST\ProgramData\CAST\CAST\Extensions\com.castsoftware.jee.1.3.12-funcrel")
    # analysis.add_dependency(r"C:\CAST\ProgramData\CAST\CAST\Extensions\com.castsoftware.internal.platform.0.9.16")
    analysis.set_verbose(verbose)
    analysis.run()
    return analysis


class MyJEETestAnalysis(cast.analysers.test.JEETestAnalysis):

    def _get_specific_options(self):
        command = cast.analysers.test.JEETestAnalysis._get_specific_options(self)
        command += ' --xml-extensions=*.xml;*.wsdl'
        return command


def get_data_created_by_plugin(analysis):
    projects = analysis.get_objects_by_category('CAST_PluginProject').items()
    if not projects:
        return {}, {}
    this_project = None
    for _, project in projects:

        if getattr(project, 'CAST_Scriptable.id') == 'com.castsoftware.ejb':
            this_project = project
            break
    objects_produced = set()
    for _, link in analysis.get_objects_by_category('isInProjectLink').items():

        if getattr(link, 'link.callee') == this_project:

            _object = getattr(link, 'link.caller')
            # skip project itself
            if getattr(_object, 'type') != 'CAST_PluginProject':
                objects_produced.add(_object)
    links_produced = set()
    for _, link in analysis.get_objects_by_property('link.project', this_project, 'link').items():
        links_produced.add(link)
    print('objects')
    for o in objects_produced:
        print('  ', o.type, getattr(o, 'identification.fullName'))
    print('links')
    for o in links_produced:
        caller = getattr(o, 'link.caller')
        callee = getattr(o, 'link.callee')
        print('  ', caller.type, getattr(caller, 'identification.fullName'), '->', callee.type,
              getattr(callee, 'identification.fullName'))
