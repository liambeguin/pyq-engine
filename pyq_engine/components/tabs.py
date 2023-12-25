import plotly.graph_objs as go

from dash import callback, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

from pyq_engine import utils
from pyq_engine.components import plot


def tabs(default='spectrogram'):
    return html.Div(
    [
        dcc.Store(id='graph-store'),
        dbc.Tabs(
            [
                dbc.Tab(label='Spectrogram', tab_id='spectrogram'),
                dbc.Tab(label='Frequency', tab_id='frequency'),
                dbc.Tab(label='IQ Plot', tab_id='iq'),
            ],
            id='tabs',
            active_tab=default,
        ),
        html.Div(id="tab-content"),
    ],
)


@callback(
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


@callback(
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

    sigmf = utils.load_sigmf_contents(contents)
    annotations = sigmf.get_annotations()

    metadata = sigmf.get_global_info()
    if 'core:extensions' in metadata:
        del metadata['core:extensions']

    samples = sigmf[cursor[0]:cursor[1]]
    fc = sigmf.get_captures()[0]['core:frequency'] if rf_freq else None

    graphs = {}
    graphs['spectrogram'] = plot.spectrogram(samples, sigmf, fc=fc, fft_size=fft_size, title=filename)
    graphs['frequency'] = plot.frequencies(samples, sigmf, fc=fc, title=filename, analyze=analyze)
    graphs['iq'] = plot.IQ(samples, title=filename)

    return graphs, metadata, annotations
