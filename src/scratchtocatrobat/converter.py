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

import collections
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
from scratchtocatrobat import version
from scratchtocatrobat.scratch import JsonKeys as scratchkeys
from scratchtocatrobat.tools import svgtopng
from scratchtocatrobat.tools import wavconverter


class _SpecialCasePlaceholder(object):
    pass

_DEFAULT_BRICK_CLASS = catbricks.WaitBrick
_SPECIAL_CASE_BRICK_CLASS = _SpecialCasePlaceholder()

_SOUND_LENGTH_VARIABLE_NAME_FORMAT = "length_of_{}_in_msecs"

log = common.log


def _key_to_broadcast_message(key_name):
    return "key " + key_name + " pressed"


def _background_look_to_broadcast_message(look_name):
    return "start background scene: " + look_name


def _next_background_look_broadcast_message():
    return "set background to next look"


class _ScratchToCatrobat(object):

    # based on: http://code.google.com/p/scratch-js/source/browse/trunk/editor.htm
    # note: for Scratch blocks without mapping (value set to 'None') placeholder Catrobat bricks will be added
    SCRATCH_TO_CATROBAT_MAPPING = {
        #
        # Scripts
        #
        "whenGreenFlag": catbase.StartScript,
        "whenIReceive": catbase.BroadcastScript,
        "whenKeyPressed": lambda sprite, key: catbase.BroadcastScript(sprite, _key_to_broadcast_message(key)),
        "whenSensorGreaterThan": None,
        "whenSceneStarts": lambda sprite, look_name: catbase.BroadcastScript(sprite, _background_look_to_broadcast_message(look_name)),
        "whenClicked": catbase.WhenScript,

        #
        # Bricks
        #
        "broadcast:": catbricks.BroadcastBrick,
        "doBroadcastAndWait": catbricks.BroadcastBrick,  # FIXME: not correct
        "doReturn": None,
        "doWaitUntil": None,
        "wait:elapsed:from:": lambda sprite, time_value: catbricks.WaitBrick(sprite, int(time_value * 1000)),
        "stopAll": None,
        "stopScripts": None,

        # conditionals
        "doForever": catbricks.ForeverBrick,
        "doIf": [catbricks.IfLogicBeginBrick, catbricks.IfLogicEndBrick],
        "doIfElse": [catbricks.IfLogicBeginBrick, catbricks.IfLogicElseBrick, catbricks.IfLogicEndBrick],
        "doRepeat": catbricks.RepeatBrick,
        "doUntil": None,

        "turnRight:": catbricks.TurnRightBrick,
        "turnLeft:": catbricks.TurnLeftBrick,
        "heading:": catbricks.PointInDirectionBrick,
        "forward:": catbricks.MoveNStepsBrick,
        "pointTowards:": catbricks.PointToBrick,
        "gotoX:y:": catbricks.PlaceAtBrick,
        "glideSecs:toX:y:elapsed:from:": catbricks.GlideToBrick,
        "xpos:": catbricks.SetXBrick,
        "ypos:": catbricks.SetYBrick,
        "bounceOffEdge": catbricks.IfOnEdgeBounceBrick,
        "changeXposBy:": catbricks.ChangeXByNBrick,
        "changeYposBy:": catbricks.ChangeYByNBrick,

        # variables
        "setVar:to:": catbricks.SetVariableBrick,
        "changeVar:by:": catbricks.ChangeVariableBrick,
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
        "startScene": catbricks.BroadcastBrick,
        "nextScene": catbricks.NextLookBrick,  # only allowed in scene object so same as nextLook

        "say:duration:elapsed:from:": None,
        "say:": None,
        "think:duration:elapsed:from:": None,
        "think:": None,
        # TODO: remove lambdas to increase readability
        "changeGraphicEffect:by:": lambda sprite, effectType, value:
            catbricks.ChangeBrightnessByNBrick(sprite, value) if effectType == 'brightness' else (catbricks.ChangeGhostEffectByNBrick(sprite, value) if effectType == 'ghost' else None),
        "setGraphicEffect:to:": lambda sprite, effectType, value:
            catbricks.SetBrightnessBrick(sprite, value) if effectType == 'brightness' else (catbricks.SetGhostEffectBrick(sprite, value) if effectType == 'ghost' else None),
        "filterReset": catbricks.ClearGraphicEffectBrick,
        "changeSizeBy:": catbricks.ChangeSizeByNBrick,
        "setSizeTo:": catbricks.SetSizeToBrick,
        "show": catbricks.ShowBrick,
        "hide": catbricks.HideBrick,
        "comeToFront": catbricks.ComeToFrontBrick,
        "goBackByLayers:": catbricks.GoNStepsBackBrick,

        # sound
        "playSound:": catbricks.PlaySoundBrick,
        "doPlaySoundAndWait": _SPECIAL_CASE_BRICK_CLASS,
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
        "rounded": None,  # TODO
        "computeFunction:of:": None,  # TODO
        "randomFrom:to:": None,  # TODO

        # variables
        "readVariable": None,  # TODO

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
        "scale": None,  # TODO
    }

    OPERATORS_MAPPING = {
        "+": catformula.Operators.PLUS,
        "-": catformula.Operators.MINUS,
        "*": catformula.Operators.MULT,
        "/": catformula.Operators.DIVIDE,
        "<": catformula.Operators.SMALLER_THAN,
        "=": catformula.Operators.EQUAL,
        ">": catformula.Operators.GREATER_THAN,
        "&": catformula.Operators.LOGICAL_AND,
        "|": catformula.Operators.LOGICAL_OR,
        "not": catformula.Operators.LOGICAL_NOT,
    }

    @classmethod
    def catrobat_brick_for(cls, scratch_block_name):
        assert isinstance(scratch_block_name, (str, unicode))
        if scratch_block_name not in cls.SCRATCH_TO_CATROBAT_MAPPING:
            raise common.ScratchtobatError("Unknown Scratch block name: {}".format(scratch_block_name))
        return cls.SCRATCH_TO_CATROBAT_MAPPING[scratch_block_name]

    @classmethod
    def create_script(cls, scratch_script_name, sprite, arguments):
        assert sprite is not None
        if scratch_script_name not in scratch.SCRATCH_SCRIPTS:
            assert False, "Missing script mapping for: " + scratch_script_name
        # TODO: separate script and brick mapping
        return cls.catrobat_brick_for(scratch_script_name)(sprite, *arguments)

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


