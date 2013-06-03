import zipfile

def extract_project(input_sb2, temp_download_dir):
    with zipfile.ZipFile(input_sb2, 'r') as myzip: 
        myzip.extractall(temp_download_dir)