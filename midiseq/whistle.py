import wave
import numpy as np
import sounddevice as sd

from .elements import Seq, Note
import midiseq.env as env

import matplotlib.pyplot as plt



def readWav(filename):
    with wave.open(filename, 'rb') as wav_file:
        num_frames = wav_file.getnframes()
        sample_width = wav_file.getsampwidth()
        framerate = wav_file.getframerate()
        data = wav_file.readframes(num_frames)

    # Convert binary data to numpy array
    dtype_map = {1: np.int8, 2: np.int16, 4: np.int32}
    audio_data = np.frombuffer(data, dtype=dtype_map[sample_width])

    return audio_data, framerate



def spectrogram(x, Fs, NFFT=1024, noverlap=512):

    def window_hanning(x):
        """ 
        Return *x* times the Hanning (or Hann) window of len(*x*).
        """
        return np.hanning(len(x))*x
    
    result = np.lib.stride_tricks.sliding_window_view(x, NFFT, axis=0)[::NFFT - noverlap].T
    
    window = window_hanning(np.ones(NFFT, x.dtype))
    result = result * window.reshape((-1, 1))
    
    numFreqs = (NFFT + 1)//2
    result = np.fft.rfft(result, n=NFFT, axis=0)[:numFreqs, :]
    
    result = np.conj(result) * result # Power spectral density
    freqs = np.fft.rfftfreq(NFFT, 1/Fs)[:numFreqs]
    t = np.arange(NFFT/2, len(x) - NFFT/2 + 1, NFFT - noverlap)/Fs

    return result.real, freqs, t



def normalizeSpectrogram(spec, freqs, times, low_freq=200, high_freq=4000):
    # Remove unused frequencies
    min_freq_index = np.argmin(freqs < low_freq)
    max_freq_index = np.argmax(freqs > high_freq)
    freqs = freqs[min_freq_index:max_freq_index]
    spec = spec[min_freq_index:max_freq_index]
    
    # Normalize spectrogram
    min_val = np.min(spec)
    max_val = np.max(spec)
    spec_norm = (spec - min_val) / (max_val - min_val)
    
    return spec_norm, freqs, times



def findRegions(spec, freqs, times):
    """ Should be called with on a spectrogram with a high time resolution
    """
    
    peak_power = np.max(spec, axis=0)
    peak_fbin = np.argmax(spec, axis=0)
    threshold = 0.02 * peak_power.max()
    gate = peak_power > threshold
    
    gate_idx = np.where(gate)[0]
    regions = []
    region_start = gate_idx[0]
    last_idx = gate_idx[0]
    last_fbin = peak_fbin[last_idx]
    for idx in gate_idx:
        if idx - last_idx > 1 or abs(peak_fbin[idx] - last_fbin) > 1:
            # Region break
            regions.append( (region_start, last_idx) )
            region_start = idx
        last_idx = idx
        last_fbin = peak_fbin[idx]
    regions.append( (region_start, last_idx ) )
    
    # Convert to seconds
    regions = [ (times[start], times[end]) for start, end in regions ]

    # Filter out impossibly short regions
    regions = [ (start, end) for start, end in regions if end-start > 0.05 ]
    
    return regions



def findRegionsIdx(spec, freqs, times):
    """ Should be called with on a spectrogram with a high time resolution
    """
    
    peak_power = np.max(spec, axis=0)
    peak_fbin = np.argmax(spec, axis=0)
    threshold = 0.02 * peak_power.max()
    gate = peak_power > threshold
    
    gate_idx = np.where(gate)[0]
    regions = []
    region_start = gate_idx[0]
    last_idx = gate_idx[0]
    last_fbin = peak_fbin[last_idx]
    for idx in gate_idx:
        if idx - last_idx > 1 or abs(peak_fbin[idx] - last_fbin) > 1:
            # Region break
            regions.append( (region_start, last_idx) )
            region_start = idx
        last_idx = idx
        last_fbin = peak_fbin[idx]
    regions.append( (region_start, last_idx ) )
    
    # Filter out impossibly short regions
    regions = [ (start, end) for start, end in regions if end-start > 2 ]

    return regions



