from scratchtocatrobat.scratch.scratch3 import Scratch3Block
from scratchtocatrobat.tools import logger
log = logger.log


def unpack_block_list(blocklist):
    if isinstance(blocklist[0], list) and len(blocklist) == 1:
        blocklist = blocklist[0]
    return blocklist

def visitBlock(blockcontext):
    if not isinstance(blockcontext, BlockContext):
        return blockcontext
    blocklist = []
    while blockcontext.block != None:
        blockhandler = blockcontext.getBlockHandler()
        converted_block = blockhandler(blockcontext)
        blocklist.append(converted_block)
        blockcontext.nextBlock()
    blocklist = unpack_block_list(blocklist)
    return blocklist

def visitScriptBlock(blockcontext):
    if not isinstance(blockcontext, BlockContext):
        return blockcontext

    log.info("[Scratch3]  Converting Script: {}".format(blockcontext.block.opcode))
    scriptblock_handler = blockcontext.getBlockHandler()
    scriptblock = scriptblock_handler(blockcontext)
    blockcontext.nextBlock()

    blocklist = []
    blocklist.append(scriptblock)
    while blockcontext.block != None:
        block_handler = blockcontext.getBlockHandler()
        converted_block = block_handler(blockcontext)
        blocklist.append(converted_block)
        blockcontext.nextBlock()
    return blocklist

def visitLiteral(literal):
    if literal is None:
        return None #TODO: Warning or error message maybe?
    elif literal[0] == 12:
        return ["readVariable", literal[1]]
    elif literal[0] == 13:
        return ["contentsOfList:", literal[1]]
    elif literal[0] == 5 or literal[0] == 6 or literal[0] == 7:
        if literal[1] is None:
            return 0
        try:
            return int(literal[1])
        except:
            return str(literal[1])
    elif literal[0] == 4 or literal[0] == 8:
        if literal[1] == '':
            return 0.0
        return float(literal[1])
    elif literal[0] == 9:
        return literal[1]
    else:
        return literal[1]


def isShadowBlock(block, attributename):
    return block.inputs[attributename][0] == 1

def visitGeneric(blockcontext, attributename):
    block = blockcontext.block
    if not attributename in block.inputs:
        log.warn("[Scratch3] Failed to convert attribute: {} of block {} (type {}). Input is: {}".format(attributename, block.name, block.opcode, block.inputs.get(attributename)))
        return [False]

    block_id = blockcontext.getInput(attributename)[1]
    subblock = blockcontext.get_block(block_id)
    if not isinstance(subblock, Scratch3Block):
        return visitLiteral(block_id)

    subblockcontext = BlockContext(subblock, blockcontext.spriteblocks)
    blocklist = visitBlock(subblockcontext)
    if isShadowBlock(block, attributename):
        return blocklist[0]
    return blocklist


def visitDefault(blockcontext):
    log.warn("block not yet implemented: " + blockcontext.block.opcode)
    return ["say:", "ERROR: BLOCK NOT FOUND: " + blockcontext.block.opcode]

def visitCondition(blockcontext):
    block = blockcontext.block
    if not "CONDITION" in block.inputs:
        log.warn("[Scratch3] Possibly empty condition in block {} ({})".format(blockcontext.block.name, blockcontext.block.opcode))
        #if there is no condition block, it evaluates to true in scratch
        return ['=', 0, 0]

    block_id = blockcontext.getInput("CONDITION")[1]
    conditionblock = blockcontext.get_block(block_id)
    if not isinstance(conditionblock, Scratch3Block):
        log.warn("[Scratch3] Possibly empty condition in block {} ({})".format(blockcontext.block.name, blockcontext.block.opcode))
        return False
    condition = visitGeneric(blockcontext, "CONDITION")
    return condition


def visitBlockList(blockcontext):
    if not isinstance(blockcontext, BlockContext):
        return blockcontext
    blocklist = []

    while blockcontext.block != None:
        block_handler = blockcontext.getBlockHandler()
        converted_block = block_handler(blockcontext)
        blocklist.append(converted_block)
        blockcontext.nextBlock()
    return blocklist

def visitSubstack(blockcontext, substackkey):
    if not substackkey in blockcontext.block.inputs:
        log.warn("[Scratch3] Possibly empty if or else clause in block {} ({})".format(blockcontext.block.name, blockcontext.block.opcode))
        return None
    block_id = blockcontext.getInput(substackkey)[1]
    substackstartblock = blockcontext.get_block(block_id)
    if not isinstance(substackstartblock, Scratch3Block):
        return None
    substack_context = BlockContext(substackstartblock, blockcontext.spriteblocks)
    substack = visitBlockList(substack_context)
    return substack


def visitMutation(blockcontext):
    return blockcontext.block.mutation["proccode"]

def visitParams(blockcontext):
    paramids = blockcontext.block.mutation["argumentids"].strip("[]").split(",")
    sanitized = []
    for paramid in paramids:
        sanitized.append(paramid.strip("\""))
    arguments = []

    for paramid in sanitized:
        if paramid == "":
            continue
        arg = visitGeneric(blockcontext, paramid)
        arguments.append(arg)
    return arguments

def sanitizeListArgument(listString):
    paramids = listString.strip("[]").split(",")
    sanitized = []
    for paramid in paramids:
        paramid = paramid.strip("\"")
        if paramid == '':
            continue
        sanitized.append(paramid)
    return sanitized

def sanitizeListDefault(listString):
    paramids = listString.strip("[]").split(",")
    sanitized = []
    for paramid in paramids:
        paramid = paramid.strip("\"")
        if paramid == 'true': paramid = True
        if paramid == 'false': paramid = False
        if paramid == 'todo': paramid = None #TODO: this is most likely only a temporary placeholder
        sanitized.append(paramid)
    return sanitized




class BlockContext(object):
    def __init__(self, block, spriteblocks):
        self.block = block
        self.spriteblocks = spriteblocks

    def nextBlock(self):
        self.block = self.block.nextBlock

    def getOpcode(self):
        if isinstance(self.block, Scratch3Block):
            return self.block.opcode
        return None

    def getBlockHandler(self):
        from blockmapping import visitormap
        return visitormap.get(self.getOpcode(), visitDefault)

    def getInput(self, input_key):
        if not isinstance(self.block, Scratch3Block):
            return None
        value = self.block.inputs.get(input_key)
        return value

    def get_block(self, block_id):
        if not isinstance(block_id, basestring):
            return block_id

        block = self.spriteblocks.get(block_id)
        if block is None:
            return block_id
        return block

