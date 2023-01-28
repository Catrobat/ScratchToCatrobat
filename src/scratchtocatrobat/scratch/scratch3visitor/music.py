from visitorUtil import visitGeneric
from scratchtocatrobat.tools import logger

log = logger.log

def visitPlayDrumForBeats(blockcontext):
    drum = visitGeneric(blockcontext, 'DRUM')
    beats = visitGeneric(blockcontext, "BEATS")
    return ['drum:duration:elapsed:from:', drum, beats]

def visitDrumMenu(blockcontext):
    block = blockcontext.block
    return block.fields["DRUM"][0]

def visitPlayNoteForBeats(blockcontext):
    note = visitGeneric(blockcontext, 'NOTE')
    beats = visitGeneric(blockcontext, "BEATS")
    return ['noteOn:duration:elapsed:from:', note, beats]

def visitNoteMenu(blockcontext):
    block = blockcontext.block
    return block.fields["NOTE"][0]

def visitChangeTempoBy(blockcontext):
    tempo = visitGeneric(blockcontext, 'TEMPO')
    return ['changeTempoBy:', tempo]









