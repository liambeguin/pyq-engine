import plotly.graph_objs as go

from dash import callback, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

from pyq_engine import utils
from pyq_engine.components import plot


def tabs(default='spectrogram'):
    return html.Div(
    [
        dbc.Tabs(
            [
                dbc.Tab(label='Spectrogram', tab_id='spectrogram'),
                dbc.Tab(label='Frequency', tab_id='frequency'),
                dbc.Tab(label='Time', tab_id='time'),
                dbc.Tab(label='IQ Plot', tab_id='iq'),
            ],
            id='tabs',
            active_tab=default,
        ),
        dbc.Spinner(
            [
                dcc.Store(id='graph-store'),
                html.Div(id="tab-content"),
            ],
            color='primary',
        ),
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
        Output('graph-store', 'data'),
    [
        Input('filename', 'filename'),
        Input('samples-store', 'data'),
        Input('metadata-store', 'data'),
        Input('fft-size', 'value'),
        Input(dict(type='pyq-engine-onoff-button', id='rf-freq'), 'n_clicks'),
        Input(dict(type='pyq-engine-onoff-button', id='do-analysis'), 'n_clicks'),
        Input('cursor', 'value'),
    ],
)
def generate_graphs(filename, store, metadata, fft_size, rf_freq, analyze, cursor):
    """
    This callback generates three simple graphs from random data.
    """
    if not store:
        # generate empty graphs when app loads
        return {k: go.Figure(data=[]) for k in ['spectrogram', 'frequency', 'time', 'iq']}

    samples = utils.deserialize_samples(store)
    samples = samples[cursor[0]:cursor[1]]

    fc = metadata['captures'][0]['core:frequency'] if rf_freq % 2 else 0

    graphs = {}
    graphs['spectrogram'] = plot.spectrogram(samples, metadata, fc=fc, fft_size=fft_size, title=filename)
    graphs['frequency'] = plot.frequencies(samples, metadata, fc=fc, title=filename, analyze=analyze % 2)
    graphs['time'] = plot.time(samples, metadata, title=filename)
    graphs['iq'] = plot.IQ(samples, title=filename)

    return graphs
