#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2015 The Catrobat Team
#  (http://developer.catrobat.org/credits)
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
#  along with this program.  If not, see http://www.gnu.org/licenses/.
from __future__ import unicode_literals

import itertools
import numbers
import os
import shutil
import types
import zipfile
import re
import unicodedata
from codecs import open

import org.catrobat.catroid.common as catcommon
import org.catrobat.catroid.content as catbase
import org.catrobat.catroid.content.bricks as catbricks
import org.catrobat.catroid.formulaeditor as catformula
import org.catrobat.catroid.formulaeditor.FormulaElement.ElementType as catElementType
import org.catrobat.catroid.io as catio

from scratchtocatrobat import catrobat
from scratchtocatrobat import common
from scratchtocatrobat import scratch
from scratchtocatrobat.scratch import JsonKeys as scratchkeys
from scratchtocatrobat.tools import svgtopng
from scratchtocatrobat.tools import wavconverter
from scratchtocatrobat.tools import helpers
from __builtin__ import None

_DEFAULT_BRICK_CLASS = catbricks.WaitBrick
_DEFAULT_FORMULA_ELEMENT = catformula.FormulaElement(catElementType.NUMBER, str(00001), None)  # @UndefinedVariable (valueOf)

_GENERATED_VARIABLE_PREFIX = helpers.application_info("short_name") + ":"
_SOUND_LENGTH_VARIABLE_NAME_FORMAT = "length_of_{}_in_secs"

_SPEAK_BRICK_THINK_INTRO = "I am thinking. "

_SUPPORTED_IMAGE_EXTENSIONS_BY_CATROBAT = {".gif", ".jpg", ".jpeg", ".png"}
_SUPPORTED_SOUND_EXTENSIONS_BY_CATROBAT = {".mp3", ".wav"}

UNSUPPORTED_SCRATCH_BRICK_NOTE_MESSAGE_PREFIX = "Missing brick for Scratch identifier: "

log = common.log

class ConversionError(common.ScratchtobatError):
        pass

class UnmappedBlock(object):

    def __init__(self, sprite, *args):
        self.sprite = sprite
        self.block_and_args = _with_unmapped_blocks_replaced_as_default_formula_value(args)

    def __str__(self):
        return catrobat.simple_name_for(self.block_and_args)

    def to_placeholder_brick(self):
        return _placeholder_for_unmapped_bricks_to(*self.block_and_args)

def _with_unmapped_blocks_replaced_as_default_formula_value(arguments):
    return [_DEFAULT_FORMULA_ELEMENT if isinstance(argument, UnmappedBlock) else argument for argument in arguments]

def _placeholder_for_unmapped_bricks_to(*args):
    arguments = ", ".join(map(catrobat.simple_name_for, args))
    temp = _DEFAULT_BRICK_CLASS(500)
    return [temp, catbricks.NoteBrick(UNSUPPORTED_SCRATCH_BRICK_NOTE_MESSAGE_PREFIX + arguments)]

def _key_to_broadcast_message(key_name):
    return "key " + key_name + " pressed"

def _background_look_to_broadcast_message(look_name):
    return "start background scene: " + look_name

def _next_background_look_broadcast_message():
    return "set background to next look"

def _sec_to_msec(duration):
    return duration * 1000

# note: for Scratch blocks without mapping placeholder Catrobat bricks will be added
class _ScratchToCatrobat(object):

    compute_block_parameters_mapping = {
        # math functions
        "abs": catformula.Functions.ABS,
        "sqrt": catformula.Functions.SQRT,
        "sin": catformula.Functions.SIN,
        "cos": catformula.Functions.COS,
        "tan": catformula.Functions.TAN,
        "asin": catformula.Functions.ARCSIN,
        "acos": catformula.Functions.ARCCOS,
        "atan": catformula.Functions.ARCTAN,
        "e^": catformula.Functions.EXP,
        "ln": catformula.Functions.LN,
        "log": catformula.Functions.LOG,
        "rounded": catformula.Functions.ROUND,
        "randomFrom:to:": catformula.Functions.RAND,
        "%": catformula.Functions.MOD,

        #  TODO: replace "dummy" keyword by corresponding Catrobat function as soon as Catrobat supports this...
        "10 ^": "dummy",
        "floor": catformula.Functions.FLOOR,
        "ceiling": catformula.Functions.CEIL,

        # user list functions
        "getLine:ofList:": catformula.Functions.LIST_ITEM,
        "lineCountOfList:": catformula.Functions.NUMBER_OF_ITEMS,
        "list:contains:": catformula.Functions.CONTAINS,

        # string functions
        "stringLength:": catformula.Functions.LENGTH,
        "letter:of:": catformula.Functions.LETTER,
        "concatenate:with:": catformula.Functions.JOIN
    }

    unary_operators_mapping = {
        "not": catformula.Operators.LOGICAL_NOT,
    }

    operators_mapping = dict({
        "+": catformula.Operators.PLUS,
        "-": catformula.Operators.MINUS,
        "*": catformula.Operators.MULT,
        "/": catformula.Operators.DIVIDE,
        "<": catformula.Operators.SMALLER_THAN,
        "=": catformula.Operators.EQUAL,
        ">": catformula.Operators.GREATER_THAN,
        "&": catformula.Operators.LOGICAL_AND,
        "|": catformula.Operators.LOGICAL_OR,
    }.items() + unary_operators_mapping.items())

    complete_mapping = dict({
        #
        # Scripts
        #
        "whenGreenFlag": catbase.StartScript,
        "whenIReceive": lambda message: catbase.BroadcastScript(message.lower()), # lower case to prevent case-sensitivity issues in Catrobat...
        "whenKeyPressed": lambda key: catbase.BroadcastScript(_key_to_broadcast_message(key)),
        # TODO: "whenSensorGreaterThan"
        "whenSceneStarts": lambda look_name: catbase.BroadcastScript(_background_look_to_broadcast_message(look_name)),
        "whenClicked": catbase.WhenScript,

        #
        # Bricks
        #
        "broadcast:": lambda message: catbricks.BroadcastBrick(message.lower()), # lower case to prevent case-sensitivity issues in Catrobat...
        "doBroadcastAndWait": lambda message: catbricks.BroadcastWaitBrick(message.lower()), # lower case to prevent case-sensitivity issues in Catrobat...
        # TODO: creation method for FormulaElement object
        "wait:elapsed:from:": lambda duration: catbricks.WaitBrick(catformula.Formula(duration)),

        # conditionals
        "doForever": catbricks.ForeverBrick,
        # FIXME: dummy value
        "doIf": "dummy",  # [catbricks.IfLogicBeginBrick, catbricks.IfLogicEndBrick],
        "doIfElse": "dummy",  # [catbricks.IfLogicBeginBrick, catbricks.IfLogicElseBrick, catbricks.IfLogicEndBrick],
        "doRepeat": catbricks.RepeatBrick,
        "doUntil": "dummy",
        "doWaitUntil": "dummy",

        "turnRight:": catbricks.TurnRightBrick,
        "turnLeft:": catbricks.TurnLeftBrick,
        "heading:": catbricks.PointInDirectionBrick,
        "forward:": catbricks.MoveNStepsBrick,
        "pointTowards:": catbricks.PointToBrick,
        "gotoX:y:": catbricks.PlaceAtBrick,
        "glideSecs:toX:y:elapsed:from:": lambda duration, x_pos, y_pos: catbricks.GlideToBrick(x_pos, y_pos, _sec_to_msec(duration) if isinstance(duration, numbers.Number) else duration),
        "xpos:": catbricks.SetXBrick,
        "ypos:": catbricks.SetYBrick,
        "bounceOffEdge": catbricks.IfOnEdgeBounceBrick,
        "changeXposBy:": catbricks.ChangeXByNBrick,
        "changeYposBy:": catbricks.ChangeYByNBrick,

        # variables
        "setVar:to:": lambda *args: _create_variable_brick(*itertools.chain(args, [catbricks.SetVariableBrick])),
        "changeVar:by:": lambda *args: _create_variable_brick(*itertools.chain(args, [catbricks.ChangeVariableBrick])),
        "readVariable": lambda variable_name: _variable_for(variable_name),
        "showVariable:": catbricks.ShowTextBrick,
        "hideVariable:": catbricks.HideTextBrick,

        # formula lists
        "append:toList:": catbricks.AddItemToUserListBrick,
        "insert:at:ofList:": catbricks.InsertItemIntoUserListBrick,
        "deleteLine:ofList:": catbricks.DeleteItemOfUserListBrick,
        "setLine:ofList:to:": catbricks.ReplaceItemInUserListBrick,
        #"showList:": catbricks.*, # TODO: implement this as soon as Catrobat supports this...
        #"hideList:": catbricks.*, # TODO: implement this as soon as Catrobat supports this...

        # looks
        "lookLike:": catbricks.SetLookBrick,
        "nextCostume": catbricks.NextLookBrick,
        "startScene": catbricks.BroadcastBrick,
        "nextScene": catbricks.NextLookBrick,  # only allowed in scene object so same as nextLook

        # TODO: remove lambdas to increase readability
        "changeGraphicEffect:by:": lambda effect_type, value:
            catbricks.ChangeBrightnessByNBrick(value) if effect_type == 'brightness' else
            catbricks.ChangeTransparencyByNBrick(value) if effect_type == 'ghost' else
            _placeholder_for_unmapped_bricks_to("changeGraphicEffect:by:", effect_type, value),
        "setGraphicEffect:to:": lambda effect_type, value:
            catbricks.SetBrightnessBrick(value) if effect_type == 'brightness' else
            catbricks.SetTransparencyBrick(value) if effect_type == 'ghost' else
            _placeholder_for_unmapped_bricks_to("setGraphicEffect:to:", effect_type, value),
        "filterReset": catbricks.ClearGraphicEffectBrick,
        "changeSizeBy:": catbricks.ChangeSizeByNBrick,
        "setSizeTo:": catbricks.SetSizeToBrick,
        "show": catbricks.ShowBrick,
        "hide": catbricks.HideBrick,
        "comeToFront": catbricks.ComeToFrontBrick,
        "goBackByLayers:": catbricks.GoNStepsBackBrick,

        # sound
        "playSound:": catbricks.PlaySoundBrick,
        "doPlaySoundAndWait": catbricks.PlaySoundBrick,
        "stopAllSounds": catbricks.StopAllSoundsBrick,
        "changeVolumeBy:": catbricks.ChangeVolumeByNBrick,
        "setVolumeTo:": catbricks.SetVolumeToBrick,

        # sprite values
        "xpos": catformula.Sensors.OBJECT_X,
        "ypos": catformula.Sensors.OBJECT_Y,
        "heading": catformula.Sensors.OBJECT_ROTATION,
        "size": catformula.Sensors.OBJECT_SIZE,

        # sensors
        # WORKAROUND: using ROUND for Catrobat float => Scratch int
        "soundLevel": lambda *_args: catrobat.formula_element_for(catformula.Functions.ROUND, arguments=[catrobat.formula_element_for(catformula.Sensors.LOUDNESS)]),  # @UndefinedVariable
    }.items() + compute_block_parameters_mapping.items() + operators_mapping.items())

    @classmethod
    def catrobat_brick_class_for(cls, scratch_block_name):
        assert isinstance(scratch_block_name, (str, unicode))
        catrobat_brick = cls.complete_mapping.get(scratch_block_name)
        if isinstance(catrobat_brick, types.LambdaType):
            catrobat_brick.__name__ = scratch_block_name + "-lambda"
        return catrobat_brick

    @classmethod
    def create_script(cls, scratch_script_name, sprite, arguments):
        assert sprite is not None
        if scratch_script_name not in scratch.SCRIPTS:
            assert False, "Missing script mapping for: " + scratch_script_name
        # TODO: separate script and brick mapping
        return cls.catrobat_brick_class_for(scratch_script_name)(*arguments)

