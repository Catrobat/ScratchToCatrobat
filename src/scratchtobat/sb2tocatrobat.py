from codecs import open
from scratchtobat import common, sb2
from scratchtobat.sb2 import JsonKeys as sb2keys 
from scratchtobat.tools import svgtopng, imageresizer
import hashlib
import org.catrobat.catroid.common as catcommon
import org.catrobat.catroid.content as catbase
import org.catrobat.catroid.content.bricks as catbricks
import org.catrobat.catroid.io as catio
import os
import shutil
import tempfile
import zipfile
from javax.imageio import ImageIO
from java.io import File

CATROID_PROJECT_FILE = "code.xml"
CATROID_NOMEDIA_FILE = ".nomedia"

_DEFAULT_BRICK_CLASS = catbricks.WaitBrick


def _key_to_broadcast_message(keyName):
    return keyName + "Pressed"


class _ScratchToCatrobat(object):
    # based on: http://code.google.com/p/sb2-js/source/browse/trunk/editor.htm
    SCRATCH_TO_CATROBAT_MAPPING = {
         # keys with value=None will be converted to WaitBrick with 500 ms
        #===========================================================================
        # Scripts
        #===========================================================================
        "whenGreenFlag": catbase.StartScript,
        "whenIReceive": catbase.BroadcastScript,
        "whenKeyPressed": lambda sprite, key: catbase.BroadcastScript(sprite, _key_to_broadcast_message(key)),
        "whenSensorGreaterThan": None,
        "whenSceneStarts": None,  # easy: stage msg broadcast
        "whenClicked": catbase.WhenScript,  # easy
        
        #===============================================================================
        #  Bricks  
        #===============================================================================
        "broadcast:": catbricks.BroadcastBrick,  # easy
        "doReturn": None,
        "doWaitUntil": None,
        "wait:elapsed:from:": lambda sprite, time_value: catbricks.WaitBrick(sprite, int(time_value * 1000)),
        "stopAll": None,
        "stopScripts": None,
        
        # conditionals
        "doForever": catbricks.ForeverBrick,
        "doIf": [catbricks.IfLogicBeginBrick, catbricks.IfLogicEndBrick],  # easy
        "doIfElse": [catbricks.IfLogicBeginBrick, catbricks.IfLogicElseBrick, catbricks.IfLogicEndBrick],  # easy
        "doRepeat": catbricks.RepeatBrick,
        "doUntil": None,
        
        "turnRight:": catbricks.TurnRightBrick,  # easy
        "turnLeft:": catbricks.TurnLeftBrick,  # easy
        "heading:": catbricks.PointInDirectionBrick,  # easy
        "forward:": catbricks.MoveNStepsBrick,
        "pointTowards:": catbricks.PointToBrick,  # easy
        "gotoX:y:": catbricks.PlaceAtBrick,  # easy
        "glideSecs:toX:y:elapsed:from:": catbricks.GlideToBrick,  # easy
        "xpos:": catbricks.SetXBrick,  # easy
        "ypos:": catbricks.SetYBrick,  # easy
        "bounceOffEdge": catbricks.IfOnEdgeBounceBrick,  # easy (screen as now)
        "changeXposBy:": catbricks.ChangeXByNBrick,  # easy
        "changeYposBy:": catbricks.ChangeYByNBrick,  # easy
        
        # variables
        "setVar:to:": catbricks.SetVariableBrick,  # easy
        "changeVar:by:": catbricks.ChangeVariableBrick,  # easy
        "showVariable:": None,
        "hideVariable:": None,
        
        # lists
        "append:toList:": None,
        "deleteLine:ofList:": None,
        "insert:at:ofList:": None,
        "setLine:ofList:to:": None,
        
        # pen
        "clearPenTrails": None,
        "putPenDown": None,
        "putPenUp": None,
        "penColor:": None,
        "changePenSizeBy:": None,
        "changePenHueBy:": None,
        "setPenHueTo:": None,
        "changePenShadeBy:": None,
        "setPenShadeTo:": None,
        "penSize:": None,
        "stampCostume": None,
        
        # looks
        "lookLike:": None,
        "nextCostume": catbricks.NextLookBrick,
        "startScene": None,  # easy: msg broadcast
        "nextScene": None,  # easy: msg broadcast
        
        "say:duration:elapsed:from:": None,
        "say:": None,
        "think:duration:elapsed:from:": None,
        "think:": None,
        "changeGraphicEffect:by:": lambda sprite, effectType, value: \
            catbricks.ChangeBrightnessByNBrick(sprite, value) if effectType == 'brightness' else \
                (catbricks.ChangeGhostEffectByNBrick(sprite, value) if effectType == 'ghost' else None) ,  # easy: for ghost, brightness 
        "setGraphicEffect:to:": lambda sprite, effectType, value: \
            catbricks.SetBrightnessBrick(sprite, value) if effectType == 'brightness' else \
                (catbricks.SetGhostEffectBrick(sprite, value) if effectType == 'ghost' else None) ,  # easy: for ghost, brightness
        "filterReset": catbricks.ClearGraphicEffectBrick,  # easy
        "changeSizeBy:": catbricks.ChangeSizeByNBrick,  # easy
        "setSizeTo:": catbricks.SetSizeToBrick,  # easy
        "show": catbricks.ShowBrick,  # easy
        "hide": catbricks.HideBrick,  # easy
        "comeToFront": catbricks.ComeToFrontBrick,  # easy
        "goBackByLayers:": catbricks.GoNStepsBackBrick,  # easy
        
        # sound
        "playSound:": catbricks.PlaySoundBrick,
        "doPlaySoundAndWait": None,
        "stopAllSounds": None,
        "rest:elapsed:from:": None,
        "noteOn:duration:elapsed:from:": None,
        "setVolumeTo:": None,
        "changeTempoBy:": None,
        "setTempoTo:": None,
        
        # midi
        "playDrum": None,
        
        # sensing
        "doAsk": None,
        "timerReset": None,
        
        ###############################
        # reporter blocks
        ################################
        "+": None,  # easy start
        "-": None,
        "*": None,
        "\/": None,
        "randomFrom:to:": None,
        "<": None,
        "=": None,
        ">": None,
        "&": None,
        "|": None,
        "not": None,  # easy end
        "concatenate:with:": None,
        "letter:of:": None,
        "stringLength:": None,
        "\\\\": None,
        "rounded": None,  # easy
        "computeFunction:of:": None,  # easy
        
        # variables
        "readVariable": None,  # easy
        
        # lists
        "getLine:ofList:": None,
        "lineCountOfList:": None,
        "list:contains:": None,
        
        # sensing
        "touching:": None,
        "touchingColor:": None,
        "color:sees:": None,
        "answer": None,
        "mouseX": None,
        "mouseY": None,
        "mousePressed": None,
        "keyPressed:": None,
        "distanceTo:": None,
        "timer": None,
        "getAttribute:of:": None,
        
        # looks
        "costumeIndex": None,
        "scale": None,  # easy
    }
    
    @classmethod
    def brick(cls, sb2name):
        assert isinstance(sb2name, (str, unicode))
        if not sb2name  in cls.SCRATCH_TO_CATROBAT_MAPPING:
            raise common.ScratchtobatError("Unknown brick identifier: {}".format(sb2name))
        return cls.SCRATCH_TO_CATROBAT_MAPPING[sb2name]
    
    @classmethod
    def script(cls, sb2script_name, sprite, arguments):
        if not sb2script_name in sb2.SCRATCH_SCRIPTS:
            assert False, "Missing script mapping for: " + sb2script_name
        # TODO: separate script and brick mapping
        return cls.brick(sb2script_name)(sprite, *arguments)


