from visitorUtil import visitGeneric
from scratchtocatrobat.tools import logger

log = logger.log

def visitSayforsecs(blockcontext):
    message = visitGeneric(blockcontext, "MESSAGE")
    duration = visitGeneric(blockcontext, "SECS")
    return ["say:duration:elapsed:from:", message, duration]

def visitSay(blockcontext):
    message = visitGeneric(blockcontext, "MESSAGE")
    return ["say:", message]

def visitThinkforsecs(blockcontext):
    message = visitGeneric(blockcontext, "MESSAGE")
    duration = visitGeneric(blockcontext, "SECS")
    return ["think:duration:elapsed:from:", message, duration]

def visitThink(blockcontext):
    message = visitGeneric(blockcontext, "MESSAGE")
    return ["think:", message]

def visitSwitchcostumeto(blockcontext):
    costume = visitGeneric(blockcontext, "COSTUME")
    return ["lookLike:", costume]

def visitNextcostume(blockcontext):
    return ["nextCostume"]

def visitSwitchbackdropto(blockcontext):
    backdrop = visitGeneric(blockcontext, "BACKDROP")
    return ["startScene", backdrop]

def visitNextbackdrop(blockcontext):
    log.warn("[Scratch3] block {} ({}) possibly not available in Scratch2".format(blockcontext.block.opcode, blockcontext.block.name))
    return ["nextBackdropPlaceholder"] #TODO: not in scratch2

def visitChangesizeby(blockcontext):
    size = visitGeneric(blockcontext, "CHANGE")
    return ["changeSizeBy:", size]

def visitSetsizeto(blockcontext):
    size = visitGeneric(blockcontext, "SIZE")
    return ["setSizeTo:", size]

def visitChangeeffectby(blockcontext):
    block = blockcontext.block
    effect = block.fields["EFFECT"][0]
    change = visitGeneric(blockcontext, "CHANGE")
    return ["changeGraphicEffect:by:", effect, change]

def visitSeteffectto(blockcontext):
    block = blockcontext.block
    effect = block.fields["EFFECT"][0]
    value = visitGeneric(blockcontext, "VALUE")
    return ["setGraphicEffect:to:", effect, value]

def visitCleargraphiceffects(blockcontext):
    return ["filterReset"]

def visitShow(blockcontext):
    return ["show"]

def visitHide(blockcontext):
    return ["hide"]

def visitGotofrontback(blockcontext):
    return ["comeToFront"]

def visitGoforwardbackwardlayers(blockcontext):
    block = blockcontext.block
    direction = block.fields["FORWARD_BACKWARD"][0]
    change = visitGeneric(blockcontext, "NUM")
    return ["goBackByLayers:", change]

def visitCostumenumbername(blockcontext):
    block = blockcontext.block
    name_number = block.fields["NUMBER_NAME"][0]
    if name_number == "number":
        return ["costumeIndex"]
    if name_number == "name":
        return ["costumeName"]

    return ["costumeIndexPlaceholder"]


def visitBackdropnumbername(blockcontext):
    block = blockcontext.block
    name_number = block.fields["NUMBER_NAME"][0]
    log.warn("[Scratch3] block {} ({}) possibly not available in Scratch2".format(blockcontext.block.opcode, blockcontext.block.name))
    return ["sceneNamePlaceholder"] #TODO: implement properly

def visitSize(blockcontext):
    return ["scale"]

def visitCostume(blockcontext):
    block = blockcontext.block
    return block.fields['COSTUME'][0]

def visitBackdrops(blockcontext):
    block = blockcontext.block
    return block.fields['BACKDROP'][0]