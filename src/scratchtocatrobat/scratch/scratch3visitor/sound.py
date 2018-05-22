from visitorUtil import visitGeneric

def visitPlay(blockcontext):
    sound = visitGeneric(blockcontext, 'SOUND_MENU')
    return ['playSound:', sound]

def visitPlayuntildone(blockcontext):
    sound = visitGeneric(blockcontext, 'SOUND_MENU')
    return ['playSoundAndWait', sound]

def visitStopallsounds(blockcontext):
    return ["stopAllSounds"]

def visitChangeeffectby(blockcontext):
    block = blockcontext.block
    pass #TODO: doesnt exist in scratch2/catroid

def visitSeteffectto(blockcontext):
    block = blockcontext.block
    pass #TODO: doesnt exist in scratch2/catroid

def visitCleareffects(blockcontext):
    return ["clearSoundEffects"] #TODO: not in scratch2

def visitChangevolumeby(blockcontext):
    block = blockcontext.block
    volume = visitGeneric(blockcontext, "VOLUME")
    if volume == []:
        volume = block.inputs['VOLUME'][1][1]
    return ["changeVolumeBy:", volume]

def visitSetvolumeto(blockcontext):
    block = blockcontext.block
    volume = visitGeneric(blockcontext, "VOLUME")
    if volume == []:
        volume = block.inputs['VOLUME'][1][1]
    return ["setVolumeTo:", volume]

def visitVolume(blockcontext):
    return ["volume"]


def visitSounds_menu(blockcontext):
    block = blockcontext.block
    return block.fields["SOUND_MENU"][0]


#TODO: replace music extension bricks with default ones?