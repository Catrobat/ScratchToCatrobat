import os
import shutil
import re
import tempfile
import hashlib
import Image
from xmlwriter import XmlWriter

class ScratchOutputParser:
    def __init__(self, project_path, project_name):
        self.project_path = project_path
        self.project_name = project_name
        self.xml_writer = XmlWriter()
        self.xml_writer.create_project(project_name)
        self.sprites = []

        self.temp_folder = tempfile.mkdtemp()
        os.makedirs(os.path.join(self.temp_folder, 'images'))
        os.makedirs(os.path.join(self.temp_folder, 'sounds'))

    def process_project(self):
        project_data = open(os.path.join(self.project_path, 'blocks.txt'), 'U').read()
        unparsed_sprites = project_data.split("\n\n\n")

        for unparsed_sprite in unparsed_sprites:
            if unparsed_sprite:
                sprite_info, unparsed_bricks = unparsed_sprite.split("\n\n", 1)
                sprite_name, variables, lists, position, visibility, sounds, costumes = sprite_info.split('\n')
                self.xml_writer.add_sprite(sprite_name)
                
                self.process_costumes(costumes, sprite_name)
                self.process_sounds(sounds, sprite_name)
                self.process_scripts(unparsed_bricks, sprite_name)
        
        self.xml_writer.write_to_file(os.path.join(self.temp_folder, 'projectcode.xml'))


    def process_costumes(self, costumes, sprite_name):
        costumes = re.findall(r"'(.+?)'", costumes)
        costume_filenames = os.listdir(os.path.join(self.project_path, sprite_name, 'images'))
        for costume in costumes:
            for costume_filename in costume_filenames:
                if costume_filename.startswith(costume + '.'):
                    filename = costume_filename
                    break      

            Image.open(os.path.join(self.project_path, sprite_name, 'images', filename))\
                 .save(os.path.join(self.temp_folder, 'images', sprite_name + '_' + costume + '.png'))

            filename = sprite_name + '_' + costume + '.png'

            file_contents = open(os.path.join(self.temp_folder, 'images', filename), 'rb').read()
            checksum = hashlib.md5(file_contents).hexdigest().upper()

            os.rename(os.path.join(self.temp_folder, 'images', filename),\
                      os.path.join(self.temp_folder, 'images', checksum + '_' + filename))
            filename = checksum + '_' + filename

            self.xml_writer.add_costume(costume, filename, sprite_name)

    def process_sounds(self, sounds, sprite_name):
        sounds = re.findall(r"'(.+?)'", sounds)
        sounds.remove('-')
        sounds.remove('record...')
        sounds_filenames = os.listdir(os.path.join(self.project_path, sprite_name, 'sounds'))
        for sound in sounds:
            for sound_filename in sounds_filenames:
                if sound_filename.startswith(sound + '.'):
                    filename = sound_filename
                    break      

            shutil.copy(os.path.join(self.project_path, sprite_name, 'sounds', filename),\
                        os.path.join(self.temp_folder, 'sounds', sprite_name + '_' + sound_filename))

            filename = sprite_name + '_' + sound_filename

            file_contents = open(os.path.join(self.temp_folder, 'sounds', filename), 'rb').read()
            checksum = hashlib.md5(file_contents).hexdigest().upper()

            os.rename(os.path.join(self.temp_folder, 'sounds', filename),\
                      os.path.join(self.temp_folder, 'sounds', checksum + '_' + filename))
            filename = checksum + '_' + filename

            self.xml_writer.add_sound(sound, filename, sprite_name)
    
    def process_scripts(self, unparsed_bricks, sprite_name):
        scripts_data = re.split(".*?EventHatMorph", unparsed_bricks)
        for script_data in scripts_data:
            if script_data:
                broadcasted_message = None
                script_data = script_data.splitlines()
                if "'when I receive'" in script_data[0]:
                    script_type = 'BroadcastScript'
                    broadcasted_message = script_data[1]
                elif "'when'" in script_data[0]:
                    if script_data[1] == "Scratch-StartClicked":
                        script_type = 'StartScript'
                    elif script_data[1] == "Scratch-MouseClickEvent":
                        script_type = 'WhenScript'
                    elif script_data[1] == "Scratch-KeyPressedEvent":
                        continue #TODO

                script_data = script_data[2:]
                bricks_params = []
                
                while script_data:
                    brick_name = script_data.pop(0)
                    if "BlockMorph" in brick_name:
                        brick_name = script_data.pop(0)
                        if "'show'" in brick_name:
                            bricks_params.append(("Bricks.ShowBrick", {}))
                        elif "'hide'" in brick_name:
                            bricks_params.append(("Bricks.HideBrick", {}))
                        elif "broadcast %e" in brick_name:
                            script_data.pop(0)
                            message = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.BroadcastBrick", {"broadcastMessage": message}))
                        elif "wait %n secs" in brick_name:
                            script_data.pop(0)
                            time = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            time = str(long(float(time) * 1000))
                            bricks_params.append(("Bricks.WaitBrick", {"timeToWaitInMilliSeconds": time}))
                        elif "next costume" in brick_name:
                            bricks_params.append(("Bricks.NextCostumeBrick", {}))
                        elif "set size to %n%" in brick_name:
                            script_data.pop(0)
                            size = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.SetSizeToBrick", {"size": size}))
                        elif "change size by %n" in brick_name:
                            script_data.pop(0)
                            size = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.ChangeSizeByNBrick", {"size": size}))
                        elif "turn %n degrees" in brick_name:
                            direction = script_data.pop(0)
                            script_data.pop(0)
                            degrees = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            if "#turnLeft" in direction:
                                bricks_params.append(("Bricks.TurnLeftBrick", {"degrees": degrees}))
                            else:
                                bricks_params.append(("Bricks.TurnRightBrick", {"degrees": degrees}))
                        elif "go to x:%n y:%n" in brick_name:
                            script_data.pop(0)
                            x = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            y = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.PlaceAtBrick", {"xPosition": x, "yPosition": y}))
                        elif "switch to costume %l" in brick_name:
                            script_data.pop(0)
                            costume_name = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.SetCostumeBrick", {"costume_name": costume_name}))
                        elif "play sound %S" in brick_name:
                            script_data.pop(0)
                            sound_name = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.PlaySoundBrick", {"sound_name": sound_name}))
                        elif "set %g effect to %n" in brick_name:
                            script_data.pop(0)
                            effect = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            script_data.pop(0)
                            effect_value = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            if effect == 'brightness':
                                bricks_params.append(("Bricks.SetBrightnessBrick", {"brightness": effect_value}))
                            elif effect == 'ghost':
                                bricks_params.append(("Bricks.SetGhostEffectBrick", {"transparency": effect_value}))
                        elif "change %g effect to %n" in brick_name:
                            script_data.pop(0)
                            effect = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            script_data.pop(0)
                            effect_value = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            if effect == 'brightness':
                                bricks_params.append(("Bricks.ChangeBrightnessBrick", {"changeBrightness": effect_value}))
                            elif effect == 'ghost':
                                bricks_params.append(("Bricks.ChangeGhostEffectBrick", {"changeGhostEffect": effect_value}))
                        elif "stop all sounds" in brick_name:
                            bricks_params.append(("Bricks.StopAllSoundsBrick", {}))
                        elif "change volume by %n" in brick_name:
                            script_data.pop(0)
                            volume = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.ChangeVolumeByBrick", {"volume": volume}))
                        elif "set volume to %n%" in brick_name:
                            script_data.pop(0)
                            volume = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.SetVolumeToBrick", {"volume": volume}))
                        elif "say %s" in brick_name:
                            script_data.pop(0)
                            text = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.SpeakBrick", {"text": text}))
                        elif "set x to" in brick_name:
                            script_data.pop(0)
                            x = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.SetXBrick", {"xPosition": x}))
                        elif "set y to" in brick_name:
                            script_data.pop(0)
                            y = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.SetYBrick", {"yPosition": y}))
                        elif "change x by" in brick_name:
                            script_data.pop(0)
                            x = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.ChangeXByBrick", {"xMovement": x}))
                        elif "change y by" in brick_name:
                            script_data.pop(0)
                            y = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.ChangeYByBrick", {"yMovement": y}))
                        elif "point in direction %d" in brick_name:
                            script_data.pop(0)
                            degrees = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.PointInDirectionBrick", {"degrees": degrees}))
                        elif "glide %n secs to x:%n y:%n" in brick_name:
                            script_data.pop(0)
                            time = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            time = str(long(float(time) * 1000))
                            x = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            y = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.GlideToBrick", {"durationInMilliSeconds": time, "xDestination": x, "yDestination": y}))
                        elif "if on edge, bounce" in brick_name:
                            bricks_params.append(("Bricks.IfOnEdgeBounceBrick", {}))
                        elif "move %n steps" in brick_name:
                            script_data.pop(0)
                            steps = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.MoveNStepsBrick", {"steps": steps}))
                        elif "go to front" in brick_name:
                            bricks_params.append(("Bricks.ComeToFrontBrick", {}))
                        elif "go back %n layers" in brick_name:
                            script_data.pop(0)
                            steps = re.findall(r"'(.+?)'", script_data.pop(0))[0]
                            bricks_params.append(("Bricks.GoNStepsBackBrick", {"steps": steps}))
                        elif "point towards %m" in brick_name:
                            if script_data.pop(0) == '(#mouse)':
                                script_data.pop(0)
                                script_data.pop(0)
                                continue
                            else:
                                pointed_sprite = script_data.pop(0)
                                script_data.pop(0)
                                script_data.pop(0)
                                bricks_params.append(("Bricks.PointToBrick", {"pointedSprite": pointed_sprite}))

                self.sprites.append((sprite_name, bricks_params))
                self.xml_writer.add_script(sprite_name, script_type, bricks_params, broadcasted_message)

    def save_to(self, path_to_output):
        shutil.make_archive(os.path.join(path_to_output, self.project_name), 'zip', self.temp_folder)