def _create_variable_brick(value, user_variable, Class):
    assert Class in set([catbricks.SetVariableBrick, catbricks.ChangeVariableBrick])
    assert isinstance(user_variable, catformula.UserVariable)
    return Class(catrobat.create_formula_with_value(value), user_variable)

def _variable_for(variable_name):
    return catformula.FormulaElement(catElementType.USER_VARIABLE, variable_name, None)  # @UndefinedVariable

def _catrobat_resource_file_name_for(scratch_md5_name, scratch_resource_name):
    assert os.path.basename(scratch_md5_name) == scratch_md5_name and len(os.path.splitext(scratch_md5_name)[0]) == 32, "Must be MD5 hash with file ext: " + scratch_md5_name
    # remove unsupported unicode characters from filename
#     if isinstance(scratch_resource_name, unicode):
#         scratch_resource_name = unicodedata.normalize('NFKD', scratch_resource_name).encode('ascii','ignore')
#         if (scratch_resource_name == None) or (len(scratch_resource_name) == 0):
#             scratch_resource_name = "unicode_replaced"
    resource_ext = os.path.splitext(scratch_md5_name)[1]
    return scratch_md5_name.replace(resource_ext, "_" + scratch_resource_name + resource_ext)

def resource_name_for(file_path):
    return common.md5_hash(file_path) + os.path.splitext(file_path)[1]

def copy_media_file(scratch_project, original_to_converted_catrobat_resource_file_name, scratch_md5_name, src_path, target_dir, is_converted_file=False):
    # for Catrobat separate file is needed for resources which are used multiple times but with different names
    for scratch_resource_name in scratch_project.find_all_resource_names_for(scratch_md5_name):
        catrobat_resource_file_name = _catrobat_resource_file_name_for(scratch_md5_name, scratch_resource_name)
        if is_converted_file:
            original_resource_file_name = catrobat_resource_file_name
            converted_scratch_md5_name = resource_name_for(src_path)
            catrobat_resource_file_name = _catrobat_resource_file_name_for(converted_scratch_md5_name, scratch_resource_name)
            original_to_converted_catrobat_resource_file_name[original_resource_file_name] = catrobat_resource_file_name
            assert catrobat_resource_file_name != original_resource_file_name # check if renamed!
        shutil.copyfile(src_path, os.path.join(target_dir, catrobat_resource_file_name))
    if is_converted_file:
        os.remove(src_path)

# TODO: refactor _key_* functions to be used just once
def _key_image_path_for(key):
    key_images_path = os.path.join(common.get_project_base_path(), 'resources', 'images', 'keys')
    for key_filename in os.listdir(key_images_path):
        basename, _ = os.path.splitext(key_filename)
        if basename.lower().endswith("_".join(key.split())):
            return os.path.join(key_images_path, key_filename)
    assert False, "Key '%s' not found in %s" % (key, os.listdir(key_images_path))


# TODO:  refactor _key_* functions to be used just once
def _key_filename_for(key):
    assert key is not None
    key_path = _key_image_path_for(key)
    # TODO: extract method, already used once
    return common.md5_hash(key_path) + "_" + _key_to_broadcast_message(key) + os.path.splitext(key_path)[1]


def generated_variable_name(variable_name):
    return _GENERATED_VARIABLE_PREFIX + variable_name


def _sound_length_variable_name_for(resource_name):
    return generated_variable_name(_SOUND_LENGTH_VARIABLE_NAME_FORMAT.format(resource_name))


def _is_generated(variable_name):
    return variable_name.startswith(_GENERATED_VARIABLE_PREFIX)


def converted(scratch_project, progress_bar=None):
    return Converter.converted_project_for(scratch_project, progress_bar)