def _key_image_path_for(key):
    key_images_path = os.path.join(common.get_project_base_path(), 'resources', 'key_images')
    for key_filename in os.listdir(key_images_path):
        basename, _ = os.path.splitext(key_filename)
        if basename.lower().endswith(" ".join(key.split())):
            return os.path.join(key_images_path, key_filename)


def _key_filename_for(key):
    key_path = _key_image_path_for(key)
    # TODO: extract method, already used once
    return common.md5_hash(key_path) + "_" + _key_to_broadcast_message(key) + os.path.splitext(key_path)[1]


def _convert_to_catrobat_project(sb2_project):
    catr_project = catbase.Project(None, sb2_project.name)
    catr_project.getXmlHeader().virtualScreenHeight = sb2.STAGE_HEIGHT_IN_PIXELS
    catr_project.getXmlHeader().virtualScreenWidth = sb2.STAGE_WIDTH_IN_PIXELS
    for _ in sb2_project.project_code.objects:
        catr_sprite = _convert_to_catrobat_sprite(_)
        catr_project.addSprite(catr_sprite)
        
    def add_used_key_sprites(listened_keys, catr_project):
        height_pos = 1
        for idx, key in enumerate(listened_keys):
            width_pos = idx
            key_filename = _key_filename_for(key)
            key_message = _key_to_broadcast_message(key)
            
            key_sprite = catbase.Sprite(key_message)
            key_look = catcommon.LookData()
            key_look.setLookName(key_message)
            key_look.setLookFilename(key_filename)
            key_sprite.getLookDataList().add(key_look)
           
           # initialize key images in left upper corner
            when_started_script = catbase.StartScript(key_sprite)            
            set_look_brick = catbricks.SetLookBrick(key_sprite)
            set_look_brick.setLook(key_look)
            
            # special handling wider button
            if key == "space":
                width_pos = 0
                height_pos = 2
            y_pos = (sb2.STAGE_HEIGHT_IN_PIXELS / 2) - 30 * height_pos
            x_pos = -(sb2.STAGE_WIDTH_IN_PIXELS / 2) + 30 * (width_pos + 1)
            place_at_brick = catbricks.PlaceAtBrick(key_sprite, x_pos, y_pos)
            
            bricks = [place_at_brick, set_look_brick, catbricks.SetSizeToBrick(key_sprite, 33)] 
            when_started_script.getBrickList().addAll(bricks)
            key_sprite.addScript(when_started_script)
            
            when_tapped_script = catbase.WhenScript(key_sprite)
            when_tapped_script.addBrick(catbricks.BroadcastBrick(key_sprite, key_message))
            key_sprite.addScript(when_tapped_script)
            
            catr_project.addSprite(key_sprite)
    
    add_used_key_sprites(sb2_project.listened_keys, catr_project)
        
    return catr_project


