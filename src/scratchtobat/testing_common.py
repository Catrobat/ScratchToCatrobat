import os

def get_res_path():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), 
                                                            "../../test/res"))
    
def get_json_path():
    return os.path.join(get_res_path() , "json/")


    