class Converter(object):

    def __init__(self, scratch_project):
        self.scratch_project = scratch_project

    @classmethod
    def converted_project_for(cls, scratch_project, progress_bar=None):
        converter = Converter(scratch_project)
        catrobat_project = converter._converted_catrobat_program(progress_bar)
        assert catrobat.is_background_sprite(catrobat_project.getSpriteList().get(0))
        return ConvertedProject(catrobat_project, scratch_project)

    def _converted_catrobat_program(self, progress_bar=None):
        _catr_project = catbase.Project(None, self.scratch_project.name)
        self._scratch_object_converter = _ScratchObjectConverter(_catr_project, self.scratch_project, progress_bar)
        self._add_global_user_lists_to(_catr_project)
        self._add_converted_sprites_to(_catr_project)
        self._add_key_sprites_to(_catr_project, self.scratch_project.listened_keys)
        self._update_xml_header(_catr_project.getXmlHeader(), self.scratch_project.project_id, self.scratch_project.description)
        return _catr_project

    def _add_global_user_lists_to(self, catrobat_project):
        if self.scratch_project.global_user_lists is None:
            return

        for global_user_list in self.scratch_project.global_user_lists:
            # TODO: use "visible" as soon as show/hide-formula-list-bricks are available in Catrobat => global_formula_list["visible"]
            # TODO: use "isPersistent" as soon as Catrobat supports this => global_formula_list["isPersistent"]
            data_container = catrobat_project.getDataContainer()
            data_container.addProjectUserList(global_user_list["listName"])

    def _add_converted_sprites_to(self, catrobat_project):
        for scratch_object in self.scratch_project.objects:
            catr_sprite = self._scratch_object_converter(scratch_object)
            catrobat_project.addSprite(catr_sprite)

    # TODO: make it more explicit that this depends on the conversion code for "whenKeyPressed" Scratch block
    @staticmethod
    def _add_key_sprites_to(catrobat_project, listened_keys):
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
            when_started_script = catbase.StartScript()
            set_look_brick = catbricks.SetLookBrick()
            set_look_brick.setLook(key_look)

            # special handling wider button
            if key == "space":
                width_pos = 0
                height_pos = 2
            y_pos = (scratch.STAGE_HEIGHT_IN_PIXELS / 2) - 40 * height_pos
            x_pos = -(scratch.STAGE_WIDTH_IN_PIXELS / 2) + 40 * (width_pos + 1)
            place_at_brick = catbricks.PlaceAtBrick(x_pos, y_pos)

            bricks = [place_at_brick, set_look_brick, catbricks.SetSizeToBrick(33)]
            when_started_script.getBrickList().addAll(bricks)
            key_sprite.addScript(when_started_script)

            when_tapped_script = catbase.WhenScript()
            when_tapped_script.addBrick(catbricks.BroadcastBrick(key_message))
            key_sprite.addScript(when_tapped_script)

            catrobat_project.addSprite(key_sprite)

    @staticmethod
    def _update_xml_header(xml_header, scratch_project_id, scratch_project_description):
        xml_header.virtualScreenHeight = scratch.STAGE_HEIGHT_IN_PIXELS
        xml_header.virtualScreenWidth = scratch.STAGE_WIDTH_IN_PIXELS
        xml_header.setApplicationBuildName(helpers.application_info("build_name"))
        nums = re.findall(r'\d+', helpers.application_info("build_number"))
        build_number = int(nums[0]) if len(nums) > 0 else 0
        xml_header.setApplicationBuildNumber(build_number)
        xml_header.setApplicationName(helpers.application_info("name"))
        xml_header.setApplicationVersion(helpers.application_info("version"))
        xml_header.setCatrobatLanguageVersion(catrobat.CATROBAT_LANGUAGE_VERSION)
        xml_header.setDeviceName(helpers.scratch_info("device_name"))
        xml_header.setPlatform(helpers.scratch_info("platform"))
        xml_header.setPlatformVersion(float(helpers.scratch_info("platform_version")))
        xml_header.setScreenMode(catcommon.ScreenModes.STRETCH)
        xml_header.mediaLicense = helpers.catrobat_info("media_license_url")
        xml_header.programLicense = helpers.catrobat_info("program_license_url")
        assert scratch_project_id is not None
        xml_header.remixOf = helpers.config.get("SCRATCH_API", "project_base_url") + scratch_project_id
        description = scratch_project_description if scratch_project_description is not None else ""
        description = "\n" + description + "\n" if len(description) > 0 else ""
        description += "\nMade with {} version {}.\nOriginal Scratch project => {}".format( \
                         helpers.application_info("name"), \
                         helpers.application_info("version"), \
                         xml_header.remixOf)
        xml_header.setDescription(description)

