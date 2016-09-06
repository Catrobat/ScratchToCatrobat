#  ScratchToCatrobat: A tool for converting Scratch projects into Catrobat programs.
#  Copyright (C) 2013-2016 The Catrobat Team
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


class ScriptCodeModifier(object):
    def modify(self, script_code):
        return script_code


class ZeroifyEmptyValuesModifier(ScriptCodeModifier):
    def modify(self, script_code):
        return self._zeroify_empty_values(script_code)


    def _zeroify_empty_values(self, raw_block):
        from scratchtocatrobat.converter import converter
        if not isinstance(raw_block, list) or len(raw_block) == 0:
            return raw_block

        if isinstance(raw_block[0], list):
            return [self._zeroify_empty_values(sub_block) for sub_block in raw_block]

        # replace empty arguments/operands of math functions and math operators
        # (i.e. "" and " ") with 0. This is actually default behavior in Scratch.
        if converter.is_math_function_or_operator(raw_block[0]):
            assert len(raw_block) > 1
            raw_block[1:] = map(lambda arg: arg if not isinstance(arg, (str, unicode)) \
                                                or arg.strip() != '' else 0, raw_block[1:])

        return [raw_block[0]] + [self._zeroify_empty_values(arg) for arg in raw_block[1:]]


class InjectMissingBracketsModifier(ScriptCodeModifier):
    def modify(self, script_code):
        return self._inject_missing_brackets_to_formula_blocks(script_code, [])


    def _inject_missing_brackets_to_formula_blocks(self, raw_block, math_stack=[]):
        from scratchtocatrobat.converter import converter
        if not isinstance(raw_block, list) or len(raw_block) == 0:
            return raw_block

        if isinstance(raw_block[0], list):
            return [self._inject_missing_brackets_to_formula_blocks(sub_block, []) for sub_block in raw_block]

        should_add_brackets = False
        if converter.is_math_operator(raw_block[0]):
            assert len(raw_block) > 1
            current_operator = raw_block[0]
            if current_operator != "()":
                if len(math_stack) > 0:
                    previous_operator = math_stack[len(math_stack) - 1]
                    should_add_brackets = self._has_previous_operator_higher_priority(previous_operator, current_operator)
                    assert(not isinstance(current_operator, list))

                math_stack += [current_operator]
            else:
                math_stack = []

        result = [raw_block[0]] + [self._inject_missing_brackets_to_formula_blocks(arg, math_stack) for arg in raw_block[1:]]
        return ["()", result] if should_add_brackets else result


    def _has_previous_operator_higher_priority(self, previous_operator, curr_operator):
        if previous_operator == curr_operator:
            return False

        line_operators = ["+", "-"]
        punctuation_operators = ["*", "/"]
        logic_operators = ["|","&", "not"]
        comparison_operator = ["<", ">", "="]

        if previous_operator in punctuation_operators and curr_operator in line_operators:
            return True

        if previous_operator in line_operators and curr_operator in punctuation_operators:
            return False

        if (previous_operator == "%") or (previous_operator in comparison_operator) or (previous_operator in logic_operators):
            return True

        return previous_operator != curr_operator
