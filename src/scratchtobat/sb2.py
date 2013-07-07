from scratchtobat import  common
import hashlib
import itertools
import json
import os
import logging

log = logging.getLogger("scratchtobat.sb2")

SCRIPT_GREEN_FLAG, SCRIPT_RECEIVE, SCRIPT_KEY_PRESSED, SCRIPT_SENSOR_GREATER_THAN, SCRIPT_SCENE_STARTS, SCRIPT_CLICKED = \
     SCRATCH_SCRIPTS = ["whenGreenFlag", "whenIReceive", "whenKeyPressed", "whenSensorGreaterThan", "whenSceneStarts", "whenClicked", ]

STAGE_HEIGHT_IN_PIXELS = 360
STAGE_WIDTH_IN_PIXELS = 480

LICENSE_URI = "http://creativecommons.org/licenses/by-sa/2.0/deed.en"


class JsonKeys(object):
    OBJNAME_KEY = "objName"
    SOUNDS_KEY = "sounds"
    COSTUMES_KEY = "costumes"
    CHILDREN_KEY = "children"
    SCRIPTS_KEY = "scripts"
    INFO_KEY = "info"
    SOUNDNAME_KEY = "soundName"
    SOUNDID_KEY = "soundID"
    SOUND_MD5 = "md5"
    COSTUME_MD5 = "baseLayerMD5"
    BASELAYERID_KEY = "baseLayerID"
    COSTUMENAME_KEY = "costumeName"


class DictAccessWrapper(object):
    def get_raw_dict(self):
        raise NotImplementedError("Must be overridden by class '{}'.".format(type(self)))

    def __getattr__(self, name):
        if name.startswith("get_"):
            json_key = name.replace("get_", "")

            def access_json_data():
                return self.get_raw_dict().get(json_key)
            return access_json_data

        raise AttributeError("'{}' object has no attribute '{}'".format(self.__class__.__name__, name))


class Project(object):
    SCRATCH_PROJECT_CODE_FILE = "project.json"

    def __init__(self, input_path, name=None):
        common.log.info("Project for {}".format(input_path))
        if not os.path.isdir(input_path):
            raise ProjectError("Project not found at: {}. Please create project.".format(input_path))

        json_path = os.path.join(input_path, self.SCRATCH_PROJECT_CODE_FILE)
        try:
            self.project_code = ProjectCode(json_path)
        except ProjectCodeError as e:
            raise ProjectError(e)
        if name:
            self.name = name
        else:
            self.name = self.project_code.get_info().get("projectID")
        if not self.name:
            raise ProjectError("No project name specified in project file. Please provide project name with constructor.")

        self.md5_to_resource_path_map = {}
        for project_dir_file in os.listdir(input_path):
            project_file_path = os.path.join(input_path, project_dir_file)
            with open(project_file_path, 'rb') as fp:
                file_hash = hashlib.md5(fp.read()).hexdigest()
            self.md5_to_resource_path_map[file_hash + os.path.splitext(project_file_path)[1]] = project_file_path
        common.log.info(self.md5_to_resource_path_map)

        def verify_resources(resources):
            for res_dict  in resources:
                assert JsonKeys.SOUND_MD5 in res_dict or JsonKeys.COSTUME_MD5 in res_dict
                md5_file = res_dict[JsonKeys.SOUND_MD5] if JsonKeys.SOUNDNAME_KEY in res_dict else res_dict[JsonKeys.COSTUME_MD5]
                resource_md5 = os.path.splitext(md5_file)[0]
                if not md5_file in self.md5_to_resource_path_map:
                    raise ProjectError("Missing resource file at project: {}. Provide resource with md5: {}".format(input_path, resource_md5))

        for sb2_object in self.project_code.objects:
            verify_resources(sb2_object.get_sounds() + sb2_object.get_costumes())

        listened_keys = []
        for object_ in self.project_code.objects:
            for script in object_.scripts:
                if script.type == SCRIPT_KEY_PRESSED:
                    assert len(script.arguments) == 1
                    listened_keys += script.arguments
        self.listened_keys = set(listened_keys)

        self.background_md5_names = set([costume[JsonKeys.COSTUME_MD5] for costume in self.project_code.stage_object.get_costumes()])


class ProjectCode(DictAccessWrapper):

    def __init__(self, json_path):
        self.json_path = json_path
        self.project_code = self.load_json_file(self.json_path)
        self.objects_data = [_ for _ in self.get_children() if "objName" in _]
        self.objects = [Object(_) for _ in [self.project_code] + self.objects_data]
        self.stage_object = self.objects[0]

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
                raise ProjectCodeError("Wrong project file: {}. Key='{}' not set.".format(self.json_path, key))

    def get_raw_dict(self):
        return self.project_code

    def _resources_of_objects(self):
        return itertools.chain.from_iterable(_.get_sounds() + _.get_costumes() for _ in self.objects)

    def md5_file_names_of_referenced_resources(self):
        def get_md5_name_of_resource(res_dict):
            assert JsonKeys.SOUND_MD5 in res_dict or JsonKeys.COSTUME_MD5 in res_dict
            md5_file_name = res_dict[JsonKeys.SOUND_MD5] if JsonKeys.SOUNDNAME_KEY in res_dict else res_dict[JsonKeys.COSTUME_MD5]
            return md5_file_name

        return (get_md5_name_of_resource(_) for _ in self._resources_of_objects())

    def resource_dicts_of_md5_name(self, md5_name):
        for resource in self._resources_of_objects():
            if resource.get(JsonKeys.SOUND_MD5) == md5_name:
                    yield resource
            elif resource.get(JsonKeys.COSTUME_MD5) == md5_name:
                    yield resource


class Object(DictAccessWrapper):

    def __init__(self, object_data):
        self.object_data = object_data
        if not self.is_valid_class_input(self.object_data):
            raise ObjectError("Input is no valid Scratch json sb2 object.")
        for key in (JsonKeys.SOUNDS_KEY, JsonKeys.COSTUMES_KEY, JsonKeys.SCRIPTS_KEY):
            if not key in self.object_data:
                self.object_data[key] = []

        self.scripts = [Script(_) for _ in self.get_scripts() if Script.is_valid_script_input(_)]

    @classmethod
    def is_valid_class_input(cls, object_data):
        return 'objName' in object_data

    def get_raw_dict(self):
        return self.object_data


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
            common.log.debug("{}".format(nested_bricks))
            for idx, brick in enumerate(nested_bricks):
                isBrickId = idx == 0 and isinstance(brick, str)
                isNestedBrick = isinstance(brick, list)
                if isBrickId:
                    common.log.debug("adding {}".format(brick))
                    result += [brick]
                elif isNestedBrick:
                    common.log.debug("calling on {}".format(brick))
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
