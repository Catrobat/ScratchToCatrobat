import os
import shutil
import zipfile

from scratchreader import ScratchReader
from scratchreader import ScratchReaderException 
from catrobatwriter import CatrobatWriter

PROJECT_JSON_FILE = "project.json"
PROJECT_CATROBAT_FILE = "code.xml"

class ProjectConverter(object):
    
    def __init__(self, input_sb2, output_folder, working_dir):
        self.input_sb2 = input_sb2
        self.output_folder = output_folder
        self.working_dir = working_dir
        self.image_out_dir = os.path.join(output_folder, "images")
        self.sound_out_dir = os.path.join(output_folder, "sounds")
    
    def create_structure(self):
        open(os.path.join(output_folder, ".nomedia"), 'w').close()        
        os.mkdir(image_out_dir)
        open(os.path.join(self.image_out_dir, ".nomedia"), 'w').close()
        os.mkdir(self.sound_out_dir)
        open(os.path.join(self.sound_out_dir, ".nomedia"), 'w').close()
        #todo screenshot
    
    def extract_sb2(self):
        with ZipFile(self.input_sb2, 'r') as myzip: 
            myzip.extractall(self.working_dir)
    
    def convert():
        self.extract_sb2()
        self.create_structure()
        json_file = os.path.join(self.working_dir, PROJECT_JSON_FILE)
        scratch_reader = ScratchReader(json_file)
        json_dict = self.scratch_reader.get_dict()
        
        catrobat_writer = CatrobatWriter(json_dict, output_folder)
        catrobat_writer.process_dict()
        
        xml_string = catrobat_writer.document.toprettyxml()
        
        with open(os.path.join(self.output_folder, PROJECT_CATROBAT_FILE), "w") as fp:
            fp.write(xml_string)
        
        for sound in catrobat_writer.sound_files:
            shutil.copy(os.path.join(self.working_dir, sound), os.path.join(self.sound_out_dir, sound))
            
        for image in catrobat_writer.costume_files:
            shutil.copy(os.path.join(self.working_dir, image), os.path.join(self.image_out_dir, image))   
        