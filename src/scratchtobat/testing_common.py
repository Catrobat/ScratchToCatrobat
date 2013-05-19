import os


def get_test_resources_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../test/res"))


def get_test_project_path(project_name):
    return os.path.join(get_test_resources_path(), "sb2", project_name)
