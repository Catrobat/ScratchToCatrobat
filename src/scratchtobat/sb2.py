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
import glob
import itertools
import json
import os

from scratchtobat import common

log = common.log

LICENSE_URI = "http://creativecommons.org/licenses/by-sa/2.0/deed.en"
SCRIPT_GREEN_FLAG, SCRIPT_RECEIVE, SCRIPT_KEY_PRESSED, SCRIPT_SENSOR_GREATER_THAN, SCRIPT_SCENE_STARTS, SCRIPT_CLICKED = SCRATCH_SCRIPTS = \
    ["whenGreenFlag", "whenIReceive", "whenKeyPressed", "whenSensorGreaterThan", "whenSceneStarts", "whenClicked", ]
SCRATCH_PROJECT_CODE_FILE = "project.json"
STAGE_OBJECT_NAME = "Stage"
STAGE_HEIGHT_IN_PIXELS = 360
STAGE_WIDTH_IN_PIXELS = 480


class JsonKeys(object):
    # TODO: remove '_KEY' suffix
    BASELAYERID_KEY = "baseLayerID"
    CHILDREN_KEY = "children"
    COSTUME_MD5 = "baseLayerMD5"
    COSTUME_RESOLUTION = "bitmapResolution"
    COSTUMENAME_KEY = "costumeName"
    COSTUMES_KEY = "costumes"
    INFO_KEY = "info"
    OBJNAME_KEY = "objName"
    SCRIPTS_KEY = "scripts"
    SOUND_MD5 = "md5"
    SOUNDID_KEY = "soundID"
    SOUNDNAME_KEY = "soundName"
    SOUNDS_KEY = "sounds"


class Project(object):

    def __init__(self, input_path, name=None):
        def read_md5_to_resource_path_mapping():
            md5_to_resource_path_map = {}
            for project_file_path in glob.glob(os.path.join(input_path, "*")):
                resource_name = common.md5_hash(project_file_path) + os.path.splitext(project_file_path)[1]
                md5_to_resource_path_map[resource_name] = project_file_path
            try:
                # penLayer is no regular resource file
                del md5_to_resource_path_map[self.project_code['penLayerMD5']]
            except KeyError:
                # TODO: include penLayer download in webapi
                pass
            return md5_to_resource_path_map

        def verify_resources(resources):
            for res_dict  in resources:
                assert JsonKeys.SOUND_MD5 in res_dict or JsonKeys.COSTUME_MD5 in res_dict
                md5_file = res_dict[JsonKeys.SOUND_MD5] if JsonKeys.SOUNDNAME_KEY in res_dict else res_dict[JsonKeys.COSTUME_MD5]
                resource_md5 = os.path.splitext(md5_file)[0]
                if not md5_file in self.md5_to_resource_path_map:
                    raise ProjectError("Missing resource file at project: {}. Provide resource with md5: {}".format(input_path, resource_md5))

        log.info("Loading Scratch project from '%s'", input_path)

        try:
            self.project_code = ProjectCode(input_path)
        except ProjectCodeError as e:
            raise ProjectError(e)
        # TODO: create and use project API wrapper to access
        if name:
            self.name = name
        else:
            self.name = self.project_code.get_info().get("projectID")
        if not self.name:
            raise ProjectError("No project name specified in project file. Please provide project name with constructor.")

        # TODO: move whole block including the two functions to ProjectCode
        self.md5_to_resource_path_map = read_md5_to_resource_path_mapping()
        assert self.project_code['penLayerMD5'] not in self.md5_to_resource_path_map
        for sb2_object in self.project_code.objects:
            # TODO: rename to verify_object?
            verify_resources(sb2_object.get_sounds() + sb2_object.get_costumes())

        listened_keys = []
        for object_ in self.project_code.objects:
            for script in object_.scripts:
                if script.type == SCRIPT_KEY_PRESSED:
                    assert len(script.arguments) == 1
                    listened_keys += script.arguments
        self.listened_keys = set(listened_keys)
        # TODO: rename
        self.background_md5_names = set([costume[JsonKeys.COSTUME_MD5] for costume in self.project_code.stage_object.get_costumes()])
        self.unused_resource_names, self.unused_resource_paths = common.pad(zip(*self.project_code.find_unused_resources_name_and_filepath()), 2, [])
        for unused_path in self.unused_resource_paths:
            log.warning("Project folder contains unused resource file: '%s'. These will be omitted for Catrobat project.", os.path.basename(unused_path))


