from scratchtobat import common
import os
import json
import java

SCRATCH_SCRIPTS = {
    "whenGreenFlag": None,
    "whenIReceive": None,
    "whenKeyPressed": None,
    "whenSensorGreaterThan": None,
    "whenSceneStarts": None,
    } 


class DictAccessWrapper(object):
    def __getattr__(self, name):
        if name.startswith("get_"):
            json_key = name.replace("get_", "")
            if json_key in self._raw_data:
                def access_json_data():
                    return self._raw_data[json_key]
                return access_json_data
        
        raise AttributeError


class Project(object):
    _SCRATCH_PROJECT_DATA_FILE = "project.json"
    
    def __init__(self, project_path):
        if not os.path.isdir(project_path):
            raise ProjectError("Create project path: {}".format(project_path))
        self.name = os.path.basename(project_path)
        self.json_path = os.path.join(project_path, self._SCRATCH_PROJECT_DATA_FILE)
        self.project_data = self.load_json_file(self.json_path)
        # TODO: property
        self.stage_data = None
        self.objects_data = [_ for _ in self.project_data["children"] if "objName" in _]
        self.objects = [Object(_) for _ in self.objects_data]
        
    def load_json_file(self, json_file):
        if not os.path.exists(json_file):
            raise ProjectError("Provide project data file: {}".format(json_file))
        with open(json_file, "r") as fp:
            json_dict = json.load(fp)
            self.verify_scratch_json(json_dict)
            return json_dict
        
    def get_raw_data(self):
        return self.project_data
    
    def verify_scratch_json(self, json_dict):
        # FIXME: check which tags are really required
        for key in ["objName", "info", "currentCostumeIndex", "penLayerMD5", "tempoBPM", "videoAlpha", "children", "costumes", "sounds"]:
            if not key in json_dict:
                raise ProjectError("Key='{}' not found in {}".format(key, self.json_path))


class ProjectError(common.ScratchtobatError):
    pass



class Object(DictAccessWrapper):
    
    def __init__(self, object_data):
        if not self.is_valid_class_input(object_data):
            raise ObjectError("Input is no valid Scratch json sb2 object.")
        self._raw_data = object_data
        scripts_data = object_data.get('scripts')
        if scripts_data:
            self.scripts = [Script(_) for _ in scripts_data]
        else:
            self.scripts = []
    
    @classmethod
    def is_valid_class_input(cls, object_data):
        return 'objName' in object_data


class ObjectError(common.ScratchtobatError):
    pass


class Script(object):
    
    def __init__(self, json_input):
        if not self.is_valid_script_input(json_input):
            raise ScriptError("Input is no valid Scratch sb2 json script.")
        script_content = json_input[2]
        self.script_id = script_content[0][0]
        if not self.script_id in SCRATCH_SCRIPTS:
            raise ScriptError("Unknown sb2 script type: {}".format(self.script_id))
        self.script_bricks = script_content[1:]

    @classmethod
    def is_valid_script_input(cls, json_input):
        return (isinstance(json_input, list) and len(json_input) == 3 and
            # NOTE: could use a json validator instead
            isinstance(json_input[0], int) and isinstance(json_input[1], int) and isinstance(json_input[2], list))
    
    def get_type(self):
        return self.script_id
        
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
        
        return get_bricks_recursively(self.script_bricks)


class ScriptError(common.ScratchtobatError):
    pass