class _ScratchObjectConverter(object):
    _catrobat_project = None
    _scratch_project = None

    def __init__(self, catrobat_project, scratch_project, progress_bar=None):
        _ScratchObjectConverter._catrobat_project = catrobat_project
        _ScratchObjectConverter._scratch_project = scratch_project
        self._progress_bar = progress_bar

    def __call__(self, scratch_object):
        return self._catrobat_sprite_from(scratch_object)

    def _catrobat_sprite_from(self, scratch_object):
        if not isinstance(scratch_object, scratch.Object):
            raise common.ScratchtobatError("Input must be of type={}, but is={}".format(scratch.Object, type(scratch_object)))
        sprite = catbase.Sprite(scratch_object.get_objName())
        log.debug("sprite name: %s", sprite.getName())

        if scratch_object.is_stage():
            catrobat.set_as_background(sprite)

        # looks and sounds has to added first because of cross-validations
        sprite_looks = sprite.getLookDataList()
        costume_resolution = None
        for scratch_costume in scratch_object.get_costumes():
            current_costume_resolution = scratch_costume.get(scratchkeys.COSTUME_RESOLUTION)
            if not costume_resolution:
                costume_resolution = current_costume_resolution
            elif current_costume_resolution != costume_resolution:
                    log.warning("Costume resolution not same for all costumes")
            sprite_looks.add(self._catrobat_look_from(scratch_costume))

        sprite_sounds = sprite.getSoundList()
        for scratch_sound in scratch_object.get_sounds():
            sprite_sounds.add(self._catrobat_sound_from(scratch_sound))

        if not scratch_object.is_stage() and scratch_object.get_lists() is not None:
            catr_data_container = self._catrobat_project.getDataContainer()
            for user_list_data in scratch_object.get_lists():
                assert len(user_list_data["listName"]) > 0
                catr_data_container.addSpriteUserListToSprite(sprite, user_list_data["listName"])

        for scratch_variable in scratch_object.get_variables():
            sprite_name = sprite.getName() if not scratch_object.is_stage() else None
            user_variable = catrobat.add_user_variable(self._catrobat_project, scratch_variable["name"], sprite=sprite, sprite_name=sprite_name)
            assert user_variable is not None
            user_variable = self._catrobat_project.getDataContainer().getUserVariable(scratch_variable["name"], sprite)
            assert user_variable is not None

        for scratch_script in scratch_object.scripts:
            sprite.addScript(self._catrobat_script_from(scratch_script, sprite))
            if self._progress_bar != None: self._progress_bar.update()

        self._add_default_behaviour_to(sprite, self._catrobat_project, scratch_object, self._scratch_project, costume_resolution)

        for scratch_variable in scratch_object.get_variables():
            args = [self._catrobat_project, scratch_variable["name"], scratch_variable["value"], sprite]
            if not scratch_object.is_stage():
                args += [sprite.getName()]
            _assign_initialization_value_to_user_variable(*args)
        return sprite

    @staticmethod
    def _catrobat_look_from(scratch_costume):
        if not scratch_costume or not (isinstance(scratch_costume, dict) and all(_ in scratch_costume for _ in (scratchkeys.COSTUME_MD5, scratchkeys.COSTUME_NAME))):
            raise common.ScratchtobatError("Wrong input, must be costume dict: {}".format(scratch_costume))
        look = catcommon.LookData()

        assert scratchkeys.COSTUME_NAME in scratch_costume
        costume_name = scratch_costume[scratchkeys.COSTUME_NAME]
        look.setLookName(costume_name)

        assert scratchkeys.COSTUME_MD5 in scratch_costume
        costume_md5_filename = scratch_costume[scratchkeys.COSTUME_MD5]
        costume_resource_name = scratch_costume[scratchkeys.COSTUME_NAME]
        look.setLookFilename(_catrobat_resource_file_name_for(costume_md5_filename, costume_resource_name))
        return look

    @staticmethod
    def _catrobat_sound_from(scratch_sound):
        soundinfo = catcommon.SoundInfo()

        assert scratchkeys.SOUND_NAME in scratch_sound
        sound_name = scratch_sound[scratchkeys.SOUND_NAME]
        soundinfo.setTitle(sound_name)

        assert scratchkeys.SOUND_MD5 in scratch_sound
        sound_md5_filename = scratch_sound[scratchkeys.SOUND_MD5]
        sound_resource_name = scratch_sound[scratchkeys.SOUND_NAME]
        soundinfo.setSoundFileName(_catrobat_resource_file_name_for(sound_md5_filename, sound_resource_name))
        return soundinfo

    @staticmethod
    def _add_default_behaviour_to(sprite, catrobat_project, scratch_object, scratch_project, costume_resolution):
        # some initial Scratch settings are done with a general JSON configuration instead with blocks. Here the equivalent bricks are added for Catrobat.
        implicit_bricks_to_add = []

        # create AddItemToUserListBrick bricks to populate user lists with their default values
        # global lists will be populated in StartScript of background/stage sprite object
        if scratch_object.is_stage() and scratch_object.get_lists() is not None:
            for global_user_list_data in scratch_project.global_user_lists:
                list_name = global_user_list_data["listName"]
                assert len(list_name) > 0
                catr_user_list = catrobat.find_global_user_list_by_name(catrobat_project, sprite, list_name)
                if "contents" not in global_user_list_data:
                    continue
                for value in global_user_list_data["contents"]:
                    catr_value_formula = catrobat.create_formula_with_value(value)
                    implicit_bricks_to_add += [catbricks.AddItemToUserListBrick(catr_value_formula, catr_user_list)]

        if not scratch_object.is_stage() and scratch_object.get_lists() is not None:
            for user_list_data in scratch_object.get_lists():
                list_name = user_list_data["listName"]
                assert len(list_name) > 0
                catr_user_list = catrobat.find_sprite_user_list_by_name(catrobat_project, sprite, list_name)
                assert catr_user_list
                if "contents" not in user_list_data:
                    continue
                for value in user_list_data["contents"]:
                    catr_value_formula = catrobat.create_formula_with_value(value)
                    implicit_bricks_to_add += [catbricks.AddItemToUserListBrick(catr_value_formula, catr_user_list)]

        # object's currentCostumeIndex determines active costume at startup
        sprite_startup_look_idx = scratch_object.get_currentCostumeIndex()
        if sprite_startup_look_idx is not None:
            if isinstance(sprite_startup_look_idx, float):
                sprite_startup_look_idx = int(round(sprite_startup_look_idx))
            spriteStartupLook = sprite.getLookDataList()[sprite_startup_look_idx]
            set_look_brick = catbricks.SetLookBrick()
            set_look_brick.setLook(spriteStartupLook)
            implicit_bricks_to_add += [set_look_brick]

        # object's scratchX and scratchY Keys determine position
        x_pos = scratch_object.get_scratchX() or 0
        y_pos = scratch_object.get_scratchY() or 0
        place_at_brick = catbricks.PlaceAtBrick(int(x_pos), int(y_pos))
        implicit_bricks_to_add += [place_at_brick]

        object_scale = scratch_object.get_scale() or 1
        if costume_resolution is not None:
            implicit_bricks_to_add += [catbricks.SetSizeToBrick(object_scale * 100.0 / costume_resolution)]

        object_direction = scratch_object.get_direction() or 90
        implicit_bricks_to_add += [catbricks.PointInDirectionBrick(object_direction)]

        object_visible = scratch_object.get_visible()
        if object_visible is not None and not object_visible:
            implicit_bricks_to_add += [catbricks.HideBrick()]

        rotation_style = scratch_object.get_rotationStyle()
        if rotation_style and rotation_style != "normal":
            log.warning("Unsupported rotation style '{}' at object: {}".format(rotation_style, scratch_object.get_objName()))

        catrobat.add_to_start_script(implicit_bricks_to_add, sprite)

    @classmethod
    def _catrobat_script_from(cls, scratch_script, sprite):
        if not isinstance(scratch_script, scratch.Script):
            raise common.ScratchtobatError("Arg1 must be of type={}, but is={}".format(scratch.Script, type(scratch_script)))
        if sprite and not isinstance(sprite, catbase.Sprite):
            raise common.ScratchtobatError("Arg2 must be of type={}, but is={}".format(catbase.Sprite, type(sprite)))

        log.debug("  script type: %s, args: %s", scratch_script.type, scratch_script.arguments)
        try:
            cat_script = _ScratchToCatrobat.create_script(scratch_script.type, sprite, scratch_script.arguments)
        except:
            cat_script = catbase.StartScript()
            wait_and_note_brick = _placeholder_for_unmapped_bricks_to("UNSUPPORTED SCRIPT", scratch_script.type)
            for brick in wait_and_note_brick:
                cat_script.addBrick(brick)

        converted_bricks = cls._catrobat_bricks_from(scratch_script.script_element, sprite)
        assert isinstance(converted_bricks, list) and len(converted_bricks) == 1
        [converted_bricks] = converted_bricks
#         print(map(catrobat.simple_name_for, converted_bricks))
#         log.debug("   --> converted: <%s>", ", ".join(map(catrobat.simple_name_for, converted_bricks)))
        ignored_blocks = 0
        for brick in converted_bricks:
            # Scratch behavior: blocks can be ignored e.g. if no arguments are set
            if not brick:
                ignored_blocks += 1
                continue
            try:
                cat_script.addBrick(brick)
            except TypeError:
                if isinstance(brick, (str, unicode)):
                    log.error("string brick: %s", brick)
                else:
                    log.error("type: %s, value: %s", brick.type, brick.value)
                assert False
        if ignored_blocks > 0:
            log.info("number of ignored Scratch blocks: %d", ignored_blocks)
        return cat_script

    @classmethod
    def _catrobat_bricks_from(cls, scratch_blocks, catrobat_sprite):
        if not isinstance(scratch_blocks, scratch.ScriptElement):
            scratch_blocks = scratch.ScriptElement.from_raw_block(scratch_blocks)
        traverser = _BlocksConversionTraverser(catrobat_sprite, cls._catrobat_project)
        traverser.traverse(scratch_blocks)
        return traverser.converted_bricks