# TODO: do not use DictAccessWrapper
class ProjectCode(common.DictAccessWrapper):

    def __init__(self, input_path):
        json_path = os.path.join(input_path, SCRATCH_PROJECT_CODE_FILE)
        if not os.path.exists(json_path):
            raise EnvironmentError("Project file not found: {}. Please create.".format(json_path))
        self.input_path = input_path
        self.json_path = json_path
        json_dict = self.load_json_file(self.json_path)
        super(ProjectCode, self).__init__(json_dict)
        self.objects_data = [_ for _ in self.get_children() if "objName" in _]
        self.objects = [Object(_) for _ in [json_dict] + self.objects_data]
        self.stage_object = self.objects[0]
        self.nonstate_objects = self.objects[1:]
        self.resource_names = {self._resource_name_from(_) for _ in self._resources_of_objects()}

    def load_json_file(self, json_file):
        if not os.path.exists(json_file):
            raise ProjectError("Provide project data file: {}".format(json_file))
        with open(json_file, "r") as fp:
            json_dict = json.load(fp)
            self.verify_scratch_json(json_dict)
            return json_dict

    def verify_scratch_json(self, json_dict):
        # FIXME: check which tags are really required
        for key in ["objName", "info", "currentCostumeIndex", "penLayerMD5", "tempoBPM", "videoAlpha", "children", "costumes", "sounds"]:
            if not key in json_dict:
                raise ProjectCodeError("In project file: '{}' key='{}' must be set.".format(self.json_path, key))

    def _resources_of_objects(self):
        return itertools.chain.from_iterable(_.get_sounds() + _.get_costumes() for _ in self.objects)

    def _resource_name_from(self, res_dict):
        assert JsonKeys.SOUND_MD5 in res_dict or JsonKeys.COSTUME_MD5 in res_dict
        md5_file_name = res_dict[JsonKeys.SOUND_MD5] if JsonKeys.SOUNDNAME_KEY in res_dict else res_dict[JsonKeys.COSTUME_MD5]
        return md5_file_name

    def find_unused_resources_name_and_filepath(self):
        for file_path in glob.glob(os.path.join(self.input_path, "*")):
            md5_resource_filename = common.md5_hash(file_path) + os.path.splitext(file_path)[1]
            if md5_resource_filename not in self.resource_names:
                if file_path != self.json_path:
                    yield md5_resource_filename, file_path

    def find_all_resource_dicts_for(self, resource_name):
        for resource in self._resources_of_objects():
            if resource_name in set([resource.get(JsonKeys.SOUND_MD5), resource.get(JsonKeys.COSTUME_MD5)]):
                yield resource


# TODO: rename
# TODO: do not use DictAccessWrapper
class Object(common.DictAccessWrapper):

    def __init__(self, object_data):
        super(Object, self).__init__(object_data)
        if not self.is_valid_class_input(object_data):
            raise ObjectError("Input is no valid Scratch object.")
        for key in (JsonKeys.SOUNDS_KEY, JsonKeys.COSTUMES_KEY, JsonKeys.SCRIPTS_KEY):
            if not key in object_data:
                object_data[key] = []
        # TODO: check for all stage-object-only keys
        self.is_stage_object = JsonKeys.INFO_KEY in object_data
        self.scripts = [Script(_) for _ in self.get_scripts() if Script.is_valid_script_input(_)]

    @classmethod
    def is_valid_class_input(cls, object_data):
        return 'objName' in object_data


# TODO: rename
class Script(object):

    def __init__(self, json_input):
        if not self.is_valid_script_input(json_input):
            raise ScriptError("Input is no valid Scratch sb2 json script.")
        script_content = json_input[2]
        script_settings = script_content[0]
        self.type = script_settings[0]
        self.arguments = script_settings[1:]
        if not self.type in SCRATCH_SCRIPTS:
            raise ScriptError("Unknown sb2 script type: {}".format(self.type))
        self.bricks = script_content[1:]

    @classmethod
    def is_valid_script_input(cls, json_input):
        if (isinstance(json_input, list) and len(json_input) == 3 and isinstance(json_input[0], int) and isinstance(json_input[1], int) and
            isinstance(json_input[2], list)):
            # NOTE: could use a json validator instead
            script_content = json_input[2]
            if script_content[0][0] in SCRATCH_SCRIPTS:
                return True

        log.warning("No valid Scratch script: {}".format(json_input))
        return False

    def get_type(self):
        return self.type

    def get_raw_bricks(self):
        def get_bricks_recursively(nested_bricks):
            result = []
            log.debug("{}".format(nested_bricks))
            for idx, brick in enumerate(nested_bricks):
                isBrickId = idx == 0 and isinstance(brick, str)
                isNestedBrick = isinstance(brick, list)
                if isBrickId:
                    log.debug("adding {}".format(brick))
                    result += [brick]
                elif isNestedBrick:
                    log.debug("calling on {}".format(brick))
                    result += get_bricks_recursively(brick)
                else:
                    assert isinstance(brick, (int, str, float)), "Unhandled brick element type {} for {}".format(type(brick), brick)
                    continue
            return result

        return get_bricks_recursively(self.bricks)


class ProjectCodeError(common.ScratchtobatError):
    pass


class ProjectError(common.ScratchtobatError):
    pass


class ObjectError(common.ScratchtobatError):
    pass


class ScriptError(common.ScratchtobatError):
    pass
