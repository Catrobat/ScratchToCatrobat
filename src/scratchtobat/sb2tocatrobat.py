from codecs import open
from scratchtobat import common, sb2, sb2webapi
from scratchtobat.sb2 import JsonKeys as sb2keys
from scratchtobat.tools import svgtopng, imageresizer, wavconverter
import org.catrobat.catroid.common as catcommon
import org.catrobat.catroid.content as catbase
import org.catrobat.catroid.content.bricks as catbricks
import org.catrobat.catroid.io as catio
import org.catrobat.catroid.formulaeditor as catformula
import os
import shutil
import tempfile
import zipfile
from javax.imageio import ImageIO
from java.io import File
import logging

CATROID_PROJECT_FILE = "code.xml"
CATROID_NOMEDIA_FILE = ".nomedia"

_DEFAULT_BRICK_CLASS = catbricks.WaitBrick


log = logging.getLogger("scratchtobat.sb2tocatrobat")
log.setLevel(logging.INFO)


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
        "doBroadcastAndWait": catbricks.BroadcastBrick,  # FIXME: not correct
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
        "lookLike:": catbricks.SetLookBrick,
        "nextCostume": catbricks.NextLookBrick,
        "startScene": None,  # easy: msg broadcast
        "nextScene": None,  # easy: msg broadcast

        "say:duration:elapsed:from:": None,
        "say:": None,
        "think:duration:elapsed:from:": None,
        "think:": None,
        "changeGraphicEffect:by:": lambda sprite, effectType, value: \
            catbricks.ChangeBrightnessByNBrick(sprite, value) if effectType == 'brightness' else \
                (catbricks.ChangeGhostEffectByNBrick(sprite, value) if effectType == 'ghost' else None),  # easy: for ghost, brightness
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
#         "+": None,  # easy start
#         "-": None,
#         "*": None,
#         "\/": None,
#         "randomFrom:to:": None,
#         "<": None,
#         "=": None,
#         ">": None,
#         "&": None,
#         "|": None,
#         "not": None,  # easy end
        "concatenate:with:": None,
        "letter:of:": None,
        "stringLength:": None,
        "\\\\": None,
        "rounded": None,  # easy
        "computeFunction:of:": None,  # easy
        "randomFrom:to:": None,  # easy

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

    OPERATORS_MAPPING = {
        "+": catformula.Operators.PLUS,  # easy start
        "-": catformula.Operators.MINUS,
        "*": catformula.Operators.MULT,
        "/": catformula.Operators.DIVIDE,
        "<": catformula.Operators.SMALLER_THAN,
        "=": catformula.Operators.EQUAL,
        ">": catformula.Operators.GREATER_THAN,
        "&": catformula.Operators.LOGICAL_AND,
        "|": catformula.Operators.LOGICAL_OR,
        "not": catformula.Operators.LOGICAL_NOT,  # easy end
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

    @classmethod
    def operator(cls, opname):
        return cls.OPERATORS_MAPPING.get(opname)


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

catr_project = None


def _convert_to_catrobat_project(sb2_project):
    global catr_project
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
            y_pos = (sb2.STAGE_HEIGHT_IN_PIXELS / 2) - 40 * height_pos
            x_pos = -(sb2.STAGE_WIDTH_IN_PIXELS / 2) + 40 * (width_pos + 1)
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
    for sb2_script in sb2_object.scripts:
        sprite.addScript(_convert_to_catrobat_script(sb2_script, sprite))

    def add_implicit_scratch_behaviour_as_bricks():
        implicit_bricks_to_add = []
        # object's currentCostumeIndex determines active costume at startup
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

        # object's scratchX and scratchY Keys determine position
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

        object_scale = sb2_object.get_scale()
        if object_scale and object_scale != 1:
            implicit_bricks_to_add += [catbricks.SetSizeToBrick(sprite, object_scale * 100.0)]

        object_direction = sb2_object.get_direction()
        if object_direction and object_direction != "90":
            implicit_bricks_to_add += [catbricks.PointInDirectionBrick(sprite, object_direction)]

        object_visible = sb2_object.get_visible()
        if not object_visible:
            implicit_bricks_to_add += [catbricks.HideBrick(sprite)]

        rotation_style = sb2_object.get_rotationStyle()
        if rotation_style and rotation_style != "normal":
            log.warning("Unsupported rotation style '{}' at object: {}".format(rotation_style, sb2_object.get_objName()))

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


def _convert_to_catrobat_bricks(sb2_brick, catr_sprite):
    global catr_project
    common.log.debug("Brick to convert={}".format(sb2_brick))
    if not sb2_brick or not (isinstance(sb2_brick, list) and isinstance(sb2_brick[0], (str, unicode))):
        raise common.ScratchtobatError("Wrong arg1, must be list with string as first element: {!r}".format(sb2_brick))
    if not isinstance(catr_sprite, catbase.Sprite):
        raise common.ScratchtobatError("Wrong arg2, must be of type={}, but is={}".format(catbase.Sprite, type(catr_sprite)))
    brick_name = sb2_brick[0]
    brick_arguments = sb2_brick[1:]
    catr_bricks = []
    catrobat_brick_class = _ScratchToCatrobat.brick(brick_name)
    try:
        # Conditionals for cases which need additional handling after brick object instantiation
        if brick_name in {'doRepeat', 'doForever'}:
            if brick_name == 'doRepeat':
                times_value, nested_bricks = brick_arguments
                if isinstance(times_value, list):
                    common.log.warning("Unsupported times_value: {}. Set to default (1).".format(times_value))
                    times_value = 1
                catr_loop_start_brick = catrobat_brick_class(catr_sprite, times_value)
            elif brick_name == 'doForever':
                [nested_bricks] = brick_arguments
                catr_loop_start_brick = catrobat_brick_class(catr_sprite)
            else:
                assert False, "Missing conditional branch for: " + brick_name

            catr_bricks += [catr_loop_start_brick]
            for brick_arg in nested_bricks:
                # Note: recursive call
                catr_bricks += _convert_to_catrobat_bricks(brick_arg, catr_sprite)
            catr_bricks += [catbricks.LoopEndBrick(catr_sprite, catr_loop_start_brick)]

        elif brick_name in ['doIf']:
            assert catr_project
            if_begin_brick = catbricks.IfLogicBeginBrick(catr_sprite, _convert_formula(brick_arguments[0], catr_sprite, catr_project))
            if_else_brick = catbricks.IfLogicElseBrick(catr_sprite, if_begin_brick)
            if_end_brick = catbricks.IfLogicEndBrick(catr_sprite, if_else_brick, if_begin_brick)

            catr_bricks += [catbricks.RepeatBrick(catr_sprite), if_begin_brick]
            nested_bricks = brick_arguments[1:]
            for brick_arg in nested_bricks:
                # Note: recursive call
                catr_bricks += _convert_to_catrobat_bricks(brick_arg, catr_sprite)

            catr_bricks += [if_else_brick, if_end_brick, catbricks.LoopEndBrick(catr_sprite, catr_bricks[0])]

        elif brick_name == "playSound:":
            [look_name] = brick_arguments
            soundinfo_name_to_soundinfo_map = {lookdata.getTitle(): lookdata for lookdata in catr_sprite.getSoundList()}
            lookdata = soundinfo_name_to_soundinfo_map.get(look_name)
            if not lookdata:
                raise ConversionError("Sprite does not contain sound with name={}".format(look_name))
            play_sound_brick = catrobat_brick_class(catr_sprite)
            play_sound_brick.setSoundInfo(lookdata)
            catr_bricks += [play_sound_brick]

#         same structure as 'playSound' above
#         elif brick_name == "startScene":
#             [look_name] = brick_arguments
#             matching_lookdatas = [_ for _ in catr_sprite.getLookDataList() if _.getLookName() == look_name]
#             if not matching_lookdatas:
#                 raise ConversionError("Sprite does not contain look with name={}".format(look_name))
#             assert len(matching_lookdatas) == 1
#             [lookdata] = matching_lookdatas
#             set_look_brick = catrobat_class_for_sb2_name(brick_name)(catr_sprite)
#             set_look_brick.setLook(lookdata)
#             catr_bricks += [set_look_brick]

        elif catrobat_brick_class in set([catbricks.SetLookBrick]):
            set_look_brick = catrobat_brick_class(catr_sprite)
            [look_name] = brick_arguments
            [look] = [look for look in catr_sprite.getLookDataList() if look.getLookName() == look_name]
            set_look_brick.setLook(look)
            catr_bricks += [set_look_brick]

        else:
            common.log.debug("Get mapping for {} in {}".format(brick_name, catr_sprite))
            catrobat_class = catrobat_brick_class
            # conditionalss for argument convertions
            if not catrobat_class:
                common.log.warning("No mapping for={}, using default class".format(brick_name))
                catr_bricks += [_DEFAULT_BRICK_CLASS(catr_sprite, 500), catbricks.NoteBrick(catr_sprite, "Missing brick for sb2 identifier: " + brick_name)]
            else:
                assert not isinstance(catrobat_class, list), "Wrong at: {1}, {0}".format(brick_arguments, brick_name)
                if brick_arguments:
                    if catrobat_class in set([catbricks.ChangeVariableBrick, catbricks.SetVariableBrick]):
                        assert catr_project
                        variable, value = brick_arguments
                        brick_arguments = [_convert_formula(value, catr_sprite, catr_project), catr_project.getUserVariables().getUserVariable(variable, catr_sprite)]
                catr_bricks += [catrobat_class(catr_sprite, *brick_arguments)]
    except TypeError as e:
        common.log.exception(e)
        assert False, "Non-matching arguments of SB2 brick '{1}'; {0}".format(brick_arguments, brick_name)

    return catr_bricks


def _convert_to_catrobat_look(costume):
    if not costume or not (isinstance(costume, dict) and all(_ in costume for _ in (sb2keys.COSTUME_MD5, sb2keys.COSTUMENAME_KEY))):
        raise common.ScratchtobatError("Wrong input, must be costume dict: {}".format(costume))
    look = catcommon.LookData()

    assert sb2keys.COSTUMENAME_KEY  in costume
    costume_name = costume[sb2keys.COSTUMENAME_KEY]
    look.setLookName(costume_name)

    assert sb2keys.COSTUME_MD5 in costume
    costume_filename = costume[sb2keys.COSTUME_MD5]
    costume_filename_ext = os.path.splitext(costume_filename)[1]
    look.setLookFilename(costume_filename.replace(costume_filename_ext, "_" + costume_name + costume_filename_ext))
    return look


def _convert_to_catrobat_sound(sound):
    soundinfo = catcommon.SoundInfo()

    assert sb2keys.SOUNDNAME_KEY in sound
    sound_name = sound[sb2keys.SOUNDNAME_KEY]
    soundinfo.setTitle(sound_name)

    assert sb2keys.SOUND_MD5 in sound
    sound_filename = sound[sb2keys.SOUND_MD5]
    sound_filename_ext = os.path.splitext(sound_filename)[1]
    soundinfo.setSoundFileName(sound_filename.replace(sound_filename_ext, "_" + sound_name + sound_filename_ext))
#     soundinfo.setSoundFileName(sound_filename.replace(sound_filename_ext, "_" + sound_name))
    return soundinfo


class ConversionError(common.ScratchtobatError):
        pass


def convert_sb2_project_to_catrobat_zip(project, catrobat_zip_file_path):
    temp_dir = tempfile.mkdtemp()
    convert_sb2_project_to_catroid_project_structure(project, temp_dir)

    def iter_dir(path):
        for root, _, files in os.walk(path):
            for file_ in files:
                yield os.path.join(root, file_)

    assert temp_dir
    assert project.name

    with zipfile.ZipFile(catrobat_zip_file_path, 'w') as zip_fp:
        for file_path in iter_dir(temp_dir):
            print file_path.replace(temp_dir, project.name), type(file_path.replace(temp_dir, project.name))
            zip_fp.write(file_path, file_path.replace(temp_dir, project.name))

    with zipfile.ZipFile(catrobat_zip_file_path, 'r') as zip_fp:
        zip_fp.extractall(os.path.dirname(catrobat_zip_file_path))
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
        def update_md5_hash(current_md5_name, file_path_for_update):
            resource_maps = list(sb2_project.project_code.resource_dicts_of_md5_name(current_md5_name))
            md5_name = common.md5_hash(file_path_for_update) + os.path.splitext(file_path_for_update)[1]
            for resource_map in resource_maps:
                if sb2keys.COSTUME_MD5 in resource_map:
                    resource_map[sb2keys.COSTUME_MD5] = md5_name
                elif sb2keys.SOUND_MD5 in resource_map:
                    resource_map[sb2keys.SOUND_MD5] = md5_name
                else:
                    assert False, "Unknown dict: {}".resource_map
            return md5_name

        for md5_name, src_path in sb2_project.md5_to_resource_path_map.iteritems():
            file_ext = os.path.splitext(md5_name)[1].lower()
            converted_file = False

            # TODO; extract method
            if file_ext in {".png", ".svg", ".jpg"}:
                target_dir = images_path
#                 # WORKAROUNF: penLayerMD5 file
#                 if not resource_maps:
#                     continue
                if file_ext == ".svg":
                    # converting svg to png -> new md5 and filename
                    src_path = svgtopng.convert(src_path)
                    converted_file = True

                elif md5_name in sb2_project.background_md5_names:
                    # resize background if not matching the default resolution
                    imageFile = File(src_path)
                    pngImage = ImageIO.read(imageFile)
                    if pngImage.getWidth() > sb2.STAGE_WIDTH_IN_PIXELS or pngImage.getHeight() > sb2.STAGE_HEIGHT_IN_PIXELS:
                        resizedImage = imageresizer.resize_png(pngImage, sb2.STAGE_WIDTH_IN_PIXELS, sb2.STAGE_HEIGHT_IN_PIXELS)
                        # FIXME
                        src_path = src_path.replace(".png", "resized.png")
                        ImageIO.write(resizedImage, "png", File(src_path))
                        converted_file = True

            elif file_ext in {".wav", ".mp3"}:
                target_dir = sounds_path
                if file_ext == ".wav":
                    if not wavconverter.is_android_compatible_wav(src_path):
                        temp_path = src_path.replace(".wav", "converted.wav")
                        wavconverter.convert_to_android_compatible_wav(src_path, temp_path)
                        src_path = temp_path
                        converted_file = True

            else:
                assert file_ext in {".json"}, md5_name
                continue

            assert os.path.exists(src_path), "Not existing: {}".format(src_path)
            if converted_file:
                md5_name = update_md5_hash(md5_name, src_path)
            # if file is used multiple times: single md5, multiple filenames
            for catroid_file_name in _convert_resource_name(sb2_project, md5_name):
                shutil.copyfile(src_path, os.path.join(target_dir, catroid_file_name))
            if converted_file:
                os.remove(src_path)

    def xml_content_of_catroid_project(catroid_project):
        storage_handler = catio.StorageHandler().getInstance()
        code_xml_content = storage_handler.XML_HEADER
        xml_header = catroid_project.getXmlHeader()
        xml_header.setApplicationBuildName(common.APPLICATION_NAME)
        # TODO: find resource with application name
        # TODO: parse application version from android manifest?
        # TODO: parse platform version
        xml_header.setApplicationName("Pocket Code")
        xml_header.setDeviceName(common.APPLICATION_NAME)
        xml_header.programLicense = sb2.LICENSE_URI
        xml_header.mediaLicense = sb2.LICENSE_URI
        xml_header.remixOf = sb2webapi.HTTP_PROJECT_URL_PREFIX + xml_header.getProgramName()
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


def _convert_formula(raw_source, sprite, project):
    tokens = []
    user_variables = project.getUserVariables()
    if not isinstance(raw_source, list):
        raw_source = [raw_source]
    for elem in raw_source:
        if isinstance(elem, (str, unicode)):

            operator = _ScratchToCatrobat.operator(elem)
            if operator:
                pass

            elif elem.endswith(":"):
                user_var = user_variables.getUserVariable(elem, sprite)
                if not user_var:
                    log.warning("Unknown variable '{}'. Aborting formula.".format(elem))
                    return catformula.Formula(catformula.FormulaElement(catformula.FormulaElement.ElementType.FUNCTION, catformula.Functions.TRUE, None))
                tokens += [catformula.InternToken(catformula.InternTokenType.USER_VARIABLE, elem)]
            else:
                assert False, "Unsupported type: {} of '{}'".format(type(elem), elem)
        elif isinstance(elem, (int, long, float, complex)):
                tokens += [catformula.InternToken(catformula.InternTokenType.NUMBER, str(elem))]
        else:
            log.warning("Unknown variable '{}'. Aborting formula.".format(elem))
            return catformula.Formula(catformula.FormulaElement(catformula.FormulaElement.ElementType.FUNCTION, catformula.Functions.TRUE, None))
            assert False, "Unsupported type: {} of '{}'".format(type(elem), elem)
    return catformula.Formula(catformula.InternFormulaParser(tokens, project, sprite).parseFormula())
