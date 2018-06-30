from visitorUtil import visitGeneric

def visitTouchingObject(blockcontext):
    touch = visitGeneric(blockcontext, "TOUCHINGOBJECTMENU")
    return ["touching:", touch]

def visitTouchingObjectMenu(blockcontext):
    block = blockcontext.block
    selection = block.fields["TOUCHINGOBJECTMENU"][0]
    return selection


def visitAskandwait(blockcontext):
    block = blockcontext.block
    question = visitGeneric(blockcontext, "QUESTION")
    if question == []:
        question = block.inputs["QUESTION"][1][1]
    return ["doAsk", question]

def visitSetdragmode(blockcontext):
    block = blockcontext.block
    dragmode = block.fields["DRAG_MODE"][0]
    return ["dragMode", dragmode] #TODO: not implemented in old converter?


def visitResettimer(blockcontext):
    return ["timerReset"]

def visitLoudness(blockcontext):
    return ["soundLevel"]

def visitDistanceto(blockcontext):
    distance = visitGeneric(blockcontext, "DISTANCETOMENU")
    return ["distanceTo:", distance]

def visitDistanceto_menu(blockcontext):
    return blockcontext.block.fields["DISTANCETOMENU"][0]

def visitColoristouchingcolor(blockcontext):
    color = visitGeneric(blockcontext, "COLOR")
    color2 = visitGeneric(blockcontext, "COLOR2")
    return ["touchingColor:", color, color2]

def visitOf(blockcontext):
    block = blockcontext.block
    property = block.fields['PROPERTY'][0]
    object = visitGeneric(blockcontext, 'OBJECT')
    return ["getAttribute:of:", property, object]


def visitTouchingobject(blockcontext):
    object = visitGeneric(blockcontext, 'TOUCHINGOBJECTMENU')
    return ["touching:", object]

def visitCurrent(blockcontext):
    block = blockcontext.block
    time = visitGeneric(blockcontext, "CURRENTMENU")
    return ["timeAndDate", time]

def visitCurrent_menu(blockcontext):
    block = blockcontext.block
    return block.fields["CURRENTMENU"][0]

def visitAnswer(blockcontext):
    return ["answer"]

def visitDayssince2000(blockcontext):
    return ["timestamp"]

def visitKeypressed(blockcontext):
    key = visitGeneric(blockcontext, "KEY_OPTION")
    if key == "": # shouldn't happen anyways since it is dropdown, but for some reason it can!?
        key = "space"
    return ["keyPressed:", key]

def visitKey_options(blockcontext):
    block = blockcontext.block
    key = block.fields["KEY_OPTION"][0]
    return key

def visitMousex(blockcontext):
    return ["mouseX"]

def visitMousedown(blockcontext):
    return ["mousePressed"]


def visitMousey(blockcontext):
    return ["mouseY"]


def visitTimer(blockcontext):
    return ["timer"]

def visitTouchingcolor(blockcontext):
    block = blockcontext.block
    color = visitGeneric(blockcontext, "COLOR")
    if color == []:
        color = block.inputs["COLOR"][1]
    return ["touchingColor:", color]

def visitUsername(blockcontext):
    return ["getUserName"]


def visitOf_object_menu(blockcontext):
    block = blockcontext.block
    return block.fields['OBJECT'][0]

def visitTouchingobjectmenu(blockcontext):
    block = blockcontext.block
    return block.fields['TOUCHINGOBJECTMENU'][0]

