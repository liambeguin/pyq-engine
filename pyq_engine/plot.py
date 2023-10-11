import dash_bootstrap_components as dbc
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


def samples_to_psd(samples, sample_rate, lo=None):
    samples = samples * np.hamming(len(samples))
    psd = 10 * np.log10(np.abs(np.fft.fftshift(np.fft.fft(samples)))**2)
    f = np.linspace(sample_rate/-2, sample_rate/2, len(psd))

    if lo is not None:
        f += lo

    return f, psd


def sigmf_to_spectrogram(samples, sample_rate, fft_size=1024, lo=None):
    num_rows = len(samples) // fft_size # // is an integer division which rounds down
    spectrogram = np.zeros((num_rows, fft_size))

    for i in range(num_rows):
        start = i * fft_size
        stop = (i + 1) * fft_size

        f, spectrogram[i,:] = samples_to_psd(samples[start:stop], sample_rate, lo)

    return f, spectrogram



fft_size_options = [2**i for i in range(5, 15)]
app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

controls = dbc.Card(
    [
        html.Div(
            [
                dbc.Label('Click to select SigMF archive file'),
                dcc.Upload(
                    id='filename',
                    children=html.Div([
                        html.A('Select Files')
                    ]),
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
                dbc.Label('RF Frequencies'),
                daq.BooleanSwitch(id='rf-freq', on=True),
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
        dbc.Button(
            "Toggle Metadata",
            id="metadata-button",
            className="me-1",
            color="primary",
            n_clicks=0,
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

    return count, [0, count // 10]


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
        Input('cursor', 'value'),
    ],
)
def generate_graphs(filename, contents, fft_size, rf_freq, cursor):
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
    annotations =sig.get_annotations()

    samples = sig[:]
    sample_count = sig.shape[0]
    sample_rate = metadata['core:sample_rate']
    lo = sig.get_captures()[0]['core:frequency'] if rf_freq else None

    freq, spectrogram = sigmf_to_spectrogram(samples, sample_rate, fft_size=fft_size, lo=lo)
    ytime = np.linspace(0.0, float(sample_count / sample_rate), num=sample_count // fft_size)

    graphs['spectrogram'] = px.imshow(
        spectrogram,
        x=freq,
        y=ytime,
        title=filename,
        aspect='auto',
        labels={
            'x': 'Frequency [Hz]',
            'y': 'Time',
            'color': 'PSD [dB]',
        },
    )
    graphs['spectrogram'].update_layout(
        hovermode='x unified',
        coloraxis={
            'colorscale': 'viridis',
        },
    )

    d = {}
    d['Frequency [Hz]'], d['PSD [dB]'] = samples_to_psd(samples[cursor[0]:cursor[1]], sample_rate, lo=lo)
    graphs['frequency'] = px.line(
        d,
        title=filename,
        x='Frequency [Hz]',
        y='PSD [dB]',
    )
    graphs['frequency'].update_layout(hovermode='x unified')

    graphs['iq'] = px.scatter(
        title=filename,
        x=np.real(samples[cursor[0]:cursor[1]]),
        y=np.imag(samples[cursor[0]:cursor[1]]),
    )

    return graphs, metadata, annotations


app.run_server(debug=True)
