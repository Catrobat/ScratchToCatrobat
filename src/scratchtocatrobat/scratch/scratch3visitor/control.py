from visitorUtil import visitGeneric, visitCondition, visitSubstack, visitMutation, visitParams
from visitorUtil import sanitizeListDefault, sanitizeListArgument


def visitWait(blockcontext):
    block = blockcontext.block
    duration = visitGeneric(blockcontext, 'DURATION')
    if duration == []:
        duration = block.inputs['DURATION'][1][1]
    return ["wait:elapsed:from:", duration]

def visitRepeat(blockcontext):
    block = blockcontext.block
    times = visitGeneric(blockcontext, "TIMES")
    if times == []:
        times = block.inputs["TIMES"][1][1]
    substack = visitSubstack(blockcontext, "SUBSTACK")
    return ["doRepeat", times, substack]

def visitIf(blockcontext):
    condition = visitCondition(blockcontext)
    substack1 = visitSubstack(blockcontext, "SUBSTACK")
    return ["doIf", condition, substack1]

def visitIf_else(blockcontext):
    condition = visitCondition(blockcontext)
    substack1 = visitSubstack(blockcontext, "SUBSTACK")
    substack2 = visitSubstack(blockcontext, "SUBSTACK2")
    return ["doIfElse", condition, substack1, substack2]

def visitWait_until(blockcontext):
    condition = visitCondition(blockcontext)
    return ["doWaitUntil", condition]

def visitRepeat_until(blockcontext):
    condition = visitCondition(blockcontext)
    substack1 = visitSubstack(blockcontext, "SUBSTACK")
    return ["doUntil", condition, substack1]

def visitCreate_clone_of(blockcontext):
    clone = visitGeneric(blockcontext, 'CLONE_OPTION')
    return ["createCloneOf", clone]

def visitCreate_clone_of_menu(blockcontext):
    block = blockcontext.block
    return block.fields["CLONE_OPTION"][0]

def visitStop(blockcontext):
    block = blockcontext.block
    return ["stopScripts", block.fields["STOP_OPTION"][0]]

def visitStart_as_clone(blockcontext):
    return ["whenCloned"]

def visitDelete_this_clone(blockcontext):
    return ["deleteClone"]

def visitForever(blockcontext):
    substack1 = visitSubstack(blockcontext, "SUBSTACK")
    return ["doForever", substack1]


def visitProcedures_call(blockcontext):
    proc_name = visitMutation(blockcontext)
    parameters = visitParams(blockcontext)
    #TODO: if the function has parameters, but the user calls it without params we should
    #insert a placeholder (e.g. None)
    return ["call", proc_name] + parameters

def visitProcedures_definition(blockcontext):
    proto = visitGeneric(blockcontext, "custom_block")
    return proto

def visitProcedures_prototype(blockcontext):
    proc_name = visitMutation(blockcontext)
    arguments = sanitizeListArgument(blockcontext.block.mutation["argumentnames"])
    if len(arguments) == 0:
        default_values = []
    else:
        default_values = sanitizeListDefault(blockcontext.block.mutation["argumentdefaults"])
    return [["procDef", proc_name, arguments, default_values, False]] #TODO: what is the last parameter


def visitArgumentIntOrString(blockcontext):
    param = blockcontext.block.fields["VALUE"][0]
    if param is None:
        param = 0
    return ["getParam", param, "r"] #TODO what is "r"

def visitArgumentBool(blockcontext):
    param =  blockcontext.block.fields["VALUE"][0]
    if param is None:
        param = False
    return ["getParam", param, "r"] #TODO what is "r"