def _update_xml_header(xml_header, scratch_project):
    xml_header.setApplicationBuildName("*** TODO ***")
    xml_header.setApplicationName(common.APPLICATION_NAME)
    xml_header.setApplicationVersion(version.__version__)
    xml_header.setCatrobatLanguageVersion(catcommon.Constants.CURRENT_CATROBAT_LANGUAGE_VERSION)
    xml_header.setDescription(scratch_project.description)
    xml_header.setDeviceName("Scratch")
    xml_header.setPlatform("Scratch")
    # TODO: platform version should allow float
    xml_header.setPlatformVersion(2)
    xml_header.setScreenMode(catcommon.ScreenModes.MAXIMIZE)
    xml_header.mediaLicense = catrobat.MEDIA_LICENSE_URI
    xml_header.programLicense = catrobat.PROGRAM_LICENSE_URI
    if scratch_project.project_id is not None:
        xml_header.remixOf = scratch.HTTP_PROJECT_URL_PREFIX + scratch_project.project_id

_catr_project = None


def catrobat_program_from(scratch_project):
    global _catr_project
    _catr_project = catbase.Project(None, scratch_project.name)
    _catr_project.getXmlHeader().virtualScreenHeight = scratch.STAGE_HEIGHT_IN_PIXELS
    _catr_project.getXmlHeader().virtualScreenWidth = scratch.STAGE_WIDTH_IN_PIXELS
    for object_ in scratch_project.objects:
        catr_sprite = _catrobat_sprite_from(object_)
        if object_ is scratch_project.stage_object:
            catr_sprite.setName(catrobat.BACKGROUND_SPRITE_NAME)
        _catr_project.addSprite(catr_sprite)

    # TODO: make it more explicit that this depends on the conversion code for "whenKeyPressed" Scratch block
    def add_used_key_sprites(listened_keys, catrobat_project):
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

            catrobat_project.addSprite(key_sprite)

    add_used_key_sprites(scratch_project.listened_keys, _catr_project)
    _update_xml_header(_catr_project.getXmlHeader(), scratch_project)
    return _catr_project


def _catrobat_sprite_from(scratch_object):
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
        sprite_looks.add(_catrobat_look_from(scratch_costume))

    sprite_sounds = sprite.getSoundList()
    for scratch_sound in scratch_object.get_sounds():
        sprite_sounds.add(_catrobat_sound_from(scratch_sound))

    # looks and sounds has to added first because of cross-validations
    for scratch_script in scratch_object.scripts:
        sprite.addScript(_catrobat_script_from(scratch_script, sprite))

    def add_initial_scratch_object_behaviour():
        # some initial Scratch settings are done with a general JSON configuration instead with blocks. Here the equivalent bricks are added for Catrobat.
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

        catrobat.add_to_start_script(implicit_bricks_to_add, sprite)

    add_initial_scratch_object_behaviour()
    return sprite


