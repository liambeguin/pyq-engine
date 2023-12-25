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

sample_slicer = html.Div(
    [
        dbc.Label('Sample Slice'),
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
    if filename is None:
        return 5000, [0, 5000]

    sig = utils.load_sigmf_contents(contents)
    count = sig.shape[0]

    return count, [0, count]