def _convert_to_catrobat_sprite(sb2_object):
    if not isinstance(sb2_object, sb2.Object):
        raise common.ScratchtobatError("Input must be of type={}, but is={}".format(sb2.Object, type(sb2_object)))
    sprite = catbase.Sprite(sb2_object.get_objName())
        
    sprite_looks = sprite.getLookDataList()
    for sb2_costume in sb2_object.get_costumes():
        sprite_looks.add(_convert_to_catrobat_look(sb2_costume))
        
    sprite_sounds = sprite.getSoundList()
    for sb2_sound in sb2_object.get_sounds():
        sprite_sounds.add(_convert_to_catrobat_sound(sb2_sound))
    
    # looks and sounds has to added first because of cross-validations 
    for idx, sb2_script in enumerate(sb2_object.scripts):
        sprite.addScript(_convert_to_catrobat_script(sb2_script, sprite))
   
    def add_implicit_scratch_behaviour_as_bricks():
        implicit_bricks_to_add = [] 
        # add implicit Scratch behaviour: object's currentCostumeIndex determines active costume at startup
        sprite_startup_look_idx = sb2_object.get_currentCostumeIndex()
        if sprite_startup_look_idx is not None:
            spriteStartupLook = sprite.getLookDataList()[sprite_startup_look_idx]
            set_look_brick = catbricks.SetLookBrick(sprite)
            set_look_brick.setLook(spriteStartupLook)
            implicit_bricks_to_add += [set_look_brick]            
            def get_or_add_startscript(sprite):
                for script in sprite.scriptList:
                    if isinstance(script, catbase.StartScript):    
                        return script
                else:
                    start_script = catbase.StartScript(sprite)
                    sprite.addScript(0, start_script)
                    return start_script
            
         # add implicit Scratch behaviour: object's scratchX and scratchY Keys determines object and therefore costume position
        if sb2_object.get_scratchX() or sb2_object.get_scratchY():
            # sets possible None to 0
            x_pos = sb2_object.get_scratchX() or 0
            y_pos = sb2_object.get_scratchY() or 0
            try:
                place_at_brick = catbricks.PlaceAtBrick(sprite, int(x_pos), int(y_pos))
            except TypeError:
                common.log.warning("Problem with args: {}, {}. Set to default (0, 0)".format(x_pos, y_pos))
                place_at_brick = catbricks.PlaceAtBrick(sprite, 0, 0)
            implicit_bricks_to_add += [place_at_brick]

        sprite_scale = sb2_object.get_scale()
        if sprite_scale:
            implicit_bricks_to_add += [catbricks.SetSizeToBrick(sprite, sprite_scale * 100.0)]
    
        start_script = get_or_add_startscript(sprite)
        start_script.getBrickList().addAll(0, implicit_bricks_to_add)
    
    add_implicit_scratch_behaviour_as_bricks()
    
    return sprite


