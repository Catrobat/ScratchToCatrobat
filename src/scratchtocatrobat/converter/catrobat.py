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
import itertools
import numbers
import java

from scratchtocatrobat.tools import common

import org.catrobat.catroid.common as catcommon
import org.catrobat.catroid.content as catbase
import org.catrobat.catroid.content.bricks as catbricks
import org.catrobat.catroid.formulaeditor as catformula

# FIXME: consider localization
_BACKGROUND_SPRITE_NAME = "Hintergrund"

ANDROID_IGNORE_MEDIA_MARKER_FILE_NAME = ".nomedia"
CATROBAT_LANGUAGE_VERSION = float("{0:.3f}".format(catcommon.Constants.CURRENT_CATROBAT_LANGUAGE_VERSION))
PACKAGED_PROGRAM_FILE_EXTENSION = catcommon.Constants.CATROBAT_EXTENSION
PROGRAM_SOURCE_FILE_NAME = catcommon.Constants.PROJECTCODE_NAME

_log = common.log

def simple_name_for(brick):
    if isinstance(brick, (list, tuple)):
        return map(simple_name_for, brick)

    simple_class_name = None

    if hasattr(brick, "getClass"):
        simple_class_name = brick.getClass().getName().split(".")[-1]
    elif not isinstance(brick, (str, unicode, numbers.Number)):
        simple_class_name = "%s:" % (type(brick))

    if isinstance(brick, catbricks.NoteBrick):
        #FIXME !! note-attribute removed from java class, now node is a formula!
        simple_class_name += ": 'S2CC-TODO: UNKNOWN_MESSAGE'"
#        simple_class_name += ": '%s'" % brick.note
    elif isinstance(brick, catformula.FormulaElement):
        simple_class_name += ": " + str(brick.getValue())
    elif isinstance(brick, catformula.Formula):
        simple_class_name += ": " + brick.formulaTree.getValue()
    elif simple_class_name is None:
        simple_class_name = unicode(brick)

    return simple_class_name


def create_lookdata(name, file_name):
    look_data = catcommon.LookData()
    look_data.setLookName(name)
    look_data.setLookFilename(file_name)
    return look_data


def set_as_background(sprite):
    sprite.setName(_BACKGROUND_SPRITE_NAME)
    assert is_background_sprite(sprite)


def is_background_sprite(sprite):
    return sprite.getName() == _BACKGROUND_SPRITE_NAME # and sprite.isBackgroundObject


def background_sprite_of(scene):
    if scene.getSpriteList().size() > 0:
        sprite = scene.getSpriteList().get(0)
        assert is_background_sprite(sprite)
    else:
        sprite = None
    return sprite


def _sprite_of(scene, sprite_name):
    sprite = None
    if sprite_name is None:
        sprite_name = _BACKGROUND_SPRITE_NAME
    for sprite_ in scene.getSpriteList():
        if sprite_.getName() == sprite_name:
            sprite = sprite_
            break
    return sprite

def find_global_or_sprite_user_list_by_name(scene, sprite, list_name):
    return scene.getDataContainer().getUserList(list_name, sprite)

def find_global_user_list_by_name(project, sprite, list_name):
    user_lists = project.getDefaultScene().getDataContainer().getProjectLists()
    for user_list in user_lists:
        if user_list.getName() == list_name:
            return user_list
    return None

def find_sprite_user_list_by_name(project, sprite, list_name):
    user_lists = project.getDefaultScene().getDataContainer().getSpriteListOfLists(sprite)
    for user_list in user_lists:
        if user_list.getName() == list_name:
            return user_list
    return None

def user_variable_of(project, variable_name, sprite_name=None):
    '''
    If `sprite_name` is None the project variables are checked.
    '''
    data_container = project.getDefaultScene().getDataContainer()
    if sprite_name is None:
        return data_container.findUserVariable(variable_name, data_container.projectVariables)
    else:
        sprite = _sprite_of(project.getDefaultScene(), sprite_name)
        return data_container.getUserVariable(variable_name, sprite)

def create_formula_with_value(variable_value):
    assert variable_value != None
    if type(variable_value) is int:
        java_variable_value = java.lang.Integer(variable_value)
    elif isinstance(variable_value, (float, long)):
        java_variable_value = java.lang.Double(variable_value)
    elif isinstance(variable_value, (str, unicode)):
        try:
            temp = common.int_or_float(variable_value)
            if temp is not None:
                variable_value = java.lang.Integer(temp) if isinstance(temp, int) else java.lang.Double(temp)
            java_variable_value = variable_value
        except:
            java_variable_value = variable_value
    else:
        assert isinstance(variable_value, catformula.FormulaElement)
        java_variable_value = variable_value
    return catformula.Formula(java_variable_value)

