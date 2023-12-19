import numpy as np
from scipy import signal


def samples_to_psd(samples, sample_rate, fc=0, nperseg=1024*8):
    _, psd = signal.welch(samples, fs=sample_rate, scaling='spectrum', return_onesided=False, nperseg=nperseg)
    psd_db = 10 * np.log10(np.abs((np.fft.fftshift((psd)))/(len(psd))))
    f = np.linspace(fc - sample_rate / 2, fc + sample_rate / 2, len(psd))
    return f, psd_db


def sigmf_to_spectrogram(samples, sample_rate, fft_size=1024, fc=0):
    num_rows = len(samples) // fft_size # // is an integer division which rounds down
    spectrogram = np.zeros((num_rows, fft_size))

    for i in range(num_rows):
        start = i * fft_size
        stop = (i + 1) * fft_size

        f, spectrogram[i,:] = samples_to_psd(samples[start:stop], sample_rate, fc, nperseg=fft_size)

    return f, spectrogram