def _convert_to_catrobat_script(sb2_script, sprite):
    if not isinstance(sb2_script, sb2.Script):
        raise common.ScratchtobatError("Arg1 must be of type={}, but is={}".format(sb2.Script, type(sb2_script)))
    if sprite and not isinstance(sprite, catbase.Sprite):
        raise common.ScratchtobatError("Arg2 must be of type={}, but is={}".format(catbase.Sprite, type(sprite)))

    cat_script = _ScratchToCatrobat.script(sb2_script.type, sprite, sb2_script.arguments)
    for sb2_brick in sb2_script.bricks:
        cat_bricks = _convert_to_catrobat_bricks(sb2_brick, sprite)
        for brick in cat_bricks:
            cat_script.addBrick(brick)
    return cat_script


def _convert_to_catrobat_bricks(sb2_brick, cat_sprite):
    common.log.debug("Brick to convert={}".format(sb2_brick))
    if not sb2_brick or not (isinstance(sb2_brick, list) and isinstance(sb2_brick[0], (str, unicode))):
        raise common.ScratchtobatError("Wrong arg1, must be list with string as first element: {!r}".format(sb2_brick))
    if not isinstance(cat_sprite, catbase.Sprite):
        raise common.ScratchtobatError("Wrong arg2, must be of type={}, but is={}".format(catbase.Sprite, type(cat_sprite)))
    brick_name = sb2_brick[0]
    brick_arguments = sb2_brick[1:]
    catr_bricks = []
    try:
        # Bricks which special handling because of e.g. argument mismatch 
        if brick_name in {'doRepeat', 'doForever'}:
            if brick_name == 'doRepeat':
                times_value, nested_bricks = brick_arguments
                if isinstance(times_value, list):
                    common.log.warning("Unsupported times_value: {}. Set to default (1).".format(times_value))
                    times_value = 1
                catr_loop_start_brick = _ScratchToCatrobat.brick(brick_name)(cat_sprite, times_value)
            elif brick_name == 'doForever':
                [nested_bricks] = brick_arguments
                catr_loop_start_brick = _ScratchToCatrobat.brick(brick_name)(cat_sprite)
            else:
                assert False, "Missing conditional branch for: " + brick_name
            catr_bricks += [catr_loop_start_brick]
            for brick_arg in nested_bricks:
                catr_bricks += _convert_to_catrobat_bricks(brick_arg, cat_sprite)
            catr_bricks += [catbricks.LoopEndBrick(cat_sprite, catr_loop_start_brick)]
            
        elif brick_name == "playSound:":
            [look_name] = brick_arguments
            soundinfo_name_to_soundinfo_map = {lookdata.getTitle(): lookdata for lookdata in cat_sprite.getSoundList()}
            lookdata = soundinfo_name_to_soundinfo_map.get(look_name)
            if not lookdata:
                raise ConversionError("Sprite does not contain sound with name={}".format(look_name))
            play_sound_brick = _ScratchToCatrobat.brick(brick_name)(cat_sprite)
            play_sound_brick.setSoundInfo(lookdata)
            catr_bricks += [play_sound_brick]

