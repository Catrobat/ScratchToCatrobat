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

import unittest

from scratchtocatrobat.tools import common_testing
import scriptcodemodifier


class TestZeroifyEmptyValuesModifier(common_testing.BaseTestCase):

    def setUp(self):
        super(TestZeroifyEmptyValuesModifier, self).setUp()
        self._modifier = scriptcodemodifier.ZeroifyEmptyValuesModifier()

    def test_non_empty_params_as_math_operand_arguments(self):
        block_list = [["wait:elapsed:from:", ["+", 1, 0]]]
        expected_block_list = [["wait:elapsed:from:", ["+", 1, 0]]]
        modified_block_list = self._modifier.modify(block_list)
        assert modified_block_list == expected_block_list

    def test_no_empty_params_as_math_function_arguments(self):
        block_list = [["wait:elapsed:from:", ["randomFrom:to:", -100, 100]]]
        expected_block_list = [["wait:elapsed:from:", ["randomFrom:to:", -100, 100]]]
        modified_block_list = self._modifier.modify(block_list)
        assert modified_block_list == expected_block_list

    def test_empty_params_as_math_operand_arguments(self):
        block_list = ["wait:elapsed:from:", ["+", "", ["randomFrom:to:", -100, 100]]]
        expected_block_list = ["wait:elapsed:from:", ["+", 0, ["randomFrom:to:", -100, 100]]]
        modified_block_list = self._modifier.modify(block_list)
        assert modified_block_list == expected_block_list

    def test_empty_params_as_math_function_arguments(self):
        block_list = [["wait:elapsed:from:", ["+", 0, ["randomFrom:to:", " ", 100]]]]
        expected_block_list = [["wait:elapsed:from:", ["+", 0, ["randomFrom:to:", 0, 100]]]]
        modified_block_list = self._modifier.modify(block_list)
        assert modified_block_list == expected_block_list


class TestInjectMissingBracketsModifier(common_testing.BaseTestCase):

    def setUp(self):
        super(TestInjectMissingBracketsModifier, self).setUp()
        self._modifier = scriptcodemodifier.InjectMissingBracketsModifier()

    def test_should_not_inject_any_brackets_when_multiplication_occurs_within_addition_in_formula(self):
        block_list = [["wait:elapsed:from:", ["+", 1, ["*", 2, 3]]]]
        expected_block_list = [["wait:elapsed:from:", ["+", 1, ["*", 2, 3]]]]
        modified_block_list = self._modifier.modify(block_list)
        assert modified_block_list == expected_block_list

    def test_should_not_inject_any_brackets_when_division_occurs_within_subtraction_in_formula(self):
        block_list = [["wait:elapsed:from:", ["-", 1, ["/", 2, 3]]]]
        expected_block_list = [["wait:elapsed:from:", ["-", 1, ["/", 2, 3]]]]
        modified_block_list = self._modifier.modify(block_list)
        assert modified_block_list == expected_block_list

    def test_should_inject_brackets_when_addition_occurs_within_multiplication_in_formula(self):
        block_list = [["wait:elapsed:from:", ["*", 1, ["+", 2, 3]]]]
        expected_block_list = [["wait:elapsed:from:", ["*", 1, ["()", ["+", 2, 3]]]]]
        modified_block_list = self._modifier.modify(block_list)
        assert modified_block_list == expected_block_list

    def test_should_not_inject_any_brackets_when_function_occurs_within_multiplication_in_formula(self):
        block_list = [["wait:elapsed:from:", ["*", 1, ["randomFrom:to:", 2, 3]]]]
        expected_block_list = [["wait:elapsed:from:", ["*", 1, ["randomFrom:to:", 2, 3]]]]
        modified_block_list = self._modifier.modify(block_list)
        assert modified_block_list == expected_block_list

    def test_should_not_inject_any_brackets_when_addition_with_brackets_occurs_within_multiplication_in_formula(self):
        block_list = [["wait:elapsed:from:", ["*", 1, ["()", ["+", 2, 3]]]]]
        expected_block_list = [["wait:elapsed:from:", ["*", 1, ["()", ["+", 2, 3]]]]]
        modified_block_list = self._modifier.modify(block_list)
        assert modified_block_list == expected_block_list

    def test_should_inject_brackets_when_addition_occurs_within_multiplication_within_multiplication_in_formula(self):
        block_list = [["wait:elapsed:from:", ["*", 1, ["*", 1, ["+", 2, 3]]]]]
        expected_block_list = [["wait:elapsed:from:", ["*", 1, ["*", 1, ["()", ["+", 2, 3]]]]]]
        modified_block_list = self._modifier.modify(block_list)
        assert modified_block_list == expected_block_list

    def test_should_inject_brackets_when_function_occurs_within_addition_occurs_within_multiplication_within_multiplication_in_formula(self):
        block_list = [["wait:elapsed:from:", ["*", 1, ["*", 1, ["+", ["sin", 2], 3]]]]]
        expected_block_list = [["wait:elapsed:from:", ["*", 1, ["*", 1, ["()", ["+", ["sin", 2], 3]]]]]]
        modified_block_list = self._modifier.modify(block_list)
        assert modified_block_list == expected_block_list


if __name__ == "__main__":
    unittest.main()
