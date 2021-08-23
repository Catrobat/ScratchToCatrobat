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