#         same structure as 'playSound' above
#         elif brick_name == "startScene":
#             [look_name] = brick_arguments
#             matching_lookdatas = [_ for _ in cat_sprite.getLookDataList() if _.getLookName() == look_name]
#             if not matching_lookdatas:
#                 raise ConversionError("Sprite does not contain look with name={}".format(look_name))
#             assert len(matching_lookdatas) == 1
#             [lookdata] = matching_lookdatas
#             set_look_brick = catrobat_class_for_sb2_name(brick_name)(cat_sprite)
#             set_look_brick.setLook(lookdata)
#             catr_bricks += [set_look_brick]
             
        else:
            common.log.debug("Get mapping for {} in {}".format(brick_name, cat_sprite))
            catrobat_class = _ScratchToCatrobat.brick(brick_name) 
            if not catrobat_class:
                common.log.warning("No mapping for={}, using default class".format(brick_name))
                catr_bricks += [_DEFAULT_BRICK_CLASS(cat_sprite, 500), catbricks.NoteBrick(cat_sprite, "Missing brick for sb2 identifier: " + brick_name)]
            else:
                catr_bricks += [catrobat_class(cat_sprite, *brick_arguments)]
    except TypeError as e:
        common.log.exception(e)
        assert False, "Non-matching arguments: {} of SB2 brick '{}'".format(brick_arguments, brick_name)
        
    return catr_bricks


def _convert_to_catrobat_look(costume):
    if not costume or not (isinstance(costume, dict) and all(_ in costume for _ in (sb2keys.BASELAYERMD5_KEY, sb2keys.COSTUMENAME_KEY))):
        raise common.ScratchtobatError("Wrong input, must be costume dict: {}".format(costume))
    look = catcommon.LookData()
    
    assert sb2keys.COSTUMENAME_KEY  in costume
    costume_name = costume[sb2keys.COSTUMENAME_KEY]
    look.setLookName(costume_name)
    
    assert sb2keys.BASELAYERMD5_KEY in costume
    costume_filename = costume[sb2keys.BASELAYERMD5_KEY]
    costume_filename_ext = os.path.splitext(costume_filename)[1]
    look.setLookFilename(costume_filename.replace(costume_filename_ext, "_" + costume_name + costume_filename_ext))
    return look


def _convert_to_catrobat_sound(sound):
    soundinfo = catcommon.SoundInfo()
    
    assert sb2keys.SOUNDNAME_KEY in sound
    sound_name = sound[sb2keys.SOUNDNAME_KEY]
    soundinfo.setTitle(sound_name) 
    
    assert sb2keys.MD5_KEY in sound
    sound_filename = sound[sb2keys.MD5_KEY]
    sound_filename_ext = os.path.splitext(sound_filename)[1]
    soundinfo.setSoundFileName(sound_filename.replace(sound_filename_ext, "_" + sound_name + sound_filename_ext)) 
    return soundinfo


class ConversionError(common.ScratchtobatError):
        pass


def convert_sb2_project_to_catroid_zip(project, catroid_zip_file_path):
    temp_dir = tempfile.mkdtemp()
    convert_sb2_project_to_catroid_project_structure(project, temp_dir)
    
    def iter_dir(path):
        for root, dirs, files in os.walk(path):
            for file in files:
                yield os.path.join(root, file)
                
    assert temp_dir
    assert project.name
    
    with zipfile.ZipFile(catroid_zip_file_path, 'w') as zip_fp:
        for file_path in iter_dir(temp_dir):
            print file_path.replace(temp_dir, project.name), type(file_path.replace(temp_dir, project.name))
            zip_fp.write(file_path, file_path.replace(temp_dir, project.name))
            
    shutil.rmtree(temp_dir)


def images_dir_of_project(temp_dir):
    return os.path.join(temp_dir, "images")


def sounds_dir_of_project(temp_dir):
    return os.path.join(temp_dir, "sounds")


