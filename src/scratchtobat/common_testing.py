from __future__ import unicode_literals

import os
import tempfile
import unittest
import zipfile
from codecs import open
from xml.etree import ElementTree

import org.catrobat.catroid.io as catio
import org.catrobat.catroid.formulaeditor as catformula

from scratchtobat import common
from scratchtobat import sb2tocatrobat

TEST_PROJECT_URL_TO_ID_MAP = {
    'http://scratch.mit.edu/projects/10132588/': '10132588',  # dance back
    # FIXME: fails with error 'http://scratch.mit.edu/projects/10189712/': '10189712',  # kick the ball
    'http://scratch.mit.edu/projects/10205819/': '10205819',  # dancing in the castle
    'http://scratch.mit.edu/projects/10530876/': '10530876',  # cat has message
    'http://scratch.mit.edu/projects/10453283/': '10453283',  # jai ho!
}

TEST_PROJECT_FILENAME_TO_ID_MAP = {
    'dancing_castle.zip': '10205819',
    'Dance back.zip': '10132588',
}
_log = common.log


class BaseTestCase(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        _package_name, module_qualified_testcase_name = self.id().split(".", 1)
        assert module_qualified_testcase_name is not None
        self._testcase_result_folder_path = os.path.join(common.get_project_base_path(), "testoutput", module_qualified_testcase_name)
        common.makedirs(self._testcase_result_folder_path)

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        common.rmtree(self.temp_dir)


class ProjectTestCase(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        cls._storagehandler = catio.StorageHandler()

    def assertScriptClasses(self, expected_script_class, expected_brick_classes, script):
        self.assertEqual(expected_script_class, [script.__class__], "Script class is not matching")
        bricks = script.getBrickList()
        self.assertTrue(bricks, "No bricks.")
        expected_len = len(expected_brick_classes)
        actual_len = len(bricks)
        self.assertEqual(expected_len, actual_len, "Wrong number of bricks. {0} != {1}".format(expected_len, actual_len))
        self.assertEqual(expected_brick_classes, [_.__class__ for _ in bricks])

    def assertCorrectCatroidProjectStructure(self, project_path, project_name):
        project_xml_path = os.path.join(project_path, sb2tocatrobat.CATROID_PROJECT_FILE)
        with open(project_xml_path) as fp:
            self.assertEqual(fp.readline(), self._storagehandler.XML_HEADER)

        root = ElementTree.parse(project_xml_path).getroot()
        self.assertEqual('program', root.tag)

        project_name_from_xml = root.find("header/programName")
        self.assertIsNotNone(project_name_from_xml, "code.xml corrupt: no programName set in header")
        self.assertEqual(project_name, project_name_from_xml.text)

        catrobat_version_from_xml = root.find("header/catrobatLanguageVersion")
        self.assertIsNotNone(project_name_from_xml, "code.xml corrupt: no catrobatLanguageVersion set in header")
        self.assertGreater(float(catrobat_version_from_xml.text), 0.0)

        sounds_dir = sb2tocatrobat.sounds_dir_of_project(project_path)
        for node in root.findall('.//sound/fileName'):
            sound_path = os.path.join(sounds_dir, node.text)
            self.assert_(os.path.exists(sound_path), "Missing: " + sound_path)

        images_dir = sb2tocatrobat.images_dir_of_project(project_path)
        for node in root.findall('.//look/fileName'):
            image_path = os.path.join(images_dir, node.text)
            _log.info("  available files: {}".format(os.listdir(os.path.dirname(image_path))))
            self.assert_(os.path.exists(image_path), "Missing: " + image_path + ", available files: {}".format(os.listdir(os.path.dirname(image_path))))

    def assertCorrectProjectZipFile(self, zip_path, project_name):
        assert os.path.exists(self.temp_dir)
        temp_dir = os.path.join(self.temp_dir, "extracted_zip")
        if not os.path.exists(temp_dir):
            os.mkdir(temp_dir)

        with zipfile.ZipFile(zip_path) as zip_fp:
            corrupt_zip_content = zip_fp.testzip()
            self.assertTrue(corrupt_zip_content is None, "Corrupt files in {}: {}".format(zip_path, corrupt_zip_content))
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
