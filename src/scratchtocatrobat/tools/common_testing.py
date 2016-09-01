#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2015 The Catrobat Team
#  (http://developer.catrobat.org/credits)
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
#  along with this program.  If not, see http://www.gnu.org/licenses/.
from __future__ import unicode_literals

import glob
import os
import sys
import shutil
import tempfile
import unittest
import zipfile
from codecs import open
from java.io import BufferedReader, InputStreamReader
from java.lang import ProcessBuilder, StringBuilder, System
from xml.etree import ElementTree

import org.catrobat.catroid.common as catcommon
import org.catrobat.catroid.content as catbase
import org.catrobat.catroid.io as catio
import org.catrobat.catroid.formulaeditor as catformula

from scratchtocatrobat.converter import catrobat
from scratchtocatrobat.tools import common
from scratchtocatrobat.converter import converter

assert System.getProperty("python.security.respectJavaAccessibility") == 'false', "Jython registry property 'python.security.respectJavaAccessibility' must be set to 'false'"

TEST_PROJECT_URL_TO_ID_MAP = {
    'https://scratch.mit.edu/projects/10132588/': '10132588',  # dance back
    # FIXME: fails with error 'http://scratch.mit.edu/projects/10189712/': '10189712',  # kick the ball
    'https://scratch.mit.edu/projects/10205819/': '10205819',  # dancing in the castle
    'https://scratch.mit.edu/projects/10530876/': '10530876',  # cat has message
    'https://scratch.mit.edu/projects/10453283/': '10453283',  # jai ho!
}
TEST_PROJECT_FILENAME_TO_ID_MAP = {
    'dancing_castle.zip': '10205819',
    'Dance back.zip': '10132588'
}
PROJECT_DUMMY_ID = "1013258"  # dance back
# TODO: parse from Java annotations
FIELD_NAMES_TO_XML_NAMES = {"virtualScreenWidth": "screenWidth", "virtualScreenHeight": "screenHeight"}
IGNORED_XML_HEADER_CLASS_FIELDS = ["serialVersionUID"]
OPTIONAL_HEADER_TAGS = ["dateTimeUpload", "description", "tags", "url", "userHandle"]

_log = common.log


def get_test_resources_path(*path_parts):
    return os.path.join(common.get_project_base_path(), "test", "res", *path_parts)


def get_test_project_path(*path_parts):
    return os.path.join(get_test_resources_path(), "scratch", *path_parts)


def get_test_project_packed_file(scratch_file):
    return os.path.join(get_test_resources_path(), "scratch_packed", scratch_file)


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

    @classmethod
    def get_test_resources_paths(cls, *args):
        target_resource_path = get_test_resources_path(*args)
        return [_ for _ in glob.glob(os.path.join(target_resource_path, "*"))]


