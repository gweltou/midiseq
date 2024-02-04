from __future__ import annotations

import threading
import sounddevice as sd
import soundfile as sf

import midiseq.env as env


env.samplerate = 44100



class SeqAudio():

    def __init__(self, buffer, samplerate):
        self.buffer = buffer
        self.samplerate = samplerate
        self.dur = len(buffer) / samplerate
        self.gain = 1.0
    

    def play(self):
        sd.play(self.buffer, self.samplerate)




def listAudioDevices():
    print(sd.query_devices())



def recAudio(dur=1) -> SeqAudio:
    sr = env.samplerate
    recording = sd.rec(int(dur * sr), samplerate=sr, channels=2)
    sd.wait() # Wait for process to finish
    return SeqAudio(recording, sr)
    # myrecording = sd.rec(int(duration * fs), dtype='int16')


def openAudio(filename) -> SeqAudio:
    data, sr = sf.read(filename, always_2d=True)
    return SeqAudio(data, sr)



current_frame = 0

def playAudio(audioseq: SeqAudio, loop=False):

    def callback(outdata, frames, time, status):
        global current_frame

        if status:
            print(status)

        chunksize = min(len(data) - current_frame, frames)
        outdata[:chunksize] = data[current_frame:current_frame + chunksize]
        if chunksize < frames:
            if loop:
                outdata[chunksize:] = data[:frames - chunksize]
                current_frame = frames - chunksize
            else:
                outdata[chunksize:] = 0
                raise sd.CallbackStop()
        current_frame += chunksize
    
    def finished_callback():
        event.set()
        print("stopped")
    
    data = audioseq.buffer
    event = threading.Event()
    stream = sd.OutputStream(
            samplerate=audioseq.samplerate, channels=data.shape[1], blocksize=2048,
            callback=callback, finished_callback=finished_callback)
    
    with stream:
        event.wait()
    


def test():
    duration = 2  # seconds

    def callback(indata, outdata, frames, time, status):
        if status:
            print(status)
        outdata[:] = indata

    with sd.Stream(channels=2, callback=callback):
        sd.sleep(int(duration * 1000))



playAudio(openAudio("test.wav"))