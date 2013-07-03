import unittest
from scratchtobat import common_testing
import org.catrobat.catroid.formulaeditor as catformula


class TestCatrobatFunc(unittest.TestCase):

    def test_can_compare_equal_formulas(self):
        self.assertTrue(common_testing.compare_formulas(catformula.Formula(0.1), catformula.Formula(0.1)))

    def test_can_compare_inequal_formulas(self):
        self.assertFalse(common_testing.compare_formulas(catformula.Formula(0.1), catformula.Formula(0.01)))
        
        
if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
