from pyaudio import PyAudio
import struct
import math
import wave
import os

path="/home/ksb/Documents/dreu/analysis/python_scripts/audio_asr/audio/clipped/naming"


def calc_rms(block):
    rms=0
    n=len(block)
    for b in block:
        b = b / (2.**15)
        square=b*b
        rms+=square
        
    rms=math.sqrt(rms/n)
    return rms
    
def main():
    # read in some block data from pyaudio
    RATE=44100
    INPUT_BLOCK_TIME=0.2
    INPUT_FRAMES_PER_BLOCK=int(RATE*INPUT_BLOCK_TIME)
    pa=PyAudio()
         
    data=True
    fmt="%dh"%INPUT_FRAMES_PER_BLOCK
    total_rms=0
    total_blocks=0
    while data:
        for dr,subdr,fnames in os.walk(path):
            for filename in fnames:
                try:
                    print filename
                    wf=wave.open("%s/%s"%(path,filename),'rb')
                    strm=pa.open(format=pa.get_format_from_width(wf.getsampwidth()),
                        channels=wf.getnchannels(),
                        rate=wf.getframerate(),
                        input=True)
                    strm.stop_stream()
                    strm.close()
                    d=wf.readframes(INPUT_FRAMES_PER_BLOCK)
                    d=struct.unpack(fmt,d)
                    wf.close()
                    total_rms+=calc_rms(d)
                    total_blocks+=1
                except:
                    #print e
                    print "*** ERROR ***"
        data=False
    avg=total_rms/total_blocks
    print "The average is %f"%avg
    

main()    