from codecs import open
from scratchtobat import converter
from xml.etree import ElementTree
import org.catrobat.catroid.io as catio
import os
import unittest
import zipfile

TEST_PROJECT_URL_TO_NAME_MAP = {
#     'http://scratch.mit.edu/projects/10205819/': '10205819',
    'http://scratch.mit.edu/projects/10132588/': '10132588',
    'http://scratch.mit.edu/projects/10203872/': '10203872',
#     'http://scratch.mit.edu/projects/10189712/': '10189712',
#     'http://scratch.mit.edu/projects/10530876/': '10530876',
   'http://scratch.mit.edu/projects/10453283/':  '10453283',
   
    }


def get_test_resources_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test/res"))


def get_test_project_path(project_folder):
    return os.path.join(get_test_resources_path(), "sb2", project_folder)


class ScratchtobatTestCase(unittest.TestCase):
    
    def assertScriptClasses(self, expected_script_class, expected_brick_classes, script):
        self.assertEqual(expected_script_class, [script.__class__], "Script class is not matching")
        bricks = script.getBrickList()
        self.assertTrue(bricks, "No bricks.")
        self.assertEqual(len(expected_brick_classes), len(bricks), "Wrong number of bricks.")
        self.assertEqual(expected_brick_classes, [_.__class__ for _ in bricks], "Wrong brick classes.")
    
    def assertCorrectCatroidProjectStructure(self, project_path, project_name):
        code_filename = os.path.join(project_path, converter.CATROID_PROJECT_FILE)
        with open(code_filename) as fp:
            code_content = fp.read()
            self.assertTrue(code_content.startswith(catio.StorageHandler.getInstance().XML_HEADER), "Xml header missing in catroid project code")
            print type(code_content), repr(code_content)
            root = ElementTree.fromstring(code_content.encode("UTF-8"))
            self.assertEqual('program', root.tag)
            code_program_name = root.find("header/programName")
            self.assertIsNotNone(code_program_name, "code.xml corrupt: no programName set in header")
            self.assertEqual(project_name, code_program_name.text,)
            
    def assertCorrectZipFile(self, catroid_zip_file_name, project_name):
        with zipfile.ZipFile(catroid_zip_file_name) as zip_fp:
            corrupt_zip_content = zip_fp.testzip()
            self.assertTrue(corrupt_zip_content is None, "Corrupt files in {}: {}".format(catroid_zip_file_name, corrupt_zip_content))
            self.assertEqual(project_name, os.path.commonprefix(zip_fp.namelist())[:-1], "Wrong project name of zipped catroid project.")
            # zipfile does not support windows' backslashes
            code_filename = project_name + "/" + converter.CATROID_PROJECT_FILE
            self.assertIn(code_filename, set(zip_fp.namelist()))
            
            all_nomedia_files = (project_name + "/" + _ for _ in (".nomedia", "images/.nomedia", "sounds/.nomedia"))
            for nomedia_file in all_nomedia_files:
                self.assertIn(nomedia_file, set(zip_fp.namelist()))
            
            code_content = zip_fp.read(code_filename)
            self.assertTrue(code_content.startswith(catio.StorageHandler.getInstance().XML_HEADER), "Xml header missing in catroid project code")
            print type(code_content), repr(code_content)
            root = ElementTree.fromstring(code_content.encode("UTF-8"))
            self.assertEqual('program', root.tag)
            code_program_name = root.find("header/programName")
            self.assertIsNotNone(code_program_name, "code.xml corrupt: no programName set in header")
            self.assertEqual(project_name, code_program_name.text,)