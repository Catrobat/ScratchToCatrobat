import json


class ScratchReader(object):
    def __init__(self, json_file):
        self.json_file = json_file
        self.load_json_file()
        
    def load_json_file(self):
        with open(self.json_file, "r") as file:
            json_string = file.read()
            self.json_dict = json.loads(json_string)
        
        
    def get_dict(self):
        return self.json_dict
        