def getRegionsPitch(spec, freqs, times, regions):
    """ Find the mean frequency for every time regions
        Should be called with a spectrogram with a high frequency resolution
    """
    
    regions_freq = []
    
    for start, end in regions:
        start_i = np.searchsorted(times, start)
        end_i = np.searchsorted(times, end)

        region_spec = spec[:, start_i:end_i]
        freq_idx = region_spec.argmax(axis=0)
        mean_freq = freqs[freq_idx].mean()
        print(start_i, end_i, mean_freq)
        
        regions_freq.append(mean_freq)
    
    return regions_freq



def hz2midi(frequency, tuning=440):
    # Calculate MIDI pitch using the formula
    midi_pitch = 69 + 12 * np.log2(frequency / tuning)
    rounded_midi_pitch = int(round(midi_pitch))
    return rounded_midi_pitch



def audio2seq(audio_data, framerate, tuning=440):
    # Create a spectrogram with high time resolution to find temporal regions
    spec, freqs, times = spectrogram(audio_data, Fs=framerate, NFFT=512, noverlap=256)
    spec, freqs, times = normalizeSpectrogram(spec, freqs, times, low_freq=500)
    regions = findRegions(spec, freqs, times)
    print(len(regions))

    # Create a spectrogram with high frequency resolution to find pitch
    spec, freqs, times = spectrogram(audio_data, Fs=framerate, NFFT=2048, noverlap=1024)
    mean_frequencies = getRegionsPitch(spec, freqs, times, regions)

    print(mean_frequencies)
    regions = zip(regions,
                map(lambda f: hz2midi(f, tuning), mean_frequencies))
    
    seq = Seq()
    for (start, end), pitch in regions:
        dur = end - start
        note = Note(pitch, dur / env.note_dur)
        seq.add(note, start)
    
    return seq



def wav2seq(filename) -> Seq:
    """ Convert a wave file to a MIDI sequence """
    audio_data, framerate = readWav(filename)
    plot_spectrogram(audio_data, framerate)
    return audio2seq(audio_data, framerate)



def whistle(dur=4, tuning=440.0, strip=True) -> Seq:
    """ Record a MIDI sequence by whistling in a microphone

        Parameters
        ----------
            dur : int
                Recording duration (in seconds)
            tuning : float
                'A' tuning (in Hz)
            strip : boolean
                Remove silences at both ends
    """
    print(f"Recording for {dur} seconds...", end='')
    sr = 44100
    buffer = sd.rec(int(dur * sr), samplerate=sr, channels=1)[:,0]
    sd.wait()
    print("done")
    buffer *= 2**15
    buffer = buffer.astype(np.int16)

    plot_spectrogram(buffer, sr)
    seq = audio2seq(buffer, sr, tuning=tuning)
    if strip:
        seq.strip()
    return seq



def plot_spectrogram(audio_data, framerate, NFFT=512, noverlap=256):
    spec, freqs, times = spectrogram(audio_data, Fs=framerate, NFFT=NFFT, noverlap=noverlap)
    spec, freqs, times = normalizeSpectrogram(spec, freqs, times, low_freq=500)
    
    regions = findRegions(spec, freqs, times)
    
    #spec = np.flipud(spec)
    
    # Plot the spectrogram
    plt.figure()
    plt.subplot(211)
    plt.imshow(20 * np.log10(spec), cmap='viridis')
    plt.xlabel('Time (s)')
    plt.ylabel('Frequency (Hz)')
    plt.axis('auto')
    #plt.ylim(0, 8000)
    plt.title('Spectrogram')
    #plt.colorbar(label='Intensity (dB)')
    
    regions = findRegionsIdx(spec, freqs, times)
    gate = np.zeros(len(spec[0]))
    for reg in regions:
        gate[reg[0]:reg[1]] = 1.0

    
    #plt.tight_layout()
    plt.subplot(212)
    plt.plot(spec.max(axis=0))
    plt.xlim(0, len(spec[0]))
    
    plt.show()