def _catrobat_script_from(scratch_script, sprite):
    if not isinstance(scratch_script, scratch.Script):
        raise common.ScratchtobatError("Arg1 must be of type={}, but is={}".format(scratch.Script, type(scratch_script)))
    if sprite and not isinstance(sprite, catbase.Sprite):
        raise common.ScratchtobatError("Arg2 must be of type={}, but is={}".format(catbase.Sprite, type(sprite)))

    cat_script = _ScratchToCatrobat.create_script(scratch_script.type, sprite, scratch_script.arguments)
    for scratch_block in scratch_script.blocks:
        cat_bricks = _catrobat_bricks_from(scratch_block, sprite)
        for brick in cat_bricks:
            cat_script.addBrick(brick)
    return cat_script


def _catrobat_bricks_from(scratch_block, catr_sprite):
    global _catr_project

    def add_placeholder_for_unmapped_blocks_to(catr_bricks, catr_sprite, block_name):
        catr_bricks += [_DEFAULT_BRICK_CLASS(catr_sprite, 500), catbricks.NoteBrick(catr_sprite, "Missing brick for scratch identifier: " + block_name)]
    common.log.debug("Brick to convert={}".format(scratch_block))
    if not scratch_block or not (isinstance(scratch_block, list) and isinstance(scratch_block[0], (str, unicode))):
        raise common.ScratchtobatError("Wrong arg1, must be list with string as first element: {!r}".format(scratch_block))
    if not isinstance(catr_sprite, catbase.Sprite):
        raise common.ScratchtobatError("Wrong arg2, must be of type={}, but is={}".format(catbase.Sprite, type(catr_sprite)))
    block_name = scratch_block[0]
    block_arguments = scratch_block[1:]
    catr_bricks = []
    catrobat_brick_class = _ScratchToCatrobat.catrobat_brick_for(block_name)
    try:
        # Conditionals for cases which need additional handling after brick object instantiation
        if block_name in {'doRepeat', 'doForever'}:
            if block_name == 'doRepeat':
                times_value, nested_blocks = block_arguments
                if isinstance(times_value, list):
                    common.log.warning("Unsupported times_value: {}. Set to default (1).".format(times_value))
                    times_value = 1
                catr_loop_start_brick = catrobat_brick_class(catr_sprite, times_value)
            elif block_name == 'doForever':
                [nested_blocks] = block_arguments
                catr_loop_start_brick = catrobat_brick_class(catr_sprite)
            else:
                assert False, "Missing conditional branch for: " + block_name

            catr_bricks += [catr_loop_start_brick]
            for block in nested_blocks:
                # Note: recursive call
                catr_bricks += _catrobat_bricks_from(block, catr_sprite)
            catr_bricks += [catbricks.LoopEndBrick(catr_sprite, catr_loop_start_brick)]

        elif block_name in ['doIf']:
            assert _catr_project
            if_begin_brick = catbricks.IfLogicBeginBrick(catr_sprite, _catrobat_formula_from(block_arguments[0], catr_sprite, _catr_project))
            if_else_brick = catbricks.IfLogicElseBrick(catr_sprite, if_begin_brick)
            if_end_brick = catbricks.IfLogicEndBrick(catr_sprite, if_else_brick, if_begin_brick)

            catr_bricks += [catbricks.RepeatBrick(catr_sprite), if_begin_brick]
            nested_blocks = block_arguments[1:]
            for block in nested_blocks:
                # Note: recursive call
                catr_bricks += _catrobat_bricks_from(block, catr_sprite)

            catr_bricks += [if_else_brick, if_end_brick, catbricks.LoopEndBrick(catr_sprite, catr_bricks[0])]

        elif block_name == "playSound:":
            [look_name] = block_arguments
            soundinfo_name_to_soundinfo_map = {lookdata.getTitle(): lookdata for lookdata in catr_sprite.getSoundList()}
            lookdata = soundinfo_name_to_soundinfo_map.get(look_name)
            if not lookdata:
                raise ConversionError("Sprite does not contain sound with name={}".format(look_name))
            play_sound_brick = catrobat_brick_class(catr_sprite)
            play_sound_brick.setSoundInfo(lookdata)
            catr_bricks += [play_sound_brick]

        elif block_name == "doPlaySoundAndWait":
            [look_name] = block_arguments
            soundinfo_name_to_soundinfo_map = {lookdata.getTitle(): lookdata for lookdata in catr_sprite.getSoundList()}
            lookdata = soundinfo_name_to_soundinfo_map.get(look_name)
            if not lookdata:
                raise ConversionError("Sprite does not contain sound with name={}".format(look_name))
            play_sound_brick = catbricks.PlaySoundBrick(catr_sprite)
            play_sound_brick.setSoundInfo(lookdata)
            catr_bricks += [play_sound_brick, catbricks.WaitBrick(catr_sprite, 0)]

        elif block_name == "startScene":
            assert _catr_project

            [look_name] = block_arguments
            background_sprite = catrobat.background_sprite_of(_catr_project)
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
            [look_name] = block_arguments
            [look] = [look for look in catr_sprite.getLookDataList() if look.getLookName() == look_name]
            set_look_brick.setLook(look)
            catr_bricks += [set_look_brick]

        else:
            common.log.debug("Get mapping for {} in {}".format(block_name, catr_sprite))
            catrobat_class = catrobat_brick_class
            if not catrobat_class:
                common.log.warning("No mapping for: '{}', arguments: {}".format(block_name, block_arguments))
                add_placeholder_for_unmapped_blocks_to(catr_bricks, catr_sprite, block_name)
            else:
                assert not isinstance(catrobat_class, list), "Wrong at: {1}, {0}".format(block_arguments, block_name)
                # conditionals for argument convertions
                if block_arguments:
                    if catrobat_class in set([catbricks.ChangeVariableBrick, catbricks.SetVariableBrick]):
                        assert _catr_project
                        variable, value = block_arguments
                        block_arguments = [_catrobat_formula_from(value, catr_sprite, _catr_project), _catr_project.getUserVariables().getUserVariable(variable, catr_sprite)]
                    elif catrobat_class == catbricks.GlideToBrick:
                        secs, x_dest_pos, y_dest_pos = block_arguments
                        block_arguments = [x_dest_pos, y_dest_pos, secs * 1000]
                try:
                    catr_bricks += [catrobat_class(catr_sprite, *block_arguments)]
                except TypeError as e:
                    common.log.exception(e)
                    common.log.info("Replacing with default brick")
                    catr_bricks += [catbricks.WaitBrick(catr_sprite, 1000)]
    except TypeError as e:
        common.log.exception(e)
        common.log.info("Replacing with default brick")
        catr_bricks += [catbricks.WaitBrick(catr_sprite, 1000)]
        # assert False, "Non-matching arguments of scratch brick '{1}': {0}".format(block_arguments, block_name)

    return catr_bricks


