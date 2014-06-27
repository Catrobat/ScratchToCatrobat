#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2014 The Catrobat Team
#  (<http://developer.catrobat.org/credits>)
#
#  This program is free software: you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation, either version 3 of the
#  License, or (at your option) any later version.
#
#  An additional term exception under section 7 of the GNU Affero
#  General Public License, version 3, is available at
#  http://developer.catrobat.org/license_additional_term
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public License
#  along with this program.  If not, see <http://www.gnu.org/licenses/>.
from __future__ import unicode_literals

import os
import shutil
import zipfile
from codecs import open

import org.catrobat.catroid.common as catcommon
import org.catrobat.catroid.content as catbase
import org.catrobat.catroid.content.bricks as catbricks
import org.catrobat.catroid.formulaeditor as catformula
import org.catrobat.catroid.io as catio

from scratchtocatrobat import catrobat
from scratchtocatrobat import common
from scratchtocatrobat import scratch
from scratchtocatrobat import scratchwebapi
from scratchtocatrobat.scratch import JsonKeys as scratchkeys
from scratchtocatrobat.tools import svgtopng
from scratchtocatrobat.tools import wavconverter

_DEFAULT_BRICK_CLASS = catbricks.WaitBrick

log = common.log


def _key_to_broadcast_message(key_name):
    return "key " + key_name + " pressed"


def _background_look_to_broadcast_message(look_name):
    return "start background scene: " + look_name


def _next_background_look_broadcast_message():
    return "set background to next look"


