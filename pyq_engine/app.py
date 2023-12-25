import argparse
import dash_bootstrap_components as dbc
from dash import Dash, dcc, html, Input, Output, State

from pyq_engine import utils
from pyq_engine import components


app = Dash(
    __name__,
    title='PYQ-Engine',
    external_stylesheets=[dbc.themes.BOOTSTRAP],
)

controls = dbc.Card(
    [
        components.controls.upload,
        html.Hr(),
        components.controls.fft_size,
        html.Hr(),
        components.controls.switches,
        html.Hr(),
        components.controls.freq_cursor,
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
                dbc.Col(components.tabs, class_name='m-0 col-10'),
            ],
            align='top',
        ),
    ],
)


def main():
    parser = argparse.ArgumentParser('pyq-engine')
    parser.add_argument('--debug', default=False, action='store_true')
    options = parser.parse_args()

    app.run(debug=options.debug, host='0.0.0.0')
