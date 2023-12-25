from dash import callback, dcc, html, Input, Output, State
import dash_daq as daq
import dash_bootstrap_components as dbc

from pyq_engine import utils


upload = html.Div(
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
)


def fft_size(options):
    return html.Div(
        [
            dbc.Label('FFT Size'),
            dcc.Dropdown(
                id='fft-size',
                options=options,
                value=1024,
            ),
        ],
    )

switches = html.Div(
    [
        daq.BooleanSwitch(label='RF Frequencies', id='rf-freq', on=True),
        daq.BooleanSwitch(label='Analysis', id='do-analysis', on=True),
    ],
)

freq_cursor = html.Div(
    [
        dbc.Label('Frequency Cursor'),
        dcc.RangeSlider(
            0, 50,
            value=[10, 20],
            marks=None,
            allowCross=False,
            tooltip={'placement': 'bottom', 'always_visible': True},
            id='cursor',
        ),
    ],
)


@callback(
    [
        Output("cursor", "max"),
        Output("cursor", "value"),
    ],
    Input('filename', 'filename'),
    Input('filename', 'contents'),
)
def update_freq_cursor(filename, contents):
    count = 50

    if filename:
        sig = utils.load_sigmf_contents(contents)
        count = sig.shape[0]

    return count, [0, count]