class ConvertedProject(object):

    def __init__(self, catrobat_project, scratch_project):
        self.scratch_project = scratch_project
        self.catrobat_program = catrobat_project
        self.name = self.catrobat_program.getXmlHeader().getProgramName()

    @staticmethod
    def _converted_output_path(output_dir, project_name):
        return os.path.join(output_dir, catrobat.encoded_project_name(project_name) + catrobat.PACKAGED_PROGRAM_FILE_EXTENSION)

    def save_as_catrobat_package_to(self, output_dir, archive_name=None, progress_bar=None):

        def iter_dir(path):
            for root, _, files in os.walk(path):
                for file_ in files:
                    yield os.path.join(root, file_)
        log.info("convert Scratch project to '%s'", output_dir)

        with common.TemporaryDirectory() as catrobat_program_dir:
            self.save_as_catrobat_directory_structure_to(catrobat_program_dir, progress_bar)
            common.makedirs(output_dir)
            archive_name = self.name if archive_name == None else archive_name
            catrobat_zip_file_path = self._converted_output_path(output_dir, archive_name)
            log.info("  save packaged Scratch project to '%s'", catrobat_zip_file_path)
            if os.path.exists(catrobat_zip_file_path):
                os.remove(catrobat_zip_file_path)
            with zipfile.ZipFile(catrobat_zip_file_path, 'w') as zip_fp:
                for file_path in iter_dir(unicode(catrobat_program_dir)):
                    assert isinstance(file_path, unicode)
                    path_inside_zip = file_path.replace(catrobat_program_dir, u"")
                    zip_fp.write(file_path, path_inside_zip)
            assert os.path.exists(catrobat_zip_file_path), "Catrobat package not written: %s" % catrobat_zip_file_path
        return catrobat_zip_file_path

    @staticmethod
    def _images_dir_of_project(temp_dir):
        return os.path.join(temp_dir, "images")

    @staticmethod
    def _sounds_dir_of_project(temp_dir):
        return os.path.join(temp_dir, "sounds")

    def save_as_catrobat_directory_structure_to(self, temp_path, progress_bar=None):
        def create_directory_structure():
            sounds_path = self._sounds_dir_of_project(temp_path)
            os.mkdir(sounds_path)

            images_path = self._images_dir_of_project(temp_path)
            os.mkdir(images_path)

            for _ in (temp_path, sounds_path, images_path):
                # TODO: into common module
                open(os.path.join(_, catrobat.ANDROID_IGNORE_MEDIA_MARKER_FILE_NAME), 'a').close()
            return sounds_path, images_path

        # TODO: refactor to a MediaConverter class
        def write_mediafiles(original_to_converted_catrobat_resource_file_name, progress_bar):
            all_resources = []
            class MediaType(object):
                IMAGE = 1
                AUDIO = 2
                UNCONVERTED_SVG = 3
                UNCONVERTED_WAV = 4

            for scratch_md5_name, src_path in self.scratch_project.md5_to_resource_path_map.iteritems():
                assert os.path.exists(src_path), "Not existing: {}. Available files in directory: {}".format(src_path, os.listdir(os.path.dirname(src_path)))
                if scratch_md5_name in self.scratch_project.unused_resource_names:
                    log.info("Ignoring unused resource file: %s", src_path)
                    if progress_bar != None: progress_bar.update()
                    continue

                file_ext = os.path.splitext(scratch_md5_name)[1].lower()
                resource_info = { "scratch_md5_name": scratch_md5_name, "src_path": src_path }
                if file_ext in {".png", ".svg", ".jpg", ".gif"}:
                    resource_info["dest_path"] = images_path
                    resource_info["status"] = MediaType.IMAGE
                    if file_ext == ".svg":
                        resource_info["status"] = MediaType.UNCONVERTED_SVG
                elif file_ext in {".wav", ".mp3"}:
                    resource_info["dest_path"] = sounds_path
                    resource_info["status"] = MediaType.AUDIO
                    if file_ext == ".wav" and not wavconverter.is_android_compatible_wav(src_path):
                        resource_info["status"] = MediaType.UNCONVERTED_WAV
                else:
                    assert file_ext in {".json"}, "Unknown media file extension: %s" % src_path
                    continue
                all_resources.append(resource_info)

            from threading import Thread
            class MediaResourceConverterThread(Thread):
                def run(self):
                    old_src_path = self._kwargs["info"]["src_path"]
                    status = self._kwargs["info"]["status"]
                    if status == MediaType.UNCONVERTED_SVG:
                        # converting svg to png -> new md5 and filename
                        new_src_path = svgtopng.convert(old_src_path)
                    elif status == MediaType.UNCONVERTED_WAV:
                        # converting Android-incompatible wav to compatible wav
                        new_src_path = old_src_path.replace(".wav", "_converted.wav")
                        wavconverter.convert_to_android_compatible_wav(old_src_path, new_src_path)
                    else:
                        assert False, "Unsupported Media Type! Cannot convert media file: %s" % old_src_path
                    self._kwargs["new_svg_src_paths"][old_src_path] = new_src_path
                    progress_bar = self._kwargs["progress_bar"]
                    if progress_bar != None: progress_bar.update()
                    assert os.path.exists(new_src_path), "Not existing: {}. Available files in directory: {}".format(new_src_path, os.listdir(os.path.dirname(new_src_path)))

            # schedule parallel conversions (one conversion per thread)
            unconverted_types = { MediaType.UNCONVERTED_SVG, MediaType.UNCONVERTED_WAV }
            unconverted_media_resources = [res for res in all_resources if res["status"] in unconverted_types]
            # update progress bar for all those media files that don't have to be converted
            if progress_bar != None: [progress_bar.update() for res in all_resources if res["status"] not in unconverted_types]
            new_svg_src_paths = {}
            max_concurrent_threads = int(helpers.config.get("MEDIA_CONVERTER", "max_concurrent_threads"))
            resource_index = 0
            num_total_resources = len(unconverted_media_resources)
            reference_index = 0
            while resource_index < num_total_resources:
                num_next_resources = min(max_concurrent_threads, (num_total_resources - resource_index))
                next_resources_end_index = resource_index + num_next_resources
                threads = []
                for index in range(resource_index, next_resources_end_index):
                    assert index == reference_index
                    reference_index += 1
                    info = unconverted_media_resources[index]
                    kwargs = { "info": info,
                               "new_svg_src_paths": new_svg_src_paths,
                               "progress_bar": progress_bar }
                    threads.append(MediaResourceConverterThread(kwargs=kwargs))
                for thread in threads:
                    thread.start()
                for thread in threads:
                    thread.join()
                resource_index = next_resources_end_index
            assert reference_index == resource_index and reference_index == num_total_resources

            for resource_info in all_resources:
                scratch_md5_name = resource_info["scratch_md5_name"]
                src_path = resource_info["src_path"]
                src_path = new_svg_src_paths[src_path] if src_path in new_svg_src_paths else src_path # check if path changed after conversion
                dest_path = resource_info["dest_path"]
                is_converted_file = resource_info["status"] in unconverted_types
                copy_media_file(self.scratch_project, original_to_converted_catrobat_resource_file_name, scratch_md5_name, src_path, dest_path, is_converted_file)

        def rename_resource_file_names_in(catrobat_program, rename_map):
            number_of_converted = 0
            for look_data_or_sound_info in catrobat.media_objects_in(catrobat_program):
                # HACK: by accessing private field don't have to care about type
                renamed_file_name = rename_map.get(look_data_or_sound_info.fileName)
                if renamed_file_name is not None:
                    look_data_or_sound_info.fileName = renamed_file_name
                    number_of_converted += 1
            assert number_of_converted >= len(rename_map)

        def program_source_for(catrobat_program):
            storage_handler = catio.StorageHandler()
            code_xml_content = storage_handler.XML_HEADER
            code_xml_content += storage_handler.getXMLStringOfAProject(catrobat_program)
            return code_xml_content

        def write_program_source(catrobat_program):
            # TODO: extract method
            # note: at this position because of use of sounds_path variable
            # TODO: make it more explicit that the "doPlayAndWait" brick workaround depends on the following code block
            for catrobat_sprite in catrobat_program.getSpriteList():
                for sound_info in catrobat_sprite.getSoundList():
                    sound_length_variable_name = _sound_length_variable_name_for(sound_info.getTitle())
                    sound_length = common.length_of_audio_file_in_secs(os.path.join(sounds_path, sound_info.getSoundFileName()))
                    sound_length = round(sound_length, 3) # accuracy +/- 0.5 milliseconds => review if we really need this...
                    _add_new_user_variable_with_initialization_value(catrobat_program, sound_length_variable_name, sound_length, catrobat_sprite, catrobat_sprite.getName())

            program_source = program_source_for(catrobat_program)
            with open(os.path.join(temp_path, catrobat.PROGRAM_SOURCE_FILE_NAME), "wb") as fp:
                fp.write(program_source.encode("utf8"))

            # copying key images needed for keyPressed substitution
            for listened_key in self.scratch_project.listened_keys:
                key_image_path = _key_image_path_for(listened_key)
                shutil.copyfile(key_image_path, os.path.join(images_path, _key_filename_for(listened_key)))

        # TODO: rename/rearrange abstracting methods
        log.info("  Creating Catrobat project structure")
        sounds_path, images_path = create_directory_structure()
        log.info("  Saving media files")
        original_to_converted_catrobat_resource_file_name = {}
        write_mediafiles(original_to_converted_catrobat_resource_file_name, progress_bar)
        rename_resource_file_names_in(self.catrobat_program, original_to_converted_catrobat_resource_file_name)
        log.info("  Saving project XML file")
        write_program_source(self.catrobat_program)
        if progress_bar != None: progress_bar.update(progress_bar.saving_xml_progress_weight)

