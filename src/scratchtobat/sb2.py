from scratchtobat import common
import os
import json
import hashlib
from scratchtobat import catrobatwriter as sb2keys
import itertools

SCRATCH_SCRIPTS = {
    "whenGreenFlag": None,
    "whenIReceive": None,
    "whenKeyPressed": None,
    "whenSensorGreaterThan": None,
    "whenSceneStarts": None,
    }

STAGE_HEIGHT_IN_PIXELS = 360
STAGE_WIDTH_IN_PIXELS = 480


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
    
    def __init__(self, project_path):
        common.log.info("Project for {}".format(project_path))
        if not os.path.isdir(project_path):
            raise ProjectError("Create project path: {}".format(project_path))
        self.name = os.path.basename(project_path)
        json_path = os.path.join(project_path, self.SCRATCH_PROJECT_CODE_FILE)
        try:
            self.project_code = ProjectCode(json_path)
        except ProjectCodeError as e:
            raise ProjectError(e)
            
        # TODO: property
        self.stage_data = None
        
        md5_to_resource_path_map = {}
        for project_dir_file in os.listdir(project_path):
            project_file_path = os.path.join(project_path, project_dir_file)
            with open(project_file_path, 'rb') as fp:
                file_hash = hashlib.md5(fp.read()).hexdigest()
            md5_to_resource_path_map[file_hash] = project_file_path 
        common.log.info(md5_to_resource_path_map)
        
        def verify_resources(resources):
            for res_dict  in resources:
                assert sb2keys.MD5_KEY in res_dict or sb2keys.BASELAYERMD5_KEY in res_dict
                md5_file = res_dict[sb2keys.MD5_KEY] if sb2keys.SOUNDNAME_KEY in res_dict else res_dict[sb2keys.BASELAYERMD5_KEY]
                resource_path = os.path.join(project_path, md5_file)
                resource_md5 = os.path.splitext(md5_file)[0]
                if not resource_md5 in md5_to_resource_path_map:
                    raise ProjectError("Missing resource file. Provide resource with md5: {}".format(resource_md5))
        
        for sb2_object in self.project_code.objects:
            verify_resources(sb2_object.get_sounds() + sb2_object.get_costumes())
    

class ProjectCode(DictAccessWrapper):
    
    def __init__(self, json_path):
        self.json_path = json_path
        self.project_code = self.load_json_file(self.json_path)
        self.objects_data = [_ for _ in self.get_children() if "objName" in _]
        self.objects = [Object(_) for _ in [self.project_code] + self.objects_data]

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

    def md5_file_names_of_referenced_resources(self):    
        def verify_resources(resources):
            result = []
            for res_dict  in resources:
                assert sb2keys.MD5_KEY in res_dict or sb2keys.BASELAYERMD5_KEY in res_dict
                md5_file_name = res_dict[sb2keys.MD5_KEY] if sb2keys.SOUNDNAME_KEY in res_dict else res_dict[sb2keys.BASELAYERMD5_KEY]
                result += [md5_file_name]
            return result
        
        return itertools.chain.from_iterable(verify_resources(sb2_object.get_sounds() + sb2_object.get_costumes()) for sb2_object in self.objects)
            

class Object(DictAccessWrapper):
    
    def __init__(self, object_data):
        self.object_data = object_data
        if not self.is_valid_class_input(self.object_data):
            raise ObjectError("Input is no valid Scratch json sb2 object.")
        scripts_data = self.object_data.get('scripts')
        if scripts_data:
            self.scripts = [Script(_) for _ in scripts_data]
        else:
            self.scripts = []
    
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
        self.script_type = script_content[0][0]
        if not self.script_type in SCRATCH_SCRIPTS:
            raise ScriptError("Unknown sb2 script type: {}".format(self.script_type))
        self.bricks = script_content[1:]

    @classmethod
    def is_valid_script_input(cls, json_input):
        return (isinstance(json_input, list) and len(json_input) == 3 and
            # NOTE: could use a json validator instead
            isinstance(json_input[0], int) and isinstance(json_input[1], int) and isinstance(json_input[2], list))
    
    def get_type(self):
        return self.script_type
        
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
