import sys
import os
import tempfile
import subprocess
import time
from parser import ScratchOutputParser

def main():
    if len(sys.argv) != 4:
        print 'Invalid arguments. Correct usage:'
        print 'python catrobatProjectBuilder.py <path_to_scratch_project> <project_title> <path_to_output>'
        return 1
    path_to_scratch_project = sys.argv[1]
    project_title = sys.argv[2]
    path_to_output = sys.argv[3]


    scratch_temp_folder = tempfile.mkdtemp()
    pipe = subprocess.Popen(['./squeak/scratch', 'squeak/ScratchSourceCode1.4.image', path_to_scratch_project, scratch_temp_folder])
    scratch_pid = pipe.pid

    elapsed_time = 0
    while not os.path.isfile(os.path.join(scratch_temp_folder, 'finished.txt')) and elapsed_time < 300:
        time.sleep(1)
        elapsed_time += 1

    subprocess.Popen(['kill', '-9', str(scratch_pid)])

    parser = ScratchOutputParser(scratch_temp_folder, project_title)
    parser.process_project()
    parser.save_to(path_to_output)


if __name__ == '__main__':
    main()