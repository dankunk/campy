"""

campy Python-based simultaneous multi-camera recording script implementing real-time compression
Output is (by default) one MP4 video file for each camera

Usage: 
cd to folder where videos will be stored (separate 'CameraN' folders will be generated)
python campy.py ./campy_config.yaml

Usage example:
python C:\\Code\\campy\\campy.py D:\\20200401\\test\\videos "C:\\Users\\Wang Lab\\Documents\\Basler\\Pylon5_settings\\acA1920-150uc_1152x1024p_100fps_trigger_RGB_p6.pfs" 6 100 10

python ~/Documents/campy/campy2.py /media/kyle/Video1/20200401/test/videos /home/kyle/Documents/Basler/acA1920-150uc_1152x1024p_100fps_trigger_BGR.pfs 4 100 5

"""

# Multiprocessing Pool method sustainable up to 1 MP @ 100 Hz? (24-bit RGB)
import numpy as np
import os
import time
import sys
import threading, queue
from collections import deque
import multiprocessing as mp

if sys.platform == "linux" or sys.platform == "linux2":
    os.environ['IMAGEIO_FFMPEG_EXE'] = '/home/usr/Documents/ffmpeg/ffmpeg'
# elif sys.platform == "win32":
#     os.environ['IMAGEIO_FFMPEG_EXE'] = 'C:\\ProgramData\\FFmpeg\\bin\\ffmpeg'

from cameras.basler import cam
from writer import campipe
from display import display

# To-do: change positional arguments to name value pairs
videoFolder = str(sys.argv[1])
camSettings = str(sys.argv[2])
numCams =  int(sys.argv[3])
frameRate = float(sys.argv[4])
recTimeInSec = float(sys.argv[5])

# User-set Parameters
# To-do: 
    # write config - include system, camera, and user configurations?
    # read config
    # replace campy input arguments with config.yaml input

# Recording config
# videoFolder = #
# recTimeInSec = #
# frameRate = 100
# numCams = 6

# System config (e.g. 3 gpus)
gpuToUse = [0, 0, 0, 2, 2, 2] # list of GPU indices for hardware compression (e.g. 0,1,2)

# Camera config
# camSettings list (1 for each camera) or 1 for all
# camProducer = basler
# camPixelFormat = rgb # bayer, gray

# ffmpeg config
# quality = 19
# codec = 'H264_nvenc' # hevc_nvenc

# User default settings
chunkLengthInSec = 30
displayFrameRate = 10 # In hz, set up to ~30
displayDownSample = 2 # Downsampling factor for displaying images

def main(c):
    # Initialize queues for display window and video writer
    dispQueue = deque([],2)
    writeQueue = deque()

    # Open camera c
    camera = cam.Open(c, camSettings)

    # Start ffmpeg video writer 
    writer = campipe.OpenWriter(c, videoFolder, frameRate, gpu=gpuToUse[c])

    # Start image window display ('consumer' thread)
    threading.Thread(
        target=display.DisplayFrames, 
        daemon=True, 
        args=(c, dispQueue,)
        ).start()

    # Start video writer ('consumer' thread)
    threading.Thread(
        target=campipe.WriteFrames, 
        daemon=True, 
        args=(c, writer, writeQueue, frameRate, recTimeInSec,)
        ).start()

    # Start retrieving frames (main 'producer' thread)
    meta = cam.GrabFrames(c, camera, dispQueue, writeQueue, 
        frameRate, recTimeInSec, displayFrameRate, displayDownSample)

    # Once GrabFrames is finished grabbing, close up camera
    cam.Close(c, camera)

    # Save metadata at end of recording (frame numbers, timestamps, camera parameters etc.)
    cam.SaveMetadata(c, meta, videoFolder)

if __name__ == '__main__':

    if sys.platform=='win32':
        pool = mp.Pool(processes=numCams)
        pool.map(main, range(0, numCams))

    elif sys.platform == 'linux' or sys.platform == 'linux2':
        ctx = mp.get_context('spawn') # for linux compatibility
        pool = ctx.Pool(processes=numCams)
        p = pool.map_async(main, range(0, numCams))
        p.get()