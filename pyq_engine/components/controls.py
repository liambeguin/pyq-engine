from dash import callback, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc

from pyq_engine import utils
from pyq_engine.components import warning, button


upload = html.Div(
    [
        dcc.Store(id='samples-store'),
        dcc.Store(id='metadata-store'),
        dcc.Upload(
            id='filename',
            children=html.Div([
                html.A('Upload Archive')
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
        button.OnOff(label='RF Frequencies', id='rf-freq', on=True),
        button.OnOff(label='Enable Analysis', id='do-analysis', on=True),
    ],
)

fullscreen = html.Div(
    [
        dbc.Button(
            'Fullscreen', id='open-fs',
            style={
                'width': '100%',
                'margin-bottom': '10px',
            },
        ),
        dbc.Modal(id='modal-fs', fullscreen=True),
    ],
)

@callback(
    Output("modal-fs", "is_open"),
    Input("open-fs", "n_clicks"),
    State("modal-fs", "is_open"),
)
def toggle_modal(n, is_open):
    if n:
        return not is_open
    return is_open


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
        Output('samples-store', 'data'),
        Output('metadata-store', 'data'),
        Output('warning-modal', 'is_open'),
        Output('warning-modal', 'children'),
    ],
    [
        Input('filename', 'filename'),
        Input('filename', 'contents'),
    ],
)
def load_file(filename, contents):
    limit = int(1e6)
    w = None
    if not filename:
        return None, None, False, []

    try:
        sigmf = utils.load_sigmf_contents(contents)
    except Exception as e:
        return (
            None, None, True,
            warning.warn('SigMF Error', 'Unable to open SigMFArchive: ' + str(e)),
        )

    samples = sigmf[:]
    if samples.shape[0] > limit:
        w = warning.warn('SigMF Warning', f'Truncating samples for performance {samples.shape[0]} -> ({limit},)')
        samples = samples[:limit]

    return (
        utils.serialize_samples(samples),
        sigmf._metadata,
        w is not None, w,
    )


@callback(
    [
        Output("cursor", "max"),
        Output("cursor", "value"),
    ],
    Input('samples-store', 'data'),
)
def update_sample_slice(samples):
    if samples is None:
        return 5000, [0, 5000]

    count = utils.deserialize_samples(samples).shape[0]

    return count, [0, count]
