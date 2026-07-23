from typing import Dict, Optional

import threading
import sounddevice as sd
import soundfile as sf

import midiseq.env as env




class AudioSample():
    def __init__(self, buffer, samplerate):
        self.buffer = buffer
        self.samplerate = samplerate
        self.dur = len(buffer) / samplerate



class AudioMixer():
    def __init__(self):
        self.samplerate = 44_100
        self.blocksize = 2048

        self.samples: Dict[int, list] = {}
        self._active_samples = set() # Set of sample_id
        self._lock = threading.Lock()

        self._running = False
        self.stream = sd.OutputStream(
            samplerate = self.samplerate,
            channels = 2,
            blocksize = self.blocksize,
            callback = self._callback,
            finished_callback = self._finished_callback
        )
    

    def loadSample(self, audio_path: str, sample_n: int) -> None:
        """Load a sample"""
        data, sr = sf.read(audio_path, always_2d=True)
        self.samples[sample_n] = [data, 0, False] # List of [audio_data, frame_n, looping]


    def triggerSample(self, sample_id: int, time=0, looping=False) -> None:
        """Start a sample immediately"""
        if not self._running:
            self.stream.start()
            self._running = True
        
        with self._lock:
            self.samples[sample_id][1] = 0  # Reset frame index
            self._active_samples.add(sample_id)


    def _callback(self, outdata, buffer_size, time, status):
        """
        If no data is to be sent, the output buffer should be filled with zeroes.

        https://python-sounddevice.readthedocs.io/en/0.5.3/api/streams.html#sounddevice.Stream

        Args:
            outdata:
                Audio buffer to be written to (two-dimensional numpy.ndarray)
            frames (int):
                Number of audio frames to be processed
            time:
                Time structure 
            status:
                Description
        """
        if status:
            print(status)

        outdata.fill(0)

        with self._lock:
            active_snapshot = self._active_samples.copy()

        for segment_id in active_snapshot:
            sample = self.samples[segment_id]
            audio_data = sample[0]
            frame_idx = sample[1]
            chunksize = min(len(audio_data) - frame_idx, buffer_size)
            outdata[:chunksize] += audio_data[frame_idx:frame_idx + chunksize]
            if chunksize < buffer_size:
                # End of sample
                with self._lock:
                    self._active_samples.remove(segment_id)
            else:
                sample[1] = frame_idx + chunksize


    def _finished_callback(self):
        print("stopped")


    def stop(self):
        self.stream.stop()
    


def listAudioDevices():
    print(sd.query_devices())



def recAudio(dur=1) -> AudioSample:
    sr = env.samplerate
    recording = sd.rec(int(dur * sr), samplerate=sr, channels=2)
    sd.wait() # Wait for process to finish
    return AudioSample(recording, sr)
    # myrecording = sd.rec(int(duration * fs), dtype='int16')


def openAudio(filename) -> AudioSample:
    data, sr = sf.read(filename, always_2d=True)
    return AudioSample(data, sr)



# current_frame = 0

# def playAudio(audioseq: AudioSample, loop=False):

#     def callback(outdata, frames, time, status):
#         """
#         If no data is to be sent, the output buffer should be filled with zeroes.

#         https://python-sounddevice.readthedocs.io/en/0.5.3/api/streams.html#sounddevice.Stream

#         Args:
#             outdata:
#                 Audio buffer to be written to (two-dimensional numpy.ndarray)
#             frames (int):
#                 Number of audio frames to be processed
#             time:
#                 Time structure 
#             status: Description
#         """
#         global current_frame

#         if status:
#             print(status)

#         chunksize = min(len(data) - current_frame, frames)
#         outdata[:chunksize] = data[current_frame:current_frame + chunksize]
#         if chunksize < frames:
#             # Last audio chunk
#             if loop:
#                 outdata[chunksize:] = data[:frames - chunksize] # Loop data
#                 current_frame = frames - chunksize
#             else:
#                 outdata[chunksize:] = 0 # Pad with zeroes
#                 raise sd.CallbackStop()
#         current_frame += chunksize
    
#     def finished_callback():
#         event.set()
#         print("stopped")
    
#     data = audioseq.buffer
#     event = threading.Event()
#     stream = sd.OutputStream(
#         samplerate=audioseq.samplerate,
#         channels=data.shape[1],
#         blocksize=env.blocksize,
#         callback=callback,
#         finished_callback=finished_callback
#     )
    
#     with stream:
#         event.wait()
    


def test():
    duration = 2  # seconds

    def callback(indata, outdata, frames, time, status):
        if status:
            print(status)
        outdata[:] = indata

    with sd.Stream(channels=2, callback=callback):
        sd.sleep(int(duration * 1000))



# playAudio(openAudio("test.wav"))