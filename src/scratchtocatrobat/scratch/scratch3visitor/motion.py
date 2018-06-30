from visitorUtil import visitGeneric

def visitMovesteps(blockcontext):
    steps = visitGeneric(blockcontext, "STEPS")
    return ["forward:", steps]

def visitTurnright(blockcontext):
    degrees = visitGeneric(blockcontext, "DEGREES")
    return ["turnRight:", degrees]

def visitTurnleft(blockcontext):
    degrees = visitGeneric(blockcontext, "DEGREES")
    return ["turnLeft:", degrees]

def visitGoto(blockcontext):
    to = visitGeneric(blockcontext, "TO")
    return ["gotoSpriteOrMouse:", to]

def visitGotoxy(blockcontext):
    x = visitGeneric(blockcontext, "X")
    y = visitGeneric(blockcontext, "Y")
    return ["gotoX:y:", x, y]

def visitGlideto(blockcontext):
    secs = visitGeneric(blockcontext, "SECS")
    to = visitGeneric(blockcontext, "TO")
    return ["glideTo:", secs, to] #TODO: not in scratch2?

def visitGlidesecstoxy(blockcontext):
    secs = visitGeneric(blockcontext, "SECS")
    x = visitGeneric(blockcontext, "X")
    y = visitGeneric(blockcontext, "Y")
    return ["glideSecs:toX:y:elapsed:from:", secs, x, y]

def visitPointindirection(blockcontext):
    direction = visitGeneric(blockcontext, "DIRECTION")
    return ["heading:", direction]

def visitPointtowards(blockcontext):
    towards = visitGeneric(blockcontext, "TOWARDS")
    return ["pointTowards:", towards]

def visitChangexby(blockcontext):
    x = visitGeneric(blockcontext, "DX")
    return ["changeXposBy:", x]

def visitSetx(blockcontext):
    x = visitGeneric(blockcontext, "X")
    return ["xpos:", x]

def visitChangeyby(blockcontext):
    y = visitGeneric(blockcontext, "DY")
    return ["changeYposBy:", y]

def visitSety(blockcontext):
    y = visitGeneric(blockcontext, "Y")
    return ["ypos:", y]

def visitIfonedgebounce(blockcontext):
    return ["bounceOffEdge"]

def visitSetrotationstyle(blockcontext):
    block = blockcontext.block
    rotation_style = block.fields["STYLE"][0]
    return ["setRotationStyle", rotation_style]

def visitDirection(blockcontext):
    return ["heading"]

def visitYposition(blockcontext):
    return ["ypos"]

def visitXposition(blockcontext):
    return ["xpos"]

def visitGoto_menu(blockcontext):
    block = blockcontext.block
    return block.fields["TO"][0]

def visitGlideto_menu(blockcontext):
    block = blockcontext.block
    return block.fields["TO"][0]

def visitPointtowards_menu(blockcontext):
    block = blockcontext.block
    return block.fields["TOWARDS"][0]