# TODO: could be done with just user_variables instead of project object
def _add_new_user_variable_with_initialization_value(project, variable_name, variable_value, sprite, sprite_name=None):
    user_variable = catrobat.add_user_variable(project, variable_name, sprite=sprite, sprite_name=sprite_name)
    assert user_variable is not None
    variable_initialization_brick = _create_variable_brick(variable_value, user_variable, catbricks.SetVariableBrick)
    catrobat.add_to_start_script([variable_initialization_brick], sprite)

def _assign_initialization_value_to_user_variable(project, variable_name, variable_value, sprite, sprite_name=None):
    user_variable = project.getDataContainer().getUserVariable(variable_name, sprite)
    assert user_variable is not None and user_variable.getName() == variable_name, "variable: %s, sprite_name: %s" % (variable_name, sprite.getName())
    variable_initialization_brick = _create_variable_brick(variable_value, user_variable, catbricks.SetVariableBrick)
    catrobat.add_to_start_script([variable_initialization_brick], sprite)

# based on: http://stackoverflow.com/a/4274204
def _register_handler(dict_, *names):
    def dec(f):
        m_name = f.__name__
        for name in names:
            dict_[name] = m_name
        return f
    return dec


class _BlocksConversionTraverser(scratch.AbstractBlocksTraverser):

    _block_name_to_handler_map = {}

    def __init__(self, catrobat_sprite, catrobat_project):
        assert catrobat_sprite is not None
        assert catrobat_project is not None
        self.sprite = catrobat_sprite
        self.project = catrobat_project
        self._stack = []
        self._child_stack = []

    @property
    def stack(self):
        return self.converted_bricks

    @property
    def converted_bricks(self):
        return self._stack

    def traverse(self, script_element):
        self._stack += [script_element.name]
        super(_BlocksConversionTraverser, self).traverse(script_element)

    def _pop_stack(self, start_index):
        popped = list(self._stack[start_index:])
        del self._stack[start_index:]
        return popped

    def _visit(self, script_element):
        self.script_element = script_element
        arguments_start_index = len(self._stack) - self._stack[::-1].index(script_element.name)
        self.arguments = self._pop_stack(arguments_start_index)

        new_stack_values = self._converted_script_element()

        del self._stack[-1]
        if not isinstance(new_stack_values, list):
            new_stack_values = [new_stack_values]
        # TODO: simplify this...
        if len(self._child_stack) > 0 and len(new_stack_values) == len([val for val in new_stack_values if isinstance(val, catbricks.Brick)]):
            for brick_list in reversed(self._child_stack):
                self._stack += brick_list
            self._child_stack = []
        if len(new_stack_values) > 1 and isinstance(new_stack_values[-1], catformula.FormulaElement):
            # TODO: lambda check if all entries are instance of Brick
            self._child_stack += [new_stack_values[:-1]]
            new_stack_values = [new_stack_values[-1]]
        self._stack += new_stack_values

    def _converted_script_element(self):
        script_element = self.script_element
        if script_element.name == "computeFunction:of:":
            # removing block name which is common prefix for all function blocks:
            # [Block("computeFunction:of:"), BlockValue("tan"), ...] is changed to [Block("tan"), ...]
            assert len(self.arguments) >= 1
            self.script_element = scratch.Block(name=self.arguments[0])
            self.arguments = self.arguments[1:]
        self.block_name = block_name = self.script_element.name
        if isinstance(self.script_element, scratch.Block):
            log.debug("    block to convert: %s, arguments: %s", block_name, catrobat.simple_name_for(self.arguments))
            self.CatrobatClass = _ScratchToCatrobat.catrobat_brick_class_for(block_name)
            handler_method_name = self._block_name_to_handler_map.get(block_name)
            try:
                if handler_method_name is not None:
                    converted_element = getattr(self, handler_method_name)()
                else:
                    converted_element = self._regular_block_conversion()
            except Exception as e:
                log.warn("-" * 80)
                log.warn("Replacing {0} with NoteBrick".format(block_name))
                log.warn("Exception: {0}, ".format(e.message), exc_info=1)
                log.warn("-" * 80)
                converted_element = _placeholder_for_unmapped_bricks_to(block_name)
        elif isinstance(self.script_element, scratch.BlockValue):
            converted_element = [script_element.name]
        else:
            assert isinstance(self.script_element, scratch.BlockList)
            # TODO: readability
            converted_element = [[arg2 for arg1 in self.arguments for arg2 in (arg1.to_placeholder_brick() if isinstance(arg1, UnmappedBlock) else [arg1])]]
        return converted_element

    def _regular_block_conversion(self):
        CatrobatClass = self.CatrobatClass
        # TODO: replace with UnmappedBlock as a None object
        if CatrobatClass is not None:
            is_catrobat_enum = not hasattr(CatrobatClass, "__module__") and hasattr(CatrobatClass, "getClass")
            self.arguments = _with_unmapped_blocks_replaced_as_default_formula_value(self.arguments)
            for try_number in range(6):
                try:
                    # TODO: simplify
                    if try_number == 0:
                        converted_args = [common.int_or_float(arg) or arg if isinstance(arg, (str, unicode)) else arg for arg in self.arguments]
                    elif try_number == 1:
                        converted_args = [catformula.FormulaElement(catElementType.NUMBER, str(arg), None) if isinstance(arg, numbers.Number) else arg for arg in converted_args]  # @UndefinedVariable
                    elif try_number == 4:
                        converted_args = self.arguments
                    elif try_number == 2:
                        args = [arg if arg != None else "" for arg in self.arguments]
                        converted_args = [catformula.Formula(arg) for arg in args]
                    elif try_number == 3:
                        parameters = {
                            "brightness",
                            "color",  # unsupported
                            "ghost",
                        }
                        if len(self.arguments) == 2 and self.arguments[0] in parameters:
                            converted_args = [self.arguments[0]] + [catformula.Formula(arg) for arg in self.arguments[1:]]

                    if not is_catrobat_enum:
                        converted_value = CatrobatClass(*converted_args)
                    else:
                        converted_value = catrobat.formula_element_for(CatrobatClass, converted_args)
                    assert converted_value, "No result for {} with args {}".format(self.block_name, converted_args)
                    break
                except (TypeError) as e:
                    log.debug("instantiation try %d failed for class: %s, raw_args: %s, Catroid args: %s", try_number, CatrobatClass, self.arguments, map(catrobat.simple_name_for, converted_args))
                    class_exception = e
            else:
                log.error("General instantiation failed for class: %s, raw_args: %s, Catroid args: %s", CatrobatClass, self.arguments, map(catrobat.simple_name_for, converted_args))
                raise class_exception
                log.exception(class_exception)
                self.errors += [class_exception]
            new_stack_values = converted_value
        else:
            log.debug("no Class for: %s, args: %s", self.block_name, map(catrobat.simple_name_for, self.arguments))
            new_stack_values = UnmappedBlock(self.sprite, *([self.block_name] + self.arguments))
        return new_stack_values

    def _converted_helper_brick_or_formula_element(self, arguments, block_name):
        preserved_args = self.arguments
        self.arguments = arguments
        preserved_catrobat_class = self.CatrobatClass
        self.CatrobatClass = _ScratchToCatrobat.complete_mapping.get(block_name)
        handler_method_name = self._block_name_to_handler_map.get(block_name)
        if handler_method_name:
            converted_element = getattr(self, handler_method_name)()
        else:
            converted_element = self._regular_block_conversion()
        self.arguments = preserved_args
        self.CatrobatClass = preserved_catrobat_class
        return converted_element

    # formula element blocks (compute, operator, ...)
    @_register_handler(_block_name_to_handler_map, "10 ^")
    def _convert_pow_of_10_block(self):
        [value] = self.arguments

        # unfortunately 10^x and pow(x) functions are not yet available in Catroid
        # but Catroid already supports exp(x) and ln(x) functions
        # since 10^x == exp(x*ln(10)) we can use 3 math functions to achieve the correct result!

        # ln(10)
        ln_formula_elem = self._converted_helper_brick_or_formula_element([10], "ln")

        # x*ln(10)     (where x:=value)
        exponent_formula_elem = self._converted_helper_brick_or_formula_element([value, ln_formula_elem], "*")

        # exp(x*ln(10))
        result_formula_elem = self._converted_helper_brick_or_formula_element([exponent_formula_elem], "e^")

        # round(exp(x*ln(10)))     (use round to get rid of rounding errors)
        return self._converted_helper_brick_or_formula_element([result_formula_elem], "rounded")

    @_register_handler(_block_name_to_handler_map, "lineCountOfList:")
    def _convert_line_count_of_list_block(self):
        [list_name] = self.arguments
        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.project, self.sprite, list_name)
        assert user_list is not None
        left_formula_elem = catformula.FormulaElement(catElementType.USER_LIST, list_name, None)
        formula_element = catformula.FormulaElement(catElementType.FUNCTION, self.CatrobatClass.toString(), None)
        formula_element.setLeftChild(left_formula_elem)
        return formula_element

    @_register_handler(_block_name_to_handler_map, "list:contains:")
    def _convert_list_contains_block(self):
        [list_name, value] = self.arguments
        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.project, self.sprite, list_name)
        assert user_list is not None
        left_formula_elem = catformula.FormulaElement(catElementType.USER_LIST, list_name, None)
        formula_element = catformula.FormulaElement(catElementType.FUNCTION, self.CatrobatClass.toString(), None)
        formula_element.setLeftChild(left_formula_elem)
        formula_element.setRightChild(catrobat.create_formula_element_with_value(value))
        return formula_element

    @_register_handler(_block_name_to_handler_map, "getLine:ofList:")
    def _convert_get_line_of_list_block(self):
        [position, list_name] = self.arguments
        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.project, self.sprite, list_name)
        assert user_list is not None

        if position == "last":
            index_formula_element = self._converted_helper_brick_or_formula_element([list_name], "lineCountOfList:")
        elif position == "random":
            start_formula_element = catformula.FormulaElement(catElementType.NUMBER, "1", None) # first index of list
            end_formula_element = self._converted_helper_brick_or_formula_element([list_name], "lineCountOfList:")
            index_formula_element = self._converted_helper_brick_or_formula_element([start_formula_element, end_formula_element], "randomFrom:to:")
        else:
            index_formula_element = catrobat.create_formula_element_with_value(position)

        right_formula_elem = catformula.FormulaElement(catElementType.USER_LIST, list_name, None)
        formula_element = catformula.FormulaElement(catElementType.FUNCTION, self.CatrobatClass.toString(), None)
        formula_element.setLeftChild(index_formula_element)
        formula_element.setRightChild(right_formula_elem)
        return formula_element

    @_register_handler(_block_name_to_handler_map, "stringLength:")
    def _convert_string_length_block(self):
        [value] = self.arguments
        left_formula_elem = catrobat.create_formula_element_with_value(value)
        formula_element = catformula.FormulaElement(catElementType.FUNCTION, self.CatrobatClass.toString(), None)
        formula_element.setLeftChild(left_formula_elem)
        return formula_element

    @_register_handler(_block_name_to_handler_map, "letter:of:")
    def _convert_letter_of_block(self):
        [index, value] = self.arguments
        index_formula_elem = catrobat.create_formula_element_with_value(index)
        value_formula_elem = catrobat.create_formula_element_with_value(value)
        formula_element = catformula.FormulaElement(catElementType.FUNCTION, self.CatrobatClass.toString(), None)
        formula_element.setLeftChild(index_formula_elem)
        formula_element.setRightChild(value_formula_elem)
        return formula_element

    @_register_handler(_block_name_to_handler_map, "concatenate:with:")
    def _convert_concatenate_with_block(self):
        [value1, value2] = self.arguments
        formula_element = catformula.FormulaElement(catElementType.FUNCTION, self.CatrobatClass.toString(), None)
        value1_formula_elem = catrobat.create_formula_element_with_value(value1)
        formula_element.setLeftChild(value1_formula_elem)
        value2_formula_elem = catrobat.create_formula_element_with_value(value2)
        formula_element.setRightChild(value2_formula_elem)
        return formula_element

    # action and other blocks
    @_register_handler(_block_name_to_handler_map, "doRepeat", "doForever")
    def _convert_loop_blocks(self):
        brick_arguments = self.arguments
        self.block_name = self.block_name
        if self.block_name == 'doRepeat':
            times_value, nested_bricks = brick_arguments
            catr_loop_start_brick = self.CatrobatClass(catformula.Formula(times_value))
        else:
            assert self.block_name == 'doForever', self.block_name
            [nested_bricks] = brick_arguments
            catr_loop_start_brick = self.CatrobatClass()
        return [catr_loop_start_brick] + nested_bricks + [catbricks.LoopEndBrick(catr_loop_start_brick)]

    @_register_handler(_block_name_to_handler_map, "startScene")
    def _convert_scene_block(self):
        [look_name] = self.arguments
        # TODO: implement!
        #if look_name == "next backdrop": => use NextLookBrick
        #if look_name == "previous backdrop": => not sure...
        background_sprite = catrobat.background_sprite_of(self.project)
        if not background_sprite:
            assert catrobat.is_background_sprite(self.sprite)
            background_sprite = self.sprite
        matching_looks = [_ for _ in background_sprite.getLookDataList() if _.getLookName() == look_name]
        if not matching_looks:
            raise ConversionError("Background does not contain look with name: {}".format(look_name))
        assert len(matching_looks) == 1
        [matching_look] = matching_looks
        look_message = _background_look_to_broadcast_message(look_name)
        broadcast_brick = self.CatrobatClass(look_message)
        broadcast_script = catbase.BroadcastScript(look_message)
        set_look_brick = catbricks.SetLookBrick()
        set_look_brick.setLook(matching_look)
        broadcast_script.addBrick(set_look_brick)
        background_sprite.addScript(broadcast_script)
        return [broadcast_brick]

    @_register_handler(_block_name_to_handler_map, "doIf", "doIfElse")
    def _convert_if_block(self):
        # TODO: does not work for certain doIfs e.g. "./run.py https://scratch.mit.edu/projects/11806234/ --no-temp-rm"
