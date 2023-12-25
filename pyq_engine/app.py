import argparse
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output, State

from pyq_engine import utils
from pyq_engine import components


def main():
    parser = argparse.ArgumentParser('pyq-engine')
    parser.add_argument('--debug', default=False, action='store_true')
    parser.add_argument('--default-tab', default='spectrogram', choices=['spectrogram', 'frequency', 'iq'])
    parser.add_argument('--fft-size-options', default=[2**i for i in range(5, 15)])
    options = parser.parse_args()

    app = Dash(
        __name__,
        title='PYQ-Engine',
        external_stylesheets=[dbc.themes.BOOTSTRAP],
    )

    controls = dbc.Card(
        [
            components.controls.upload,
            html.Hr(),
            components.controls.fft_size(options.fft_size_options),
            html.Hr(),
            components.controls.switches,
            html.Hr(),
            components.controls.sample_slicer,
            html.Hr(),
            components.metadata,
            components.annotations,
        ],
        body=True,
    )

    app.layout = html.Div(
        [
            html.H1('PYQ Engine'),
            html.Hr(),
            dbc.Row(
                [
                    dbc.Col(controls, class_name='m-0 col-2'),
                    dbc.Col(components.tabs(options.default_tab), class_name='m-0 col-10'),
                ],
                align='top',
            ),
        ],
    )

    app.run(debug=options.debug, host='0.0.0.0')