def create_formula_element_with_value(variable_value):
    return create_formula_with_value(variable_value).getRoot()

def add_user_variable(project, variable_name, sprite=None, sprite_name=None):
    ''' If `sprite_name` is set a sprite variable is added otherwise the variable is added to the project. '''
    _log.debug("adding variable '%s' to sprite '%s'", variable_name, sprite_name if sprite_name is not None else "<Stage>")
    user_variables = project.getDefaultScene().getDataContainer()
    if sprite_name is None:
        added_user_variable = user_variables.addProjectUserVariable(variable_name)
    else:
        added_user_variable = user_variables.addSpriteUserVariableToSprite(sprite, variable_name)
    assert added_user_variable is not None
    return added_user_variable


def defined_variable_names_in(project, sprite_name=None, sprite=None):
    scene = project.getDefaultScene()
    if sprite_name is None:
        user_variables = scene.getDataContainer().projectVariables
    else:
        if sprite is None:
            sprite = _sprite_of(scene, sprite_name)
        user_variables = scene.getDataContainer().getOrCreateVariableListForSprite(sprite)
    return [user_variable.getName() for user_variable in user_variables]


def media_objects_in(project):
    scene = project.getDefaultScene()
    for sprite in scene.getSpriteList():
        for media_object in itertools.chain(sprite.getLookDataList(), sprite.getSoundList()):
            yield media_object

def add_to_start_script(bricks, sprite, position=0):
    _log.debug("add to start script of '%s': %s", sprite.getName(), map(simple_name_for, bricks))
    if len(bricks) == 0: return # nothing to do

    def get_or_add_startscript(sprite):
        # HACK: accessing private member, enabled with Jython registry security settings
        for script in sprite.scriptList:
            if isinstance(script, catbase.StartScript):
                _log.debug("  found start script")
                return script
        else:
            _log.debug("  start script not found, creating one")
            start_script = catbase.StartScript()
            sprite.addScript(0, start_script)
            return start_script

    start_script = get_or_add_startscript(sprite)
    start_script.getBrickList().addAll(position, bricks)


# from org/catrobat/catroid/utils/UtilFile.java
# FIXME: use Java class directly
def encoded_project_name(project_name):
    if project_name in {".", ".."}:
        project_name = project_name.replace(".", "%2E")
    else:
        project_name = project_name.replace("%", "%25")
        project_name = project_name.replace("\"", "%22")
        project_name = project_name.replace("/", "%2F")
        project_name = project_name.replace(":", "%3A")
        project_name = project_name.replace("<", "%3C")
        project_name = project_name.replace(">", "%3E")
        project_name = project_name.replace("?", "%3F")
        project_name = project_name.replace("\\", "%5C")
        project_name = project_name.replace("|", "%7C")
        project_name = project_name.replace("*", "%2A")
    return project_name


# TODO: extend for all further, default cases
def formula_element_for(catrobat_enum, arguments=[]):
    # TODO: fetch from unary operators map
    unary_operators = [catformula.Operators.LOGICAL_NOT]
    package_name = catrobat_enum.getClass().__name__.lower()
    formula_element = None
    if package_name in {"functions", "operators", "sensors"}:
        # pad arguments
        arguments = (arguments + [None, None])[:2]

        element_type = catformula.FormulaElement.ElementType.valueOf(package_name[:-1].upper())
        enum_name = catrobat_enum.name()
        formula_parent = None

        # check if unary operator -> add formula to rightChild instead of leftChild (i.e. set leftChild to None)
        if element_type == catformula.FormulaElement.ElementType.OPERATOR and catrobat_enum in unary_operators:
            assert len(arguments) == 2 and arguments[0] != None and arguments[1] == None
            arguments[0], arguments[1] = arguments[1], arguments[0] # swap leftChild and rightChild

        formula_element = catformula.FormulaElement(element_type, enum_name, formula_parent, *arguments)  # @UndefinedVariable (valueOf)
        for formula_child in arguments:
            if formula_child is not None:
                formula_child.parent = formula_element
    return formula_element
