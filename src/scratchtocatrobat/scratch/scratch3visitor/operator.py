from visitorUtil import visitGeneric
from scratchtocatrobat.tools import logger

log = logger.log


def visitSubtract(blockcontext):
    operand1 = visitGeneric(blockcontext, "NUM1")
    operand2 = visitGeneric(blockcontext, "NUM2")
    return ["-", operand1, operand2]

def visitGt(blockcontext):
    operand1 = visitGeneric(blockcontext, "OPERAND1")
    operand2 = visitGeneric(blockcontext, "OPERAND2")
    return [">", operand1, operand2]

def visitJoin(blockcontext):
    operand1 = visitGeneric(blockcontext, "STRING1")
    operand2 = visitGeneric(blockcontext, "STRING2")
    return ["concatenate:with:", operand1, operand2]

def visitLetter_of(blockcontext):
    letter = visitGeneric(blockcontext, "LETTER")
    string = visitGeneric(blockcontext, "STRING")
    return ["letter:of:", letter, string]

def visitLt(blockcontext):
    operand1 = visitGeneric(blockcontext, "OPERAND1")
    operand2 = visitGeneric(blockcontext, "OPERAND2")
    return ["<", operand1, operand2]

def visitNot(blockcontext):
    operand1 = visitGeneric(blockcontext, "OPERAND")
    if operand1 is None:
        operand1 = False
    return ["not", operand1]

def visitMod(blockcontext):
    operand1 = visitGeneric(blockcontext, "NUM1")
    operand2 = visitGeneric(blockcontext, "NUM2")
    return ["%", operand1, operand2]

def visitAdd(blockcontext):
    operand1 = visitGeneric(blockcontext, "NUM1")
    operand2 = visitGeneric(blockcontext, "NUM2")
    return ["+", operand1, operand2]

def visitEquals(blockcontext):
    operand1 = visitGeneric(blockcontext, "OPERAND1")
    operand2 = visitGeneric(blockcontext, "OPERAND2")
    return ["=", operand1, operand2]

def visitMathop(blockcontext):
    block = blockcontext.block
    num1 = visitGeneric(blockcontext, "NUM")
    operation = block.fields["OPERATOR"][0]
    return ["computeFunction:of:", operation, num1]

def visitAnd(blockcontext):
    operand1 = visitGeneric(blockcontext, "OPERAND1")
    if operand1 is None:
        operand1 = False
    operand2 = visitGeneric(blockcontext, "OPERAND2")
    if operand2 is None:
        operand2 = False
    return ["&", operand1, operand2]

def visitRound(blockcontext):
    operand1 = visitGeneric(blockcontext, "NUM")
    return ["rounded", operand1]

def visitMultiply(blockcontext):
    operand1 = visitGeneric(blockcontext, "NUM1")
    operand2 = visitGeneric(blockcontext, "NUM2")
    return ["*", operand1, operand2]

def visitRandom(blockcontext):
    from_param = visitGeneric(blockcontext, "FROM")
    to_param = visitGeneric(blockcontext, "TO")
    return ["randomFrom:to:", from_param, to_param]

def visitDivide(blockcontext):
    operand1 = visitGeneric(blockcontext, "NUM1")
    operand2 = visitGeneric(blockcontext, "NUM2")
    return ["/", operand1, operand2]

def visitContains(blockcontext):
    operand1 = visitGeneric(blockcontext, "STRING1")
    operand2 = visitGeneric(blockcontext, "STRING2")

    log.warn("[Scratch3] block {} ({}) possibly not available in Scratch2".format(blockcontext.block.opcode, blockcontext.block.name))
    return ["contains:", operand1, operand2]
    #TODO: not in scratch2?


def visitOr(blockcontext):
    operand1 = visitGeneric(blockcontext, "OPERAND1")
    if operand1 is None:
        operand1 = False
    operand2 = visitGeneric(blockcontext, "OPERAND2")
    if operand2 is None:
        operand2 = False
    return ["|", operand1, operand2]

def visitLength(blockcontext):
    operand1 = visitGeneric(blockcontext, "STRING")
    return ["stringLength:", operand1]
