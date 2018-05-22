import unittest
from  scratchtocatrobat.scratch.scratch3visitor.looks import visitShow
from scratchtocatrobat.scratch.scratch3 import Scratch3Block
globcount = 0

TYPE_INT = 1
TYPE_STRING = 2
TYPE_BLOCK = 3
TYPE_VARIABLE = 4


def addInputToBlock(block, key, value, type=2, datatype=4):
    block.inputs[key] = [type, [datatype, value]]

def addInputOfType(block, key, type):

    if type == TYPE_INT:
        value = [1, [4, 1234]]
    elif type == TYPE_STRING:
        value = [1, [10, "teststring"]]
    elif type == TYPE_BLOCK:
        value = [2, [11, "blockid"]]
    else:
        return

    block.inputs[key] = value


def createScratch3Block(opcode):
    name = opcode + "_" + str(globcount)
    block = {}
    block['name'] = name

    global globcount
    globcount += 1

    block['opcode'] = opcode
    block['inputs'] = {}
    block['fields'] = {}
    block["parent"] = None
    block["next"] = None
    block = Scratch3Block(block, name)

    return block


def createDummyProject():

    pass

def createDummySprite():
    pass


class TestScratch3Blocks(unittest.TestCase):
    def setUp(self):
        pass
    def test_test(self):
        pass

    # def test_showSpriteBlock(self):
    #     testblock = createScratch3Block("show")
    #     addInputToBlock(testblock,"myval", 1)
    #     converted_block = visitShow(testblock, {})


if __name__ == "__main__":
    # import sys;sys.argv = ['', 'Test.testName']
    unittest.main()