class _ScratchToCatrobat(object):

    # based on: http://code.google.com/p/scratch-js/source/browse/trunk/editor.htm
    # note: for bricks without mapping (value set to 'None') placeholder bricks will be added
    SCRATCH_TO_CATROBAT_MAPPING = {
        #===========================================================================
        # Scripts
        #===========================================================================
        "whenGreenFlag": catbase.StartScript,
        "whenIReceive": catbase.BroadcastScript,
        "whenKeyPressed": lambda sprite, key: catbase.BroadcastScript(sprite, _key_to_broadcast_message(key)),
        "whenSensorGreaterThan": None,
        "whenSceneStarts": lambda sprite, look_name: catbase.BroadcastScript(sprite, _background_look_to_broadcast_message(look_name)),  # easy: stage msg broadcast
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
        "startScene": catbricks.BroadcastBrick,  # easy: msg broadcast
        "nextScene": catbricks.NextLookBrick,  # only allowed in scene object so same as nextLook

        "say:duration:elapsed:from:": None,
        "say:": None,
        "think:duration:elapsed:from:": None,
        "think:": None,
        "changeGraphicEffect:by:": lambda sprite, effectType, value: \
            catbricks.ChangeBrightnessByNBrick(sprite, value) if effectType == 'brightness' else \
                (catbricks.ChangeGhostEffectByNBrick(sprite, value) if effectType == 'ghost' else None),  # easy: for ghost, brightness
        "setGraphicEffect:to:": lambda sprite, effectType, value: \
            catbricks.SetBrightnessBrick(sprite, value) if effectType == 'brightness' else \
                (catbricks.SetGhostEffectBrick(sprite, value) if effectType == 'ghost' else None),  # easy: for ghost, brightness
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

        "doAsk": None,
        "timerReset": None,

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
    def catrobat_brick_for(cls, scratchname):
        assert isinstance(scratchname, (str, unicode))
        if not scratchname  in cls.SCRATCH_TO_CATROBAT_MAPPING:
            raise common.ScratchtobatError("Unknown brick identifier: {}".format(scratchname))
        return cls.SCRATCH_TO_CATROBAT_MAPPING[scratchname]

    @classmethod
    def create_script(cls, scratchscript_name, sprite, arguments):
        assert sprite is not None
        if not scratchscript_name in scratch.SCRATCH_SCRIPTS:
            assert False, "Missing script mapping for: " + scratchscript_name
        # TODO: separate script and brick mapping
        return cls.catrobat_brick_for(scratchscript_name)(sprite, *arguments)

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
    assert key is not None
    key_path = _key_image_path_for(key)
    # TODO: extract method, already used once
    return common.md5_hash(key_path) + "_" + _key_to_broadcast_message(key) + os.path.splitext(key_path)[1]


_catr_project = None


def _convert_to_catrobat_program(scratch_project):
    global _catr_project
    _catr_project = catbase.Project(None, scratch_project.name)
    _catr_project.getXmlHeader().virtualScreenHeight = scratch.STAGE_HEIGHT_IN_PIXELS
    _catr_project.getXmlHeader().virtualScreenWidth = scratch.STAGE_WIDTH_IN_PIXELS
    for object_ in scratch_project.project_code.objects:
        catr_sprite = _convert_to_catrobat_sprite(object_)
        if object_ is scratch_project.project_code.stage_object:
            catr_sprite.setName(catrobat.BACKGROUND_SPRITE_NAME)
        _catr_project.addSprite(catr_sprite)

    def add_used_key_sprites(listened_keys, _catr_project):
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
            y_pos = (scratch.STAGE_HEIGHT_IN_PIXELS / 2) - 40 * height_pos
            x_pos = -(scratch.STAGE_WIDTH_IN_PIXELS / 2) + 40 * (width_pos + 1)
            place_at_brick = catbricks.PlaceAtBrick(key_sprite, x_pos, y_pos)

            bricks = [place_at_brick, set_look_brick, catbricks.SetSizeToBrick(key_sprite, 33)]
            when_started_script.getBrickList().addAll(bricks)
            key_sprite.addScript(when_started_script)

            when_tapped_script = catbase.WhenScript(key_sprite)
            when_tapped_script.addBrick(catbricks.BroadcastBrick(key_sprite, key_message))
            key_sprite.addScript(when_tapped_script)

            _catr_project.addSprite(key_sprite)

    add_used_key_sprites(scratch_project.listened_keys, _catr_project)

    return _catr_project


def _convert_to_catrobat_sprite(scratch_object):
    if not isinstance(scratch_object, scratch.Object):
        raise common.ScratchtobatError("Input must be of type={}, but is={}".format(scratch.Object, type(scratch_object)))
    sprite = catbase.Sprite(scratch_object.get_objName())

    sprite_looks = sprite.getLookDataList()
    costume_resolution = None
    for scratch_costume in scratch_object.get_costumes():
        current_costume_resolution = scratch_costume.get(scratchkeys.COSTUME_RESOLUTION)
        if not costume_resolution:
            costume_resolution = current_costume_resolution
        else:
            if current_costume_resolution != costume_resolution:
                log.warning("Costume resolution not same for all costumes")
        sprite_looks.add(_convert_to_catrobat_look(scratch_costume))

    sprite_sounds = sprite.getSoundList()
    for scratch_sound in scratch_object.get_sounds():
        sprite_sounds.add(_convert_to_catrobat_sound(scratch_sound))

    # looks and sounds has to added first because of cross-validations
    for scratch_script in scratch_object.scripts:
        sprite.addScript(_convert_to_catrobat_script(scratch_script, sprite))

    def add_initial_scratch_object_behaviour():
        # some initial Scratch settings are done with a general JSON configuration instead with bricks. Here the equivalent bricks are added for catrobat.
        def get_or_add_startscript(sprite):
            # HACK: accessing private member, enabled with Jython registry security settings
            for script in sprite.scriptList:
                if isinstance(script, catbase.StartScript):
                    return script
            else:
                start_script = catbase.StartScript(sprite)
                sprite.addScript(0, start_script)
                return start_script
        implicit_bricks_to_add = []

        # object's currentCostumeIndex determines active costume at startup
        sprite_startup_look_idx = scratch_object.get_currentCostumeIndex()
        if sprite_startup_look_idx is not None:
            spriteStartupLook = sprite.getLookDataList()[sprite_startup_look_idx]
            set_look_brick = catbricks.SetLookBrick(sprite)
            set_look_brick.setLook(spriteStartupLook)
            implicit_bricks_to_add += [set_look_brick]

        # object's scratchX and scratchY Keys determine position
        x_pos = scratch_object.get_scratchX() or 0
        y_pos = scratch_object.get_scratchY() or 0
        place_at_brick = catbricks.PlaceAtBrick(sprite, int(x_pos), int(y_pos))
        implicit_bricks_to_add += [place_at_brick]

        object_scale = scratch_object.get_scale() or 1
        implicit_bricks_to_add += [catbricks.SetSizeToBrick(sprite, object_scale * 100.0 / costume_resolution)]

        object_direction = scratch_object.get_direction() or 90
        implicit_bricks_to_add += [catbricks.PointInDirectionBrick(sprite, object_direction)]

        object_visible = scratch_object.get_visible()
        if object_visible is not None and not object_visible:
            implicit_bricks_to_add += [catbricks.HideBrick(sprite)]

        rotation_style = scratch_object.get_rotationStyle()
        if rotation_style and rotation_style != "normal":
            log.warning("Unsupported rotation style '{}' at object: {}".format(rotation_style, scratch_object.get_objName()))

        start_script = get_or_add_startscript(sprite)
        start_script.getBrickList().addAll(0, implicit_bricks_to_add)

    add_initial_scratch_object_behaviour()
    return sprite


def _convert_to_catrobat_script(scratch_script, sprite):
    if not isinstance(scratch_script, scratch.Script):
        raise common.ScratchtobatError("Arg1 must be of type={}, but is={}".format(scratch.Script, type(scratch_script)))
    if sprite and not isinstance(sprite, catbase.Sprite):
        raise common.ScratchtobatError("Arg2 must be of type={}, but is={}".format(catbase.Sprite, type(sprite)))

    cat_script = _ScratchToCatrobat.create_script(scratch_script.type, sprite, scratch_script.arguments)
    for scratch_brick in scratch_script.bricks:
        cat_bricks = _convert_to_catrobat_bricks(scratch_brick, sprite)
        for brick in cat_bricks:
            cat_script.addBrick(brick)
    return cat_script


def _convert_to_catrobat_bricks(scratch_brick, catr_sprite):
    global _catr_project

    def add_placeholder_for_unmapped_bricks_to(catr_bricks, catr_sprite, brick_name):
        catr_bricks += [_DEFAULT_BRICK_CLASS(catr_sprite, 500), catbricks.NoteBrick(catr_sprite, "Missing brick for scratch identifier: " + brick_name)]
    common.log.debug("Brick to convert={}".format(scratch_brick))
    if not scratch_brick or not (isinstance(scratch_brick, list) and isinstance(scratch_brick[0], (str, unicode))):
        raise common.ScratchtobatError("Wrong arg1, must be list with string as first element: {!r}".format(scratch_brick))
    if not isinstance(catr_sprite, catbase.Sprite):
        raise common.ScratchtobatError("Wrong arg2, must be of type={}, but is={}".format(catbase.Sprite, type(catr_sprite)))
    brick_name = scratch_brick[0]
    brick_arguments = scratch_brick[1:]
    catr_bricks = []
    catrobat_brick_class = _ScratchToCatrobat.catrobat_brick_for(brick_name)
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
            assert _catr_project
            if_begin_brick = catbricks.IfLogicBeginBrick(catr_sprite, _convert_formula(brick_arguments[0], catr_sprite, _catr_project))
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

        elif brick_name == "startScene":
            assert _catr_project

            [look_name] = brick_arguments
            background_sprite = catrobat.background_sprite_of_project(_catr_project)
            if not background_sprite:
                # if no background sprite found, we are just building it now
                background_sprite = catr_sprite
            matching_looks = [_ for _ in background_sprite.getLookDataList() if _.getLookName() == look_name]
            if not matching_looks:
                raise ConversionError("Background does not contain look with name: {}".format(look_name))
            assert len(matching_looks) == 1
            [matching_look] = matching_looks
            look_message = _background_look_to_broadcast_message(look_name)
            broadcast_brick = catrobat_brick_class(catr_sprite, look_message)
            catr_bricks += [broadcast_brick]

            broadcast_script = catbase.BroadcastScript(background_sprite, look_message)
            set_look_brick = catbricks.SetLookBrick(background_sprite)
            set_look_brick.setLook(matching_look)
            broadcast_script.addBrick(set_look_brick)
            background_sprite.addScript(broadcast_script)

        elif catrobat_brick_class in set([catbricks.SetLookBrick]):
            set_look_brick = catrobat_brick_class(catr_sprite)
            [look_name] = brick_arguments
            [look] = [look for look in catr_sprite.getLookDataList() if look.getLookName() == look_name]
            set_look_brick.setLook(look)
            catr_bricks += [set_look_brick]

        else:
            common.log.debug("Get mapping for {} in {}".format(brick_name, catr_sprite))
            catrobat_class = catrobat_brick_class
            if not catrobat_class:
                common.log.warning("No mapping for: '{}', arguments: {}".format(brick_name, brick_arguments))
                add_placeholder_for_unmapped_bricks_to(catr_bricks, catr_sprite, brick_name)
            else:
                assert not isinstance(catrobat_class, list), "Wrong at: {1}, {0}".format(brick_arguments, brick_name)
                # conditionals for argument convertions
                if brick_arguments:
                    if catrobat_class in set([catbricks.ChangeVariableBrick, catbricks.SetVariableBrick]):
                        assert _catr_project
                        variable, value = brick_arguments
                        brick_arguments = [_convert_formula(value, catr_sprite, _catr_project), _catr_project.getUserVariables().getUserVariable(variable, catr_sprite)]
                    elif catrobat_class == catbricks.GlideToBrick:
                        secs, x_dest_pos, y_dest_pos = brick_arguments
                        brick_arguments = [x_dest_pos, y_dest_pos, secs * 1000]
                try:
                    catr_bricks += [catrobat_class(catr_sprite, *brick_arguments)]
                except TypeError as e:
                    common.log.exception(e)
                    common.log.info("Replacing with default brick")
                    catr_bricks += [catbricks.WaitBrick(catr_sprite, 1000)]
    except TypeError as e:
        common.log.exception(e)
        common.log.info("Replacing with default brick")
        catr_bricks += [catbricks.WaitBrick(catr_sprite, 1000)]
        # assert False, "Non-matching arguments of scratch brick '{1}': {0}".format(brick_arguments, brick_name)

    return catr_bricks


def _convert_to_catrobat_look(costume):
    if not costume or not (isinstance(costume, dict) and all(_ in costume for _ in (scratchkeys.COSTUME_MD5, scratchkeys.COSTUMENAME_KEY))):
        raise common.ScratchtobatError("Wrong input, must be costume dict: {}".format(costume))
    look = catcommon.LookData()

    assert scratchkeys.COSTUMENAME_KEY  in costume
    costume_name = costume[scratchkeys.COSTUMENAME_KEY]
    look.setLookName(costume_name)

    assert scratchkeys.COSTUME_MD5 in costume
    costume_filename = costume[scratchkeys.COSTUME_MD5]
    costume_filename_ext = os.path.splitext(costume_filename)[1]
    look.setLookFilename(costume_filename.replace(costume_filename_ext, "_" + costume_name + costume_filename_ext))
    return look


def _convert_to_catrobat_sound(sound):
    soundinfo = catcommon.SoundInfo()

    assert scratchkeys.SOUNDNAME_KEY in sound
    sound_name = sound[scratchkeys.SOUNDNAME_KEY]
    soundinfo.setTitle(sound_name)

    assert scratchkeys.SOUND_MD5 in sound
    sound_filename = sound[scratchkeys.SOUND_MD5]
    sound_filename_ext = os.path.splitext(sound_filename)[1]
    soundinfo.setSoundFileName(sound_filename.replace(sound_filename_ext, "_" + sound_name + sound_filename_ext))
#     soundinfo.setSoundFileName(sound_filename.replace(sound_filename_ext, "_" + sound_name))
    return soundinfo


class ConversionError(common.ScratchtobatError):
        pass


def convert_scratch_project_to_catrobat_zip(project, output_dir):
    def iter_dir(path):
        for root, _, files in os.walk(path):
            for file_ in files:
                yield os.path.join(root, file_)
    log.info("convert Scratch project to '%s'", output_dir)
    with common.TemporaryDirectory() as catrobat_program_dir:
        convert_scratch_project_to_catrobat_file_structure(project, catrobat_program_dir)
        common.makedirs(output_dir)
        catrobat_zip_file_path = os.path.join(output_dir, project.name + catrobat.PACKAGED_PROGRAM_FILE_EXTENSION)
        if os.path.exists(catrobat_zip_file_path):
            shutil.rmtree(catrobat_zip_file_path)
        with zipfile.ZipFile(catrobat_zip_file_path, 'w') as zip_fp:
            for file_path in iter_dir(unicode(catrobat_program_dir)):
                assert isinstance(file_path, unicode)
                path_inside_zip = file_path.replace(catrobat_program_dir, u"")
                zip_fp.write(file_path, path_inside_zip)
        assert zip_fp.fp is None or zip_fp.fp.closed

    return catrobat_zip_file_path


def images_dir_of_project(temp_dir):
    return os.path.join(temp_dir, "images")


def sounds_dir_of_project(temp_dir):
    return os.path.join(temp_dir, "sounds")


def convert_scratch_project_to_catrobat_file_structure(scratch_project, temp_path):

    def create_directory_structure():
        sounds_path = sounds_dir_of_project(temp_path)
        os.mkdir(sounds_path)

        images_path = images_dir_of_project(temp_path)
        os.mkdir(images_path)

        for _ in (temp_path, sounds_path, images_path):
            # TODO: into common module
            open(os.path.join(_, catrobat.ANDROID_IGNORE_MEDIA_MARKER_FILE_NAME), 'a').close()
        return sounds_path, images_path

    def write_mediafiles():
        def resource_name_for(file_path):
            return common.md5_hash(file_path) + os.path.splitext(file_path)[1]

        def update_resource_name(old_resource_name, new_resource_name):
            resource_maps = list(scratch_project.project_code.find_all_resource_dicts_for(old_resource_name))
            assert len(resource_maps) > 0
            for resource_map in resource_maps:
                if scratchkeys.COSTUME_MD5 in resource_map:
                    resource_map[scratchkeys.COSTUME_MD5] = new_resource_name
                elif scratchkeys.SOUND_MD5 in resource_map:
                    resource_map[scratchkeys.SOUND_MD5] = new_resource_name
                else:
                    assert False, "Unknown dict: {}".resource_map

        for md5_name, src_path in scratch_project.md5_to_resource_path_map.iteritems():
            if md5_name in scratch_project.unused_resource_names:
                log.info("Ignoring unused resource file: %s", src_path)
                continue

            file_ext = os.path.splitext(md5_name)[1].lower()
            converted_file = False

            # TODO; extract method
            if file_ext in {".png", ".svg", ".jpg", ".gif"}:
                target_dir = images_path

                if file_ext == ".svg":
                    # converting svg to png -> new md5 and filename
                    src_path = svgtopng.convert(src_path)
                    if not os.path.exists(src_path):
                        assert False, "Not existing: {}. Available files in directory: {}".format(src_path, os.listdir(os.path.dirname(src_path)))
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
                assert file_ext in {".json"}, "Unknown media file extension: %s" % src_path
                continue

            assert os.path.exists(src_path), "Not existing: {}. Available files in directory: {}".format(src_path, os.listdir(os.path.dirname(src_path)))
            if converted_file:
                new_resource_name = resource_name_for(src_path)
                update_resource_name(md5_name, new_resource_name)
                md5_name = new_resource_name
            # if file is used multiple times: single md5, multiple filenames
            for catrobat_file_name in converted_resource_names(md5_name, scratch_project):
                shutil.copyfile(src_path, os.path.join(target_dir, catrobat_file_name))
            if converted_file:
                os.remove(src_path)

    def program_source_for(catrobat_project):
        storage_handler = catio.StorageHandler()
        code_xml_content = storage_handler.XML_HEADER
        xml_header = catrobat_project.getXmlHeader()
        xml_header.setApplicationBuildName(common.APPLICATION_NAME)
        # TODO: find resource with application name
        # TODO: parse application version from android manifest?
        # TODO: parse platform version
        xml_header.setApplicationName("Pocket Code")
        xml_header.setDeviceName(common.APPLICATION_NAME)
        xml_header.catrobatLanguageVersion = catcommon.Constants.CURRENT_CATROBAT_LANGUAGE_VERSION
        xml_header.programLicense = scratch.LICENSE_URI
        xml_header.mediaLicense = scratch.LICENSE_URI
        xml_header.remixOf = scratchwebapi.HTTP_PROJECT_URL_PREFIX + xml_header.getProgramName()
        code_xml_content += storage_handler.getXMLStringOfAProject(catrobat_project)
        return code_xml_content

    def write_program_source():
        catrobat_program = _convert_to_catrobat_program(scratch_project)
        program_source = program_source_for(catrobat_program)
        with open(os.path.join(temp_path, catrobat.PROGRAM_SOURCE_FILE_NAME), "wb") as fp:
            fp.write(program_source.encode("utf8"))

        # copying key images needed for keyPressed substitution
        for listened_key in scratch_project.listened_keys:
            key_image_path = _key_image_path_for(listened_key)
            shutil.copyfile(key_image_path, os.path.join(images_path, _key_filename_for(listened_key)))

    # TODO: rename/rearrange abstracting methods
    log.info("  Creating Catrobat project structure")
    sounds_path, images_path = create_directory_structure()
    log.info("  Saving media files")
    write_mediafiles()
    log.info("  Saving project XML file")
    write_program_source()


def converted_resource_names(scratch_resource_name, project):
    assert os.path.basename(scratch_resource_name) == scratch_resource_name and len(os.path.splitext(scratch_resource_name)[0]) == 32, "Must be MD5 hash with file ext: " + scratch_resource_name
    catrobat_resource_names = []
    md5_name = scratch_resource_name
    for resource in project.project_code.find_all_resource_dicts_for(md5_name):
        if resource:
            try:
                resource_name = resource[scratchkeys.SOUNDNAME_KEY] if scratchkeys.SOUNDNAME_KEY in resource else resource[scratchkeys.COSTUMENAME_KEY]
            except KeyError:
                raise ConversionError("Error with: {}, {}".format(md5_name, resource))
            resource_ext = os.path.splitext(md5_name)[1]
            catrobat_resource_names += [md5_name.replace(resource_ext, "_" + resource_name + resource_ext)]
    assert len(catrobat_resource_names) != 0, "{} not found (path: {}). available: {}".format(scratch_resource_name, project.md5_to_resource_path_map.get(scratch_resource_name), project.project_code.resource_names)
    return catrobat_resource_names


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
                    return catformula.Formula(catformula.FormulaElement(catformula.FormulaElement.ElementType.FUNCTION, catformula.Functions.TRUE, 1.0))
                tokens += [catformula.InternToken(catformula.InternTokenType.USER_VARIABLE, elem)]
            else:
                assert False, "Unsupported type: {} of '{}'".format(type(elem), elem)
        elif isinstance(elem, (int, long, float, complex)):
                tokens += [catformula.InternToken(catformula.InternTokenType.NUMBER, str(elem))]
        else:
            log.warning("Unknown variable '{}'. Aborting formula.".format(elem))
            return catformula.Formula(catformula.FormulaElement(catformula.FormulaElement.ElementType.FUNCTION, catformula.Functions.TRUE, 1.0))
            assert False, "Unsupported type: {} of '{}'".format(type(elem), elem)
    return catformula.Formula(catformula.InternFormulaParser(tokens, project, sprite).parseFormula())
