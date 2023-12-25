import dash_bootstrap_components as dbc
import argparse
from dash import Dash, dcc, html, Input, Output, State
import dash_daq as daq
import plotly.express as px
import plotly.graph_objs as go

import base64
import io
import sigmf
import time
import numpy as np
from pathlib import Path

from pyq_engine import utils


fft_size_options = [2**i for i in range(5, 15)]
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

controls = dbc.Card(
    [
        html.Div(
            [
                dcc.Upload(
                    id='filename',
                    children=html.Div([
                        html.A('Upload SigMFArchive')
                    ]),
                    style={
                        'width': '100%',
                        'height': '60px',
                        'lineHeight': '60px',
                        'borderWidth': '1px',
                        'borderStyle': 'dashed',
                        'borderRadius': '5px',
                        'textAlign': 'center',
                    },
                ),
            ],
        ),
        html.Hr(),
        html.Div(
            [
                dbc.Label('FFT Size'),
                dcc.Dropdown(
                    id='fft-size',
                    options=fft_size_options,
                    value=1024,
                ),
            ],
        ),
        html.Hr(),
        html.Div(
            [
                daq.BooleanSwitch(label='RF Frequencies', id='rf-freq', on=True),
                daq.BooleanSwitch(label='Analysis', id='do-analysis', on=True),
            ],
        ),
        html.Hr(),
        html.Div(
            [
                dbc.Label('Cursor'),
                dcc.RangeSlider(
                    0, 50,
                    value=[10, 20],
                    marks=None,
                    allowCross=False,
                    tooltip={'placement': 'bottom', 'always_visible': True},
                    id='cursor',
                ),
            ],
        ),
        html.Hr(),
        dbc.Button(
            "Toggle Metadata",
            id="metadata-button",
            className="me-1",
            color="primary",
            n_clicks=0,
            style={
                'width': '100%',
                'margin-bottom': '10px',
            },
        ),
        dbc.Button(
            [
                "Toggle Annotations",
                dbc.Badge(id='annotations-count', color='danger', className="ms-1"),
            ],
            id="annotations-button",
            className="me-1",
            color="primary",
            n_clicks=0,
            style={
                'width': '100%',
                'margin-bottom': '10px',
            },
        ),
    ],
    body=True,
)

tabs = dbc.Container(
    [
        dbc.Tabs(
            [
                dbc.Tab(label='Spectrogram', tab_id='spectrogram'),
                dbc.Tab(label='Frequency', tab_id='frequency'),
                dbc.Tab(label='IQ Plot', tab_id='iq'),
            ],
            id='tabs',
            active_tab='spectrogram',
            className="p-0",
        ),
        html.Div(id="tab-content", className="p-0"),
    ],
)

app.layout = dbc.Container(
    [
        html.H1('PYQ Engine'),
        html.Hr(),
        dcc.Store(id='graph-store'),
        dcc.Store(id='metadata-store'),
        dcc.Store(id='annotations-store'),
        dbc.Row(
            [
                dbc.Col(controls, md=3),
                dbc.Col(tabs, md=9),
            ],
            align='center',
        ),
        dbc.Collapse(
            dbc.Card(dbc.CardBody(id='metadata')),
            id="metadata-collapse",
            is_open=False,
        ),
        dbc.Collapse(
            dbc.Card(dbc.CardBody(id='annotations')),
            id="annotations-collapse",
            is_open=False,
        ),
    ],
    fluid=True,
)

@app.callback(
    Output("tab-content", "children"),
    [Input("tabs", "active_tab"), Input('graph-store', 'data')],
)
def render_tab_content(active_tab, data):
    """
    This callback takes the 'active_tab' property as input, as well as the
    stored graphs, and renders the tab content depending on what the value of
    'active_tab' is.
    """
    if active_tab and data is not None:
        if active_tab in data.keys():
            return dcc.Graph(figure=data[active_tab])

    return "No tab selected"


@app.callback(
    [
        Output("cursor", "max"),
        Output("cursor", "value"),
    ],
    Input('filename', 'filename'),
    Input('filename', 'contents'),
)
def update_cursor(filename, contents):
    count = 50

    if filename:
        content_type, content_string = contents.split(',')
        d = io.BytesIO(base64.b64decode(content_string))
        arc = sigmf.SigMFArchiveReader(archive_buffer=d)
        count = arc.sigmffile.shape[0]

    return count, [0, count]


@app.callback(
    Output("metadata-collapse", "is_open"),
    [Input("metadata-button", "n_clicks")],
    [State("metadata-collapse", "is_open")],
)
def toggle_collapse_metadata(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    Output("metadata", "children"),
    Input('metadata-store', 'data'),
)
def update_metadata(metadata):
    if metadata is None:
        return 'open file to display metadata'

    children = []
    for k, v in metadata.items():
        children.append(
            dbc.Row(
                [
                    dbc.Col(dbc.Label(k)),
                    dbc.Col(dbc.Label(v)),
                ],
            ),
        )

    return dbc.Container(children)

