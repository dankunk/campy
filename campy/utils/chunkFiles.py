
import os
import imageio
import math
from subprocess import Popen
import sys
import time
import multiprocessing as mp

numCams = int(sys.argv[1])
chunkLengthInSec = float(sys.argv[2])  # User provides seconds directly
fname = str(sys.argv[3])

basedir = os.getcwd()

# Get metadata from video (assuming all cameras are the same)
vid1 = os.path.join(basedir,'Camera0',fname)
vid = imageio.get_reader(vid1)
fps = vid.get_meta_data()['fps']
durationInSec = vid.get_meta_data()['duration']
durationInFrames = int(fps * durationInSec)

# Compute chunk length in frames from chunk length in seconds
chunkLengthInFrames = int(fps * chunkLengthInSec)

# Compute how many chunks are needed
numChunks = math.ceil(durationInFrames / chunkLengthInFrames)

def chunkFiles(camNum):
    startFrame = 0
    endFrame = startFrame + chunkLengthInFrames - 1
    startTimeInSec = 0
    hrsStart = 0; minStart = 0; secStart = 0; msStart = 0

    viddir = os.path.join(basedir,'Camera' + str(camNum))
    fname_in = os.path.join(viddir, fname)

    for t in range(numChunks):
        outdir = os.path.join(viddir,'workspace')
        if not os.path.isdir(outdir):
            os.mkdir(outdir)
        fname_out = os.path.join(outdir,f"{startFrame}_{endFrame}.mp4")

        # Calculate startTime from hrsStart, minStart, secStart, msStart
        startTime = f"{hrsStart}:{minStart}:{secStart}.{msStart}"

        # Compute endTime from startTimeInSec + chunkLengthInSec
        timeEnd = startTimeInSec + chunkLengthInSec
        hr = math.floor(timeEnd/3600)
        timeEnd -= hr*3600
        mn = math.floor(timeEnd/60)
        timeEnd -= mn*60
        sc = math.floor(timeEnd)
        timeEnd -= sc
        ms = math.floor(timeEnd*1000)

        endTime = f"{hr}:{mn}:{sc}.{ms}"

        cmd = (f"ffmpeg -y -i {fname_in} -ss {startTime} -to {endTime} "
               f"-c:v copy -c:a copy {fname_out} -async 1 "
               "-hide_banner -loglevel warning")

        if os.path.isfile(fname_out):
            print(f"Video {camNum+1} chunk {t} already exists...")
        else:
            p = Popen(cmd.split())
            print(f"Copying video {camNum+1} chunk {t}...")
            time.sleep(5)

        startFrame += chunkLengthInFrames
        endFrame = startFrame + chunkLengthInFrames - 1
        if endFrame > durationInFrames:
            endFrame = durationInFrames
        startTimeInSec += chunkLengthInSec
        hrsStart = hr
        minStart = mn
        secStart = sc
        msStart = ms

if __name__ == '__main__':            
    ts = time.time()
    print('Chunking videos...')
    pp = mp.Pool(numCams)
    pp.map(chunkFiles, range(numCams))