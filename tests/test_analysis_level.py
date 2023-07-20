"""
Created on Dec 5, 2017

@author: JGD
"""
import unittest
import cast.analysers.test


class Test(unittest.TestCase):
    def testRegisterPlugin(self):
        # instantiate a UA analyzer for 'Batch' language defined by <category name="Batch" rid="4">
        # see http://cast-projects.github.io/Extension-SDK/doc/code_reference.html?highlight=uatestanalysis#cast.analysers.test.UATestAnalysis
        analysis = cast.analysers.test.JEETestAnalysis()

        # add_selection for folder, absolute reference
        # analysis.add_selection('C:\CAST_Clients\ACMS\Development\DEV_14.2.1\CswDev\JOBS')

        # add_selection for folder under "tests" Eclipse folder, relative reference
        analysis.add_selection(r'JEESample')
        analysis.add_dependency(r'C:\ProgramData\CAST\CAST\Extensions\com.castsoftware.jee.1.3.5-funcrel')
        # analysis.add_classpath('C:\Program Files\AdoptOpenJDK\jdk-11.0.11.9-hotspot\lib')
        analysis.set_verbose()
        analysis.run()


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
