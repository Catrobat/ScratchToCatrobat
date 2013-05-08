import json

class ScratchReader(object):
    def __init__(self, json_file):
        self.json_file = json_file
        self.load_json_file()
        
    def load_json_file(self):
        with open(self.json_file, "r") as fp:
            json_string = fp.read()
            self.json_dict = json.loads(json_string)
            self.verify_scratch_json(self.json_dict)
        
    def get_dict(self):
        return self.json_dict
    
    def verify_scratch_json(self, json_dict):
        # FIXME: check which tags are really required
        for key in ["objName", "info", "currentCostumeIndex", "penLayerMD5", "tempoBPM", "videoAlpha", "children", "costumes", "sounds"]:
            if not key in json_dict:
                raise ScratchReaderException("Key='{}' not found in {}".format(key, self.json_file))
        
class ScratchReaderException(Exception):
    pass