def _catrobat_look_from(scratch_costume):
    if not scratch_costume or not (isinstance(scratch_costume, dict) and all(_ in scratch_costume for _ in (scratchkeys.COSTUME_MD5, scratchkeys.COSTUME_NAME))):
        raise common.ScratchtobatError("Wrong input, must be costume dict: {}".format(scratch_costume))
    look = catcommon.LookData()

    assert scratchkeys.COSTUME_NAME in scratch_costume
    costume_name = scratch_costume[scratchkeys.COSTUME_NAME]
    look.setLookName(costume_name)

    assert scratchkeys.COSTUME_MD5 in scratch_costume
    costume_filename = scratch_costume[scratchkeys.COSTUME_MD5]
    costume_filename_ext = os.path.splitext(costume_filename)[1]
    look.setLookFilename(costume_filename.replace(costume_filename_ext, "_" + costume_name + costume_filename_ext))
    return look


def _catrobat_sound_from(scratch_sound):
    soundinfo = catcommon.SoundInfo()

    assert scratchkeys.SOUND_NAME in scratch_sound
    sound_name = scratch_sound[scratchkeys.SOUND_NAME]
    soundinfo.setTitle(sound_name)

    assert scratchkeys.SOUND_MD5 in scratch_sound
    sound_filename = scratch_sound[scratchkeys.SOUND_MD5]
    sound_filename_ext = os.path.splitext(sound_filename)[1]
    soundinfo.setSoundFileName(sound_filename.replace(sound_filename_ext, "_" + sound_name + sound_filename_ext))
    return soundinfo


class ConversionError(common.ScratchtobatError):
        pass


def converted_output_path(output_dir, project_name):
    return os.path.join(output_dir, project_name + catrobat.PACKAGED_PROGRAM_FILE_EXTENSION)


def save_as_catrobat_program_package_to(scratch_project, output_dir):
    def iter_dir(path):
        for root, _, files in os.walk(path):
            for file_ in files:
                yield os.path.join(root, file_)
    log.info("convert Scratch project to '%s'", output_dir)
    with common.TemporaryDirectory() as catrobat_program_dir:
        save_as_catrobat_program_to(scratch_project, catrobat_program_dir)
        common.makedirs(output_dir)
        catrobat_zip_file_path = converted_output_path(output_dir, scratch_project.name)
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


# TODO: change to OO
def save_as_catrobat_program_to(scratch_project, temp_path):

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

        # FIXME: modifies Scratch project object
        def update_resource_name(old_resource_name, new_resource_name):
            resource_maps = list(scratch_project.find_all_resource_dicts_for(old_resource_name))
            assert len(resource_maps) > 0
            for resource_map in resource_maps:
                if scratchkeys.COSTUME_MD5 in resource_map:
                    resource_map[scratchkeys.COSTUME_MD5] = new_resource_name
                elif scratchkeys.SOUND_MD5 in resource_map:
                    resource_map[scratchkeys.SOUND_MD5] = new_resource_name
                else:
                    assert False, "Unknown dict: {}".resource_map

        for scratch_md5_name, src_path in scratch_project.md5_to_resource_path_map.iteritems():
            if scratch_md5_name in scratch_project.unused_resource_names:
                log.info("Ignoring unused resource file: %s", src_path)
                continue

            file_ext = os.path.splitext(scratch_md5_name)[1].lower()
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
                update_resource_name(scratch_md5_name, new_resource_name)
                scratch_md5_name = new_resource_name
            # separate file name for each sprite in which a resource is used
            for catrobat_file_name in _catrobat_resource_file_name_for(scratch_md5_name, scratch_project):
                shutil.copyfile(src_path, os.path.join(target_dir, catrobat_file_name))
            if converted_file:
                os.remove(src_path)

    def program_source_for(catrobat_program):
        storage_handler = catio.StorageHandler()
        code_xml_content = storage_handler.XML_HEADER
        code_xml_content += storage_handler.getXMLStringOfAProject(catrobat_program)
        return code_xml_content

    def write_program_source():
        catrobat_program = catrobat_program_from(scratch_project)

        # TODO: extract method
        # note: at this position because of use of sounds_path variable
        # adding sound length variables needed for "doPlayAndWait" brick workaround
        sprite_to_variable_initializations_map = collections.defaultdict(list)
        for catrobat_sprite in catrobat_program.getSpriteList():
            for sound_info in catrobat_sprite.getSoundList():
                sound_length = common.length_of_audio_file_in_msec(os.path.join(sounds_path, sound_info.getSoundFileName()))
                variable = catrobat_program.getUserVariables().addSpriteUserVariableToSprite(catrobat_sprite, _sound_length_variable_name_for(sound_info.getTitle()))
                print catrobat_sprite.getName(), variable.getName()
                sprite_to_variable_initializations_map[catrobat_sprite] += [(variable, sound_length)]
        print sprite_to_variable_initializations_map
        for sprite, variable_initializations in sprite_to_variable_initializations_map.iteritems():
            variable_initialization_bricks = [catbricks.SetVariableBrick(sprite, catformula.Formula(value), variable) for variable, value in variable_initializations]
            catrobat.add_to_start_script(variable_initialization_bricks, sprite)

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


def _catrobat_resource_file_name_for(scratch_md5_name, scratch_project):
    assert os.path.basename(scratch_md5_name) == scratch_md5_name and len(os.path.splitext(scratch_md5_name)[0]) == 32, "Must be MD5 hash with file ext: " + scratch_md5_name
    catrobat_resource_names = []
    for resource in scratch_project.find_all_resource_dicts_for(scratch_md5_name):
        if resource:
            try:
                resource_name = resource[scratchkeys.SOUND_NAME] if scratchkeys.SOUND_NAME in resource else resource[scratchkeys.COSTUME_NAME]
            except KeyError:
                raise ConversionError("Error with: {}, {}".format(scratch_md5_name, resource))
            resource_ext = os.path.splitext(scratch_md5_name)[1]
            catrobat_resource_names += [scratch_md5_name.replace(resource_ext, "_" + resource_name + resource_ext)]
    assert len(catrobat_resource_names) != 0, "{} not found (path: {}). available: {}".format(scratch_md5_name, scratch_project.md5_to_resource_path_map.get(scratch_md5_name), scratch_project.resource_names)
    return catrobat_resource_names


def _catrobat_formula_from(raw_formula, sprite, project):
    tokens = []
    user_variables = project.getUserVariables()
    if not isinstance(raw_formula, list):
        raw_formula = [raw_formula]
    for elem in raw_formula:
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


def _sound_length_variable_name_for(resource_name):
    return _SOUND_LENGTH_VARIABLE_NAME_FORMAT.format(resource_name)
