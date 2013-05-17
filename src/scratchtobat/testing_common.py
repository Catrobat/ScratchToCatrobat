import os

SCRATCH_PROJECT_JSON_FILE = "project.json"

def get_res_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__),
                                                            "../../test/res"))

def get_json_path():
    return os.path.join(get_res_path() , "json/")


def get_test_json_path(testproject_name):
    return os.path.join(get_json_path(), testproject_name, SCRATCH_PROJECT_JSON_FILE)


