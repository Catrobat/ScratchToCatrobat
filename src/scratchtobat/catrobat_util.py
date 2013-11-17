import org.catrobat.catroid.common  as catcommon

BACKGROUND_SPRITE_NAME = "Hintergrund"
CATROBAT_PROJECT_FILEEXT = ".catrobat"


def create_lookdata(name, file_name):
    look_data = catcommon.LookData()
    look_data.setLookName(name)
    look_data.setLookFilename(file_name)
    return look_data


def background_sprite_of_project(project):
    if project.getSpriteList().size() > 0:
        sprite = project.getSpriteList().get(0)
        assert sprite.getName() == BACKGROUND_SPRITE_NAME
    else:
        sprite = None
    return sprite
