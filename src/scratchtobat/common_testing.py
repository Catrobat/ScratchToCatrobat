import os
import shutil
import tempfile
import unittest
import zipfile
from codecs import open
from xml.etree import ElementTree

import org.catrobat.catroid.io as catio
import org.catrobat.catroid.formulaeditor as catformula

from scratchtobat import sb2tocatrobat

TEST_PROJECT_URL_TO_NAME_MAP = {
#     'http://scratch.mit.edu/projects/10205819/': '10205819', # dancing in the castle
    'http://scratch.mit.edu/projects/10132588/': '10132588',  # dance back
#     'http://scratch.mit.edu/projects/10189712/': '10189712', #kick the ball
#     'http://scratch.mit.edu/projects/10530876/': '10530876', #cat has message
#    'http://scratch.mit.edu/projects/10453283/': '10453283', #  jai ho! (problem with encoding)

    }

TEST_PROJECT_FILES_TO_NAME_MAP = {
    'dancing_castle.zip': '10205819',
    'Dance back.zip': '10132588',
    }


def _rmtree_onerror_func(func, path, exc_info):
    assert os.path.exists(path), "Non existing: " + path
    func(path)


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        # FIXME: fails at jython / windows .. reason?
        # TODO: try Timer / sched workaround
        shutil.rmtree(self.temp_dir, onerror=_rmtree_onerror_func)


class ProjectTestCase(BaseTestCase):

    def assertScriptClasses(self, expected_script_class, expected_brick_classes, script):
        self.assertEqual(expected_script_class, [script.__class__], "Script class is not matching")
        bricks = script.getBrickList()
        self.assertTrue(bricks, "No bricks.")
        expected_len = len(expected_brick_classes)
        actual_len = len(bricks)
        self.assertEqual(expected_len, actual_len, "Wrong number of bricks. {0} != {1}".format(expected_len, actual_len))
        self.assertEqual(expected_brick_classes, [_.__class__ for _ in bricks])

    def assertCorrectCatroidProjectStructure(self, project_path, project_name):
        code_filename = os.path.join(project_path, sb2tocatrobat.CATROID_PROJECT_FILE)
        with open(code_filename) as fp:
            code_content = fp.read()
        self.assertTrue(code_content.startswith(catio.StorageHandler.getInstance().XML_HEADER), "Xml header missing in catroid project code")
        root = ElementTree.fromstring(code_content.encode("UTF-8"))
        self.assertEqual('program', root.tag)
        code_program_name = root.find("header/programName")
        self.assertIsNotNone(code_program_name, "code.xml corrupt: no programName set in header")
        self.assertEqual(project_name, code_program_name.text)

        sounds_dir = sb2tocatrobat.sounds_dir_of_project(project_path)
        for node in root.findall('.//sound/fileName'):
            sound_path = os.path.join(sounds_dir, node.text)
            self.assert_(os.path.exists(sound_path), "Missing: " + sound_path)

        images_dir = sb2tocatrobat.images_dir_of_project(project_path)
        for node in root.findall('.//look/fileName'):
            image_path = os.path.join(images_dir, node.text)
            self.assert_(os.path.exists(image_path), "Missing: " + image_path)

    def assertCorrectZipFile(self, catroid_zip_file_name, project_name):
        assert os.path.exists(self.temp_dir)
        temp_dir = os.path.join(self.temp_dir, "extracted_zip")
        if not os.path.exists(temp_dir):
            os.mkdir(temp_dir)

        with zipfile.ZipFile(catroid_zip_file_name) as zip_fp:
            corrupt_zip_content = zip_fp.testzip()
            self.assertTrue(corrupt_zip_content is None, "Corrupt files in {}: {}".format(catroid_zip_file_name, corrupt_zip_content))
            self.assertNotEqual(project_name, os.path.commonprefix(zip_fp.namelist())[:-1], "Wrong directory in zipped catrobat project.")

            all_nomedia_files = (".nomedia", "images/.nomedia", "sounds/.nomedia")
            for nomedia_file in all_nomedia_files:
                self.assertIn(nomedia_file, set(zip_fp.namelist()))

            zip_fp.extractall(temp_dir)
        self.assertCorrectCatroidProjectStructure(temp_dir, project_name)

    def assertEqualFormulas(self, formula1, formula2):
        assert isinstance(formula1, catformula.Formula)
        assert isinstance(formula2, catformula.Formula)

        def _compare_formula_elements(elem1, elem2):
            if not elem1 and not elem2:
                return True
            else:
                return (elem1.type == elem2.type and elem1.value == elem2.value and _compare_formula_elements(elem1.leftChild, elem2.leftChild) and
                    _compare_formula_elements(elem1.rightChild, elem2.rightChild))

        return _compare_formula_elements(formula1.formulaTree, formula2.formulaTree)