def convert_sb2_project_to_catroid_project_structure(sb2_project, temp_path):
    
    def create_catroid_directory_structure():
        sounds_path = sounds_dir_of_project(temp_path)
        os.mkdir(sounds_path)
        
        images_path = images_dir_of_project(temp_path)
        os.mkdir(images_path)
        
        for _ in (temp_path, sounds_path, images_path):
            open(os.path.join(_, CATROID_NOMEDIA_FILE), 'a').close()
        return sounds_path, images_path

    def save_mediafiles_into_catroid_directory_structure():
        def update_md5_hash(resource_maps, file_path):
            md5_name = common.md5_hash(file_path) + os.path.splitext(file_path)[1]
            for resource_map in resource_maps:
                assert sb2keys.BASELAYERMD5_KEY in resource_map, resource_map
                resource_map[sb2keys.BASELAYERMD5_KEY] = md5_name
            return md5_name
    
        for md5_name, src_path in sb2_project.md5_to_resource_path_map.iteritems():
            file_ext = os.path.splitext(md5_name)[1]
            converted_file = False
            
            if file_ext in {".png", ".svg"}:
                target_dir = images_path
                resource_maps = list(sb2_project.project_code.resource_dicts_of_md5_name(md5_name))
                # WORKAROUNF: penLayerMD5 file
                if not resource_maps:
                    continue
                if file_ext == ".svg":
                    # converting svg to png -> new md5 and filename
                    # TODO: refactor
                    src_path = svgtopng.convert(src_path)
                    md5_name = update_md5_hash(resource_maps, src_path)
                    converted_file = True
                elif md5_name in sb2_project.background_md5_names:
                    # resize background if not matching the default resolution
                    imageFile = File(src_path)
                    pngImage = ImageIO.read(imageFile)
                    if pngImage.getWidth() > sb2.STAGE_WIDTH_IN_PIXELS or pngImage.getHeight() > sb2.STAGE_HEIGHT_IN_PIXELS:
                        resizedImage = imageresizer.resize_png(pngImage, sb2.STAGE_WIDTH_IN_PIXELS, sb2.STAGE_HEIGHT_IN_PIXELS)
                        # FIXME
                        temp_path = src_path.replace(".png", "resized.png")
                        ImageIO.write(resizedImage, "png", File(temp_path))
                        md5_name = update_md5_hash(resource_maps, temp_path)
                        src_path = temp_path
                        converted_file = True
            elif file_ext in {".wav"}:
                target_dir = sounds_path
            else:
                assert file_ext in {".json"}, md5_name
                continue
            
            assert os.path.exists(src_path), "Not existing: {}".format(src_path)            
            for catroid_file_name in _convert_resource_name(sb2_project, md5_name):
                shutil.copyfile(src_path, os.path.join(target_dir, catroid_file_name))
            if converted_file:
                os.remove(src_path)
                
    def xml_content_of_catroid_project(catroid_project):
        storage_handler = catio.StorageHandler().getInstance()
        code_xml_content = storage_handler.XML_HEADER
        code_xml_content += storage_handler.getXMLStringOfAProject(catroid_project)
        return code_xml_content
    
    def save_xmlfile_into_catroid_directory_structure():
        catrobat_project = _convert_to_catrobat_project(sb2_project)
        code_xml_content = xml_content_of_catroid_project(catrobat_project)
        with open(os.path.join(temp_path, CATROID_PROJECT_FILE), "wb") as fp:
            fp.write(code_xml_content)
            
        # copying key images needed for keyPressed substitution
        for listened_key in sb2_project.listened_keys:
             key_image_path = _key_image_path_for(listened_key)
             shutil.copyfile(key_image_path, os.path.join(images_path, _key_filename_for(listened_key)))
        
    # TODO: rename/rearrange abstracting methods
    sounds_path, images_path = create_catroid_directory_structure()
    save_mediafiles_into_catroid_directory_structure()
    save_xmlfile_into_catroid_directory_structure()


def _convert_resource_name(project, md5_name):
    catroid_resource_names = []
    for resource in project.project_code.resource_dicts_of_md5_name(md5_name):
        if resource:
            try:
                resource_name = resource[sb2keys.SOUNDNAME_KEY] if sb2keys.SOUNDNAME_KEY in resource else resource[sb2keys.COSTUMENAME_KEY]
            except KeyError:
                raise ConversionError("Error with: {}, {}".format(md5_name, resource))
            resource_ext = os.path.splitext(md5_name)[1]
            catroid_resource_names += [md5_name.replace(resource_ext, "_" + resource_name + resource_ext)]
    return catroid_resource_names

