import io
import sigmf
import base64
import pandas as pd
import numpy as np
from scipy import signal


def load_sigmf_contents(contents):
    content_type, content_string = contents.split(',')
    d = io.BytesIO(base64.b64decode(content_string))
    arc = sigmf.SigMFArchiveReader(archive_buffer=d)
    return arc.sigmffile


def serialize_samples(samples: np.ndarray) -> dict[str, str]:
    buffer = base64.b64encode(samples).decode('utf-8')
    dtype = str(samples.dtype)
    return {'dtype': dtype, 'buffer': buffer }


def deserialize_samples(store: dict[str, str]) -> np.ndarray:
    buffer = base64.b64decode(store['buffer'].encode('utf-8'))
    dtype = store['dtype']
    return np.frombuffer(buffer, dtype=dtype)


def samples_to_psd(samples, sample_rate, fc=0, nperseg=1024*8):
    _, psd = signal.welch(samples, fs=sample_rate, scaling='spectrum', return_onesided=False, nperseg=nperseg)
    psd_db = 10 * np.log10(np.abs((np.fft.fftshift((psd)))/(len(psd))))
    f = np.linspace(fc - sample_rate / 2, fc + sample_rate / 2, len(psd))
    return f, psd_db


def sigmf_to_spectrogram(samples, sample_rate, nperseg=1024, fc=0):
    num_rows = len(samples) // nperseg # // is an integer division which rounds down
    spectrogram = np.zeros((num_rows, nperseg))

    for i in range(num_rows):
        start = i * nperseg
        stop = (i + 1) * nperseg

        f, spectrogram[i,:] = samples_to_psd(samples[start:stop], sample_rate, fc, nperseg=nperseg)

    return f, spectrogram


def get_peaks(freqs: np.ndarray, fftdb: np.ndarray, bandwidth: float=None, **kwargs) -> pd.DataFrame:
    '''Get FFT peaks using signal.find_peaks()

    Args:
        freqs:
            x-axis frequency range, usually the output of create_fft()
        fftdb:
            y-axis power data, usually the output of create_fft()
        bandwidth:
            required minimal peak bandwidth in Hz, used to calculate width
            passed to signal.find_peaks()
        kwargs:
            passed down to signal.find_peaks()

    Returns:
        A DataFrame with peak properties.
    '''
    if bandwidth is not None:
        f_res = freqs[1] - freqs[0]
        kwargs['width'] = bandwidth / f_res

    # add 'width' if not present, required to get signal.find_peaks() to output
    # width information
    if 'width' not in kwargs.keys():
        kwargs['width'] = 1

    peak_idxs, props = signal.find_peaks(fftdb, **kwargs)

    df = pd.DataFrame(props)
    df['indexes'] = peak_idxs
    df['center freq'] = freqs[peak_idxs]
    df['left freq'] = freqs[[int(i) for i in props['left_ips']]]
    df['right freq'] = freqs[[int(i) for i in props['right_ips']]]
    df['bandwidth'] = df['right freq'] - df['left freq']
    df['dBs'] = fftdb[peak_idxs]

    return df.sort_values('dBs', ascending=False)