@app.callback(
    Output("annotations-collapse", "is_open"),
    [Input("annotations-button", "n_clicks")],
    [State("annotations-collapse", "is_open")],
)
def toggle_collapse_annotations(n, is_open):
    if n:
        return not is_open
    return is_open

@app.callback(
    [
        Output("annotations", "children"),
        Output("annotations-count", "children"),
    ],
    Input('annotations-store', 'data'),
)
def update_annotations(annotations):
    if annotations is None:
        return 'open file to display annotations', ''

    if len(annotations) == 0:
        return 'Collection contains no annotations', ''

    cards = []
    for i, a in enumerate(annotations):
        cards.append(dbc.Card(
            [
                dbc.CardBody(
                    className='card-text',
                    children=[
                        html.H4(f'Annotation {i}', className='card-title'),
                    ] + [
                        dbc.Row(
                            [
                                dbc.Col(dbc.Label(k)),
                                dbc.Col(dbc.Label(v)),
                            ],
                        ) for k, v in a.items()
                    ],
                ),
            ],
        ))

    return cards, str(len(annotations))


def draw_annotation(figure, annotation, frequency=None, time=None):
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


@app.callback(
    [
        Output('graph-store', 'data'),
        Output('metadata-store', 'data'),
        Output('annotations-store', 'data'),
    ],
    [
        Input('filename', 'filename'),
        Input('filename', 'contents'),
        Input('fft-size', 'value'),
        Input('rf-freq', 'on'),
        Input('do-analysis', 'on'),
        Input('cursor', 'value'),
    ],
)
def generate_graphs(filename, contents, fft_size, rf_freq, analyze, cursor):
    """
    This callback generates three simple graphs from random data.
    """
    if not filename:
        # generate empty graphs when app loads
        return {k: go.Figure(data=[]) for k in ['spectrogram', 'frequency', 'time', 'iq']}, {}, []

    graphs = {}

    content_type, content_string = contents.split(',')
    d = io.BytesIO(base64.b64decode(content_string))
    arc = sigmf.SigMFArchiveReader(archive_buffer=d)
    sig = arc.sigmffile

    metadata = sig.get_global_info()
    if 'core:extensions' in metadata:
        del metadata['core:extensions']

    annotations =sig.get_annotations()

    samples = sig[:]

    sample_count = sig.shape[0]
    sample_rate = metadata['core:sample_rate']
    fc = sig.get_captures()[0]['core:frequency'] if rf_freq else None

    freq, spectrogram = utils.sigmf_to_spectrogram(samples, sample_rate, fft_size=fft_size, fc=fc)
    ytime = np.linspace(0.0, float(sample_count / sample_rate), num=sample_count // fft_size)

    graphs['spectrogram'] = px.imshow(
        spectrogram,
        x=freq,
        y=ytime,
        title=filename,
        aspect='auto',
        labels={
            'x': 'Frequency',
            'y': 'Time',
            'color': 'PSD',
        },
    )
    graphs['spectrogram'].update_layout(
        hovermode='x unified',
        xaxis_tickformat='~s',
        xaxis_ticksuffix='Hz',
        yaxis_tickformat='~s',
        yaxis_ticksuffix='s',
        coloraxis={
            'colorscale': 'viridis',
        },
    )

    graphs['spectrogram'].update_coloraxes(
        colorbar_tickformat='~s',
        colorbar_ticksuffix='dB',
    )

    for ann in annotations:
        draw_annotation(figure=graphs['spectrogram'], annotation=ann, frequency=freq, time=ytime)

    d = {}
    d['Frequency'], d['PSD'] = utils.samples_to_psd(samples[cursor[0]:cursor[1]], sample_rate, fc=fc)
    graphs['frequency'] = px.line(
        d,
        title=filename,
        x='Frequency',
        y='PSD',
    )

    if analyze:
        peaks = utils.get_peaks(d['Frequency'], d['PSD'], prominence=5)

        peaks['y'] = peaks['dBs'] - peaks['prominences'] / 2
        peaks['xerr'] = peaks['right freq'] - peaks['center freq']
        peaks['xerrminus'] = peaks['center freq'] - peaks['left freq']
        peaks['yerr'] = peaks['prominences'] / 2

        graphs['frequency'].add_traces(
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

        graphs['frequency'].add_traces(
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

    graphs['frequency'].update_layout(
        hovermode='x unified',
        xaxis_tickformat='~s',
        xaxis_ticksuffix='Hz',
        yaxis_tickformat='~s',
        yaxis_ticksuffix='dB',
    )

    graphs['iq'] = px.scatter(
        title=filename,
        x=np.real(samples[cursor[0]:cursor[1]]),
        y=np.imag(samples[cursor[0]:cursor[1]]),
    )

    return graphs, metadata, annotations


def main():
    parser = argparse.ArgumentParser('pyq-engine')
    parser.add_argument('--debug', default=False, action='store_true')
    options = parser.parse_args()
    app.run(debug=options.debug, host='0.0.0.0')
