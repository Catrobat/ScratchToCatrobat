import sys
from scratchtobat import sb2webapi, sb2, converter
import tempfile


def scratchtobat_main(argv):
    # TODO: add with upload zip
    scratch_project_url = argv[0]
    catroid_zip_path = argv[1]
    temp_download_dir = tempfile.mkdtemp()
    try:
        sb2webapi.download_project(scratch_project_url, temp_download_dir)
        project = sb2.Project(temp_download_dir)
        converter.convert_sb2_project_to_catroid_zip(project, catroid_zip_path)
    except Exception:
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(scratchtobat_main(sys.argv[1:]))
    