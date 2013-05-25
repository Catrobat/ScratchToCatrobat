import org.catrobat.catroid.formulaeditor as catformula


def compare_formulas(formula1, formula2):
    assert isinstance(formula1, catformula.Formula)
    assert isinstance(formula2, catformula.Formula)
   
    def _compare_formula_elements(elem1, elem2):
        if not elem1 and not elem2:
            return True
        else:
            return (elem1.type == elem2.type and elem1.value == elem2.value and _compare_formula_elements(elem1.leftChild, elem2.leftChild) and
                _compare_formula_elements(elem1.rightChild, elem2.rightChild))
    
    return _compare_formula_elements(formula1.formulaTree, formula2.formulaTree)