class ProjectTestCase(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super(ProjectTestCase, cls).setUpClass()
        cls._storagehandler = catio.StorageHandler()

    def assertScriptClasses(self, expected_script_class, expected_brick_classes, script):
        assert [script.__class__] == expected_script_class
        bricks = script.getBrickList()
        assert bricks
        assert len(bricks) == len(expected_brick_classes)
        assert [brick.__class__ for brick in bricks] == expected_brick_classes

    def __assertTagsAreNonempty(self, xml_root):
        header_tags = [FIELD_NAMES_TO_XML_NAMES[field] if field in FIELD_NAMES_TO_XML_NAMES else field for field in common.fields_of(catbase.XmlHeader) if field not in IGNORED_XML_HEADER_CLASS_FIELDS]
        mandatory_header_tags = set(header_tags) - set(OPTIONAL_HEADER_TAGS)
        for header_tag in header_tags:
            tag = "header/" + header_tag
            xml_node = xml_root.find(tag)
            assert xml_node is not None, "XML file error: tag '{}' must be available".format(tag)
            if header_tag in mandatory_header_tags:
                assert xml_node.text is not None, "XML file error: Value for tag '{}' must be set".format(tag)
                if header_tag == "screenMode":
                    assert xml_node.text == catcommon.ScreenModes.STRETCH.toString()  # @UndefinedVariable
                elif header_tag == "remixOf":
                    try:
                        with tempfile.NamedTemporaryFile() as temp:
                            common.download_file(xml_node.text, temp.name)
                            with open(temp.name, "r") as f:
                                assert f.read() is not None
                    except:
                        self.fail("Expection '{}' with url '{}'".format(sys.exc_info()[0], xml_node.text))

    def assertValidCatrobatProgramStructure(self, project_path, project_name):
        project_xml_path = os.path.join(project_path, catrobat.PROGRAM_SOURCE_FILE_NAME)
        with open(project_xml_path) as fp:
            assert fp.readline() == self._storagehandler.XML_HEADER

        root = ElementTree.parse(project_xml_path).getroot()
        assert root.tag == 'program'
        self.__assertTagsAreNonempty(root)

        project_name_from_xml = root.find("header/programName")
        assert project_name_from_xml.text == project_name

        catrobat_version_from_xml = root.find("header/catrobatLanguageVersion")
        assert float(catrobat_version_from_xml.text) > 0.0

        # TODO: refactor duplication
        sounds_dir = converter.ConvertedProject._sounds_dir_of_project(project_path)
        for node in root.findall('.//sound/fileName'):
            sound_path = os.path.join(sounds_dir, node.text)
            assert os.path.exists(sound_path)

        images_dir = converter.ConvertedProject._images_dir_of_project(project_path)
        for node in root.findall('.//look/fileName'):
            image_path = os.path.join(images_dir, node.text)
            assert os.path.exists(image_path), "Missing: {}, available files: {}".format(repr(image_path), os.listdir(os.path.dirname(image_path)))

    def assertValidCatrobatProgramPackageAndUnpackIf(self, zip_path, project_name, unused_scratch_resources=None):
        if unused_scratch_resources is None:
            unused_scratch_resources = []
        _log.info("unused resources: %s", ', '.join(unused_scratch_resources))
        package_extraction_dir = os.path.splitext(zip_path)[0]
        with zipfile.ZipFile(zip_path) as zip_fp:
            assert zip_fp.testzip() is None
            assert project_name != os.path.commonprefix(zip_fp.namelist())[:-1], "Wrong directory in zipped catrobat project."
            all_nomedia_files = (".nomedia", "images/.nomedia", "sounds/.nomedia")
            for nomedia_file in all_nomedia_files:
                assert nomedia_file in set(zip_fp.namelist())
            for unused_scratch_resource in unused_scratch_resources:
                for zip_filepath in zip_fp.namelist():
                    assert os.path.splitext(unused_scratch_resource)[0] not in zip_filepath
            zip_fp.extractall(package_extraction_dir)
        self.assertValidCatrobatProgramStructure(package_extraction_dir, project_name)

    def assertEqualFormulas(self, formula1, formula2):
        assert isinstance(formula1, catformula.Formula)
        assert isinstance(formula2, catformula.Formula)

        def _compare_formula_elements(elem1, elem2):
            if not elem1 and not elem2:
                return True
            else:
                return (elem1.type == elem2.type and elem1.value == elem2.value and _compare_formula_elements(elem1.leftChild, elem2.leftChild) and _compare_formula_elements(elem1.rightChild, elem2.rightChild))

        return _compare_formula_elements(formula1.formulaTree, formula2.formulaTree)


def call_returning_exit_and_output(exec_args, **popen_args):
    def readInputStream(inputStream):
        reader = BufferedReader(InputStreamReader(inputStream))
        builder = StringBuilder()
        line = None
        while True:
            line = reader.readLine()
            if line is None:
                break
            builder.append(line)
            builder.append(System.getProperty("line.separator"))
        return builder.toString()

    # WORKAOUND: because capturing output of Jython's subprocess module at testing with
    # pytest is not possible using Java implementation
    pb = ProcessBuilder(exec_args)
    env = popen_args.get('env')
    if env:
        process_env = pb.environment()
        for key in list(process_env.keySet()):
            if key not in env:
                _log.debug("remove from process-env: %s", key)
                process_env.remove(key)
        for key in env:
            process_env.put(key, env[key])
    pb.redirectErrorStream(True)
    process = pb.start()
    stdout = readInputStream(process.getInputStream())
    exitValue = process.waitFor()
    return exitValue, (stdout, stdout)