#         print(self.arguments)
#         for arg in self.arguments:
#             print("  * {0}".format(type(arg)))
#         print("----------------------")
#         temp = catrobat.simple_name_for(self.arguments[0].block_and_args)
#         for test in temp:
#             print("-> There we go: " + test)
        assert 2 <= len(self.arguments) <= 3
        if_begin_brick = catbricks.IfLogicBeginBrick(catformula.Formula(self.arguments[0]))
        if_else_brick = catbricks.IfLogicElseBrick(if_begin_brick)
        if_end_brick = catbricks.IfLogicEndBrick(if_else_brick, if_begin_brick)
        if_bricks, [else_bricks] = self.arguments[1], self.arguments[2:] or [[]]
        if_bricks = if_bricks if if_bricks != None else []
        else_bricks = else_bricks if else_bricks != None else []
        return [if_begin_brick] + if_bricks + [if_else_brick] + else_bricks + [if_end_brick]

    @_register_handler(_block_name_to_handler_map, "lookLike:")
    def _convert_look_block(self):
        set_look_brick = self.CatrobatClass()
        [look_name] = self.arguments
        assert isinstance(look_name, (str, unicode)), type(look_name)
        look = next((look for look in self.sprite.getLookDataList() if look.getLookName() == look_name), None)
        if look is None:
            log.error("Look name: '%s' not found in sprite '%s'. Available looks: %s", look_name, self.sprite.getName(), ", ".join([look.getLookName() for look in self.sprite.getLookDataList()]))
            return []
        else:
            set_look_brick.setLook(look)
            return [set_look_brick]

    @_register_handler(_block_name_to_handler_map, "showVariable:")
    def _convert_show_variable_block(self):
        [variable_name] = self.arguments
        user_variable = self.project.getDataContainer().getUserVariable(variable_name, self.sprite)
        assert user_variable is not None # the variable must exist at this stage!
        assert user_variable.getName() == variable_name
        show_variable_brick = self.CatrobatClass(0, 0)
        show_variable_brick.userVariableName = variable_name
        show_variable_brick.userVariable = user_variable
        return show_variable_brick

    @_register_handler(_block_name_to_handler_map, "hideVariable:")
    def _convert_hide_variable_block(self):
        [variable_name] = self.arguments
        user_variable = self.project.getDataContainer().getUserVariable(variable_name, self.sprite)
        assert user_variable is not None # the variable must exist at this stage!
        assert user_variable.getName() == variable_name
        hide_variable_brick = self.CatrobatClass()
        hide_variable_brick.userVariableName = variable_name
        hide_variable_brick.userVariable = user_variable
        return hide_variable_brick

    @_register_handler(_block_name_to_handler_map, "append:toList:")
    def _convert_append_to_list_block(self):
        [value, list_name] = self.arguments
        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.project, self.sprite, list_name)
        assert user_list is not None
        value_formula = catrobat.create_formula_with_value(value)
        return self.CatrobatClass(value_formula, user_list)

    @_register_handler(_block_name_to_handler_map, "insert:at:ofList:")
    def _convert_insert_at_of_list_block(self):
        [value, position, list_name] = self.arguments
        if position == "last":
            index_formula = catformula.Formula(self._converted_helper_brick_or_formula_element([list_name], "lineCountOfList:"))
        elif position == "random":
            start_formula_element = catformula.FormulaElement(catElementType.NUMBER, "1", None) # first index of list
            end_formula_element = self._converted_helper_brick_or_formula_element([list_name], "lineCountOfList:")
            formula_element = self._converted_helper_brick_or_formula_element([start_formula_element, end_formula_element], "randomFrom:to:")
            index_formula = catformula.Formula(formula_element)
        else:
            index_formula = catrobat.create_formula_with_value(position)

        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.project, self.sprite, list_name)
        assert user_list is not None
        value_formula = catrobat.create_formula_with_value(value)
        assert index_formula is not None
        return self.CatrobatClass(value_formula, index_formula, user_list)

    @_register_handler(_block_name_to_handler_map, "deleteLine:ofList:")
    def _convert_delete_line_of_list_block(self):
        [position, list_name] = self.arguments
        index_formula = None
        prepend_bricks = []
        append_bricks = []
        if position in ["last", "all"]:
            index_formula = catformula.Formula(self._converted_helper_brick_or_formula_element([list_name], "lineCountOfList:"))

            if position == "all":
                # repeat loop workaround...
                catr_loop_start_brick = catbricks.RepeatBrick(index_formula)
                prepend_bricks += [catr_loop_start_brick]
                append_bricks += [catbricks.LoopEndBrick(catr_loop_start_brick)]
                index_formula = catrobat.create_formula_with_value("1") # first item to be deleted for n-times!
        else:
            index_formula = catrobat.create_formula_with_value(position)

        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.project, self.sprite, list_name)
        assert user_list is not None
        assert index_formula is not None
        return prepend_bricks + [self.CatrobatClass(index_formula, user_list)] + append_bricks

    @_register_handler(_block_name_to_handler_map, "setLine:ofList:to:")
    def _convert_set_line_of_list_to_block(self):
        [position, list_name, value] = self.arguments
        if position == "last":
            index_formula = catformula.Formula(self._converted_helper_brick_or_formula_element([list_name], "lineCountOfList:"))
        elif position == "random":
            start_formula_element = catformula.FormulaElement(catElementType.NUMBER, "1", None) # first index of list
            end_formula_element = self._converted_helper_brick_or_formula_element([list_name], "lineCountOfList:")
            index_formula_element = self._converted_helper_brick_or_formula_element([start_formula_element, end_formula_element], "randomFrom:to:")
            index_formula = catformula.Formula(index_formula_element)
        else:
            index_formula = catrobat.create_formula_with_value(position)

        user_list = catrobat.find_global_or_sprite_user_list_by_name(self.project, self.sprite, list_name)
        assert user_list is not None
        value_formula = catrobat.create_formula_with_value(value)
        assert index_formula is not None
        return self.CatrobatClass(value_formula, index_formula, user_list)

    @_register_handler(_block_name_to_handler_map, "showList:")
    def _convert_show_list_block(self):
        #["showList:", "myList"] # for testing purposes...
        #[list_name] = self.arguments
        assert "IMPLEMENT THIS AS SOON AS CATROBAT SUPPORTS THIS!!"

    @_register_handler(_block_name_to_handler_map, "hideList:")
    def _convert_hide_list_block(self):
        #["hideList:", "myList"] # for testing purposes...
        #[list_name] = self.arguments
        assert "IMPLEMENT THIS AS SOON AS CATROBAT SUPPORTS THIS!!"

    @_register_handler(_block_name_to_handler_map, "playSound:", "doPlaySoundAndWait")
    def _convert_sound_block(self):
        [sound_name] = self.arguments
        soundinfo_name_to_soundinfo_map = {sound_data.getTitle(): sound_data for sound_data in self.sprite.getSoundList()}
        sound_data = soundinfo_name_to_soundinfo_map.get(sound_name)
        if not sound_data:
            raise ConversionError("Sprite does not contain sound with name={}".format(sound_name))
        play_sound_brick = self.CatrobatClass()
        play_sound_brick.setSoundInfo(sound_data)
        converted_bricks = [play_sound_brick]
        if self.block_name == "doPlaySoundAndWait":
            sound_length_variable = _variable_for(_sound_length_variable_name_for(sound_name))
            converted_bricks += [catbricks.WaitBrick(catformula.Formula(sound_length_variable))]
        return converted_bricks

    @_register_handler(_block_name_to_handler_map, "changeVar:by:", "setVar:to:")
    def _convert_variable_block(self):
        [variable_name, value] = self.arguments
        user_variable = self.project.getDataContainer().getUserVariable(variable_name, self.sprite)
        if user_variable is None:
            # WORKAROUND: for generated variables added in preprocessing step (e.g doUntil rewrite)
            # must be generated user variable, otherwise the variable must have already been added at this stage!
            assert(_is_generated(variable_name))
            catrobat.add_user_variable(self.project, variable_name, self.sprite, self.sprite.getName())
            user_variable = self.project.getDataContainer().getUserVariable(variable_name, self.sprite)
            assert user_variable is not None and user_variable.getName() == variable_name, "variable: %s, sprite_name: %s" % (variable_name, self.sprite.getName())
        return [self.CatrobatClass(value, user_variable)]

    @_register_handler(_block_name_to_handler_map, "say:duration:elapsed:from:", "say:", "think:duration:elapsed:from:", "think:")
    def _convert_say_think_blocks(self):
        text, _args = self.arguments[0], self.arguments[1:]
        if self.block_name.startswith("think:"):
            text = _SPEAK_BRICK_THINK_INTRO + text
            # TODO: concatenate...
        value = catrobat.create_formula_with_value(text)
        # FIXME: value should depend on text length and optionally args
        return [catbricks.SpeakBrick(value), catbricks.WaitBrick(1000)]
