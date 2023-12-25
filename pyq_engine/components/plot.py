import numpy as np

import plotly.graph_objs as go
import plotly.express as px

from pyq_engine import utils


def IQ(samples, title=None, decimate=10):
    samples = samples[::decimate]

    fig = px.scatter(
        x=np.real(samples) / np.max(np.real(samples)),
        y=np.imag(samples) / np.max(np.imag(samples)),
        title=title,
        labels={
            'x': 'I',
            'y': 'Q',
        },
    )

    fig.add_shape(
        type='circle',
        xref='x',
        yref='y',
        x0=-1, y0=-1, x1=1, y1=1,
        name='unit circle',
    )

    fig.update_layout(
        hovermode='closest',
        showlegend=True,
    )

    return fig


def draw_spectrogram_annotation(figure, annotation, frequency=None, time=None):
    y0 = annotation['core:sample_start']
    y1 = annotation['core:sample_count']

    if time is not None:
        y0 = time[y0]
        y1 = time[y1]

    if 'frequency_lower_edge' in annotation.keys():
        x0 = annotation['frequency_lower_edge']
        x1 = annotation['frequency_upper_edge']
    else:
        x0 = frequency[0]
        x1 = frequency[-1]

    figure.add_trace(go.Scatter(
        x=[x0, x0, x1, x1, x0],
        y=[y0, y1, y1, y0, y0],
        fill='toself',
        mode='lines',
        name=annotation['label'],
        showlegend=False,
    ))


def spectrogram(samples, metadata, fc, fft_size, title=None):
    sample_count = len(samples)
    sample_rate = metadata['global']['core:sample_rate']

    freq, spectrogram = utils.sigmf_to_spectrogram(samples, sample_rate, fft_size=fft_size, fc=fc)
    ytime = np.linspace(0.0, float(sample_count / sample_rate), num=sample_count // fft_size)

    fig = px.imshow(
        spectrogram,
        x=freq,
        y=ytime,
        title=title,
        aspect='auto',
        labels={
            'x': 'Frequency',
            'y': 'Time',
            'color': 'PSD',
        },
    )
    fig.update_layout(
        hovermode='x unified',
        xaxis_tickformat='~s',
        xaxis_ticksuffix='Hz',
        yaxis_tickformat='~s',
        yaxis_ticksuffix='s',
        coloraxis={
            'colorscale': 'viridis',
        },
    )

    fig.update_coloraxes(
        colorbar_tickformat='~s',
        colorbar_ticksuffix='dB',
    )

    for a in metadata['annotations']:
        draw_spectrogram_annotation(fig, a, frequency=freq, time=ytime)

    return fig


def draw_frequency_peaks(figure, peaks):
    figure.add_traces(
        go.Scatter(
            x=peaks['center freq'],
            y=peaks['dBs'],
            name='peaks',
            mode='markers',
            marker=dict(
                size=15,
                color='DarkOrange',
                symbol='circle-open-dot',
                line=dict(
                    width=2,
                ),
            ),
            hovertemplate='<br>dB=%{y:.2f}<br>fc=%{x:.3e}<br>%{text}',
            text=[f'bw={bw:.3e}<br>prominence={snr:.2}' for bw, snr in zip(peaks['bandwidth'], peaks['prominences'])],
        ),
    )


def draw_frequency_bandwidths(figure, peaks):
    peaks['y'] = peaks['dBs'] - peaks['prominences'] / 2
    peaks['xerr'] = peaks['right freq'] - peaks['center freq']
    peaks['xerrminus'] = peaks['center freq'] - peaks['left freq']
    peaks['yerr'] = peaks['prominences'] / 2

    figure.add_traces(
        go.Scatter(
            x=peaks['center freq'],
            y=peaks['y'],
            name='peaks',
            mode='markers',
            showlegend=False,
            hoverinfo='skip',
            marker=dict(
                size=1,
                color='red',
                line=dict(
                    width=2,
                ),
            ),
            error_x=dict(
                type='data',
                symmetric=False,
                array=peaks['xerr'],
                arrayminus=peaks['xerrminus'],
            ),
            error_y=dict(
                type='data',
                array=peaks['yerr'],
            ),
        ),
    )


def frequencies(samples, metadata, fc, title=None, analyze=False):
    sample_rate = metadata['global']['core:sample_rate']
    f, psd = utils.samples_to_psd(samples, sample_rate, fc=fc)
    fig = px.line(
        x=f,
        y=psd,
        title=title,
        labels={
            'x': 'Frequency',
            'y': 'PSD',
        },
    )

    if analyze:
        peaks = utils.get_peaks(f, psd, prominence=5)
        draw_frequency_peaks(fig, peaks)
        draw_frequency_bandwidths(fig, peaks)

    fig.update_layout(
        hovermode='x unified',
        xaxis_tickformat='~s',
        xaxis_ticksuffix='Hz',
        yaxis_tickformat='~s',
        yaxis_ticksuffix='dB',
    )

    return fig
