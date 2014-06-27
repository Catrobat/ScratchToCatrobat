#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2014 The Catrobat Team
#  (<http://developer.catrobat.org/credits>)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  An additional term exception under section 7 of the GNU Affero
#  General Public License, version 3, is available at
#  http://developer.catrobat.org/license_additional_term
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals

import os
import shutil
import tempfile
import unittest
import zipfile
from codecs import open
from java.lang import System
from xml.etree import ElementTree

import org.catrobat.catroid.io as catio
import org.catrobat.catroid.formulaeditor as catformula

from scratchtocatrobat import catrobat
from scratchtocatrobat import common
from scratchtocatrobat import converter

assert System.getProperty("python.security.respectJavaAccessibility") == 'false', "Jython registry property 'python.security.respectJavaAccessibility' must be set to 'false'"

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
        super(BaseTestCase, self).setUp()
        self.temp_dir = tempfile.mkdtemp(prefix="stc_")
        class_name, testcase_name = self.id().split(".")[-2:]
        assert class_name is not None and testcase_name is not None
        self.__testresult_base_path = os.path.join(common.get_project_base_path(), "testresult", class_name, testcase_name)
        if os.path.exists(self.__testresult_base_path):
            shutil.rmtree(self.__testresult_base_path)
        self.__testresult_folder_subdir = None

    def tearDown(self):
        super(BaseTestCase, self).tearDown()
        shutil.rmtree(self.temp_dir)

    @property
    def _testresult_folder_path(self):
        folder_path = self.__testresult_base_path
        if self.__testresult_folder_subdir is not None:
            folder_path = os.path.join(folder_path, self.__testresult_folder_subdir)
        common.makedirs(folder_path)
        return folder_path

    def _set_testresult_folder_subdir(self, dirname):
        self.__testresult_folder_subdir = dirname

    def failOnMissingException(self):
        self.fail("Exception not thrown")


class ProjectTestCase(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super(ProjectTestCase, cls).setUpClass()
        cls._storagehandler = catio.StorageHandler()

    def assertScriptClasses(self, expected_script_class, expected_brick_classes, script):
        self.assertEqual(expected_script_class, [script.__class__], "Script class is not matching")
        bricks = script.getBrickList()
        self.assertTrue(bricks, "No bricks.")
        expected_len = len(expected_brick_classes)
        actual_len = len(bricks)
        self.assertEqual(expected_len, actual_len, "Wrong number of bricks. {0} != {1}".format(expected_len, actual_len))
        self.assertEqual(expected_brick_classes, [_.__class__ for _ in bricks])

    def assertValidCatrobatProgramStructure(self, project_path, project_name):
        project_xml_path = os.path.join(project_path, catrobat.PROGRAM_SOURCE_FILE_NAME)
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

        # TODO: refactor duplication
        sounds_dir = converter.sounds_dir_of_project(project_path)
        for node in root.findall('.//sound/fileName'):
            sound_path = os.path.join(sounds_dir, node.text)
            self.assert_(os.path.exists(sound_path), "Missing: " + sound_path)

        images_dir = converter.images_dir_of_project(project_path)
        for node in root.findall('.//look/fileName'):
            image_path = os.path.join(images_dir, node.text)
            self.assert_(os.path.exists(image_path), "Missing: {}, available files: {}".format(repr(image_path), os.listdir(os.path.dirname(image_path))))

    def assertValidCatrobatProgramPackageAndUnpackIf(self, zip_path, project_name, unused_scratch_resources=None):
        if unused_scratch_resources is None:
            unused_scratch_resources = []
        _log.info("unused resources: %s", ', '.join(unused_scratch_resources))
        package_extraction_dir = os.path.splitext(zip_path)[0]
        with zipfile.ZipFile(zip_path) as zip_fp:
            corrupt_zip_content = zip_fp.testzip()
            self.assertTrue(corrupt_zip_content is None, "Corrupt files in {}: {}".format(zip_path, corrupt_zip_content))
            self.assertNotEqual(project_name, os.path.commonprefix(zip_fp.namelist())[:-1], "Wrong directory in zipped catrobat project.")
            all_nomedia_files = (".nomedia", "images/.nomedia", "sounds/.nomedia")
            for nomedia_file in all_nomedia_files:
                self.assertIn(nomedia_file, set(zip_fp.namelist()))
            for unused_scratch_resource in unused_scratch_resources:
                for zip_filepath in zip_fp.namelist():
                    self.assertNotIn(os.path.splitext(unused_scratch_resource)[0], zip_filepath)
            zip_fp.extractall(package_extraction_dir)
        self.assertValidCatrobatProgramStructure(package_extraction_dir, project_name)

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
