import argparse
import logging

from pathlib import Path

import dash_ag_grid as dag
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import sigmf

from dash import Dash, Input, Output, callback, dcc, html

from pyq_engine import utils

logger = logging.getLogger(__name__)


def flatten_sigmf(filename):
    sig = sigmf.sigmffile.fromfile(filename)
    m = sig._metadata

    if len(m['captures']) > 1:
           print('warning: many captures in sigmf')

    m['filename'] = filename.as_posix()
    m['captures.0'] = m['captures'][0]
    del(m['captures'])

    return pd.json_normalize(m, meta_prefix=True)



def main():
    df = pd.DataFrame()

    @callback(
        Output('graph', 'figure'),
        Input('grid', 'selectedRows'),
        prevent_initial_call=True,
    )
    def update_graph(selected_rows):
        fig = go.Figure()
        rf_freq = True
        nperseg = 1024

        for i in selected_rows:
            path = Path(i['filename'])
            sig = sigmf.sigmffile.fromfile(path)
            metadata = sig._metadata

            sample_rate = metadata['global']['core:sample_rate']
            fc = metadata['captures'][0]['core:frequency'] if rf_freq else 0
            samples = sig.read_samples()

            f, psd = utils.samples_to_psd(samples, sample_rate, fc=fc, nperseg=nperseg)
            fig.add_trace(go.Scatter(
                x=f,
                y=psd,
                name='='.join(['row_id', str(i['index'])]),
            ))

        fig.update_traces(
            # mode='markers+lines',
        )
        fig.update_layout(
            # title='',
            xaxis_title='Frequency',
            yaxis_title='PSD',
            hovermode='x unified',
            xaxis_exponentformat='SI',
            xaxis_ticksuffix='Hz',
            yaxis_exponentformat='SI',
            yaxis_ticksuffix='dB',
        )

        return fig

    parser = argparse.ArgumentParser('pyq-explorer')
    parser.add_argument('dir', type=Path, default='.')
    options = parser.parse_args()

    if not options.dir.exists():
        logger.critical('input directory doesn\'t exist')
        return

    app = Dash(
        __name__,
        title='PYQ-Explorer',
        external_stylesheets=[dbc.themes.BOOTSTRAP],
    )

    for f in options.dir.glob('**/*.sigmf-meta'):
        try:
            df = pd.concat([df, flatten_sigmf(f)])
        except Exception as e:
            logger.warning(f'skipping {f}: {e}')

    # reset row number, and add index column, for graphs
    df = df.replace({np.nan: None}).reset_index(drop=True).reset_index()

    columnDefs = [
        {'headerName': 'Row ID', 'valueGetter': {'function': 'params.data.index'}, 'headerCheckboxSelection': True },
        {'field': 'filename', 'initialHide': True },
        {
            'headerName': 'Global.Core',
            'children': [
                {'field': 'global.core:author', 'headerName': 'Author', 'initialHide': True},
                {'field': 'global.core:datatype', 'headerName': 'Data Type', 'initialHide': True},
                {'field': 'global.core:sample_rate', 'headerName': 'Sample Rate'},
                {'field': 'global.core:version', 'headerName': 'Version', 'initialHide': True},
            ],
        },
        {
            'headerName': 'Global.HE360',
            'children': [
                {'field': 'global.he360:rx_name', 'headerName': 'RX Name'},
                {'field': 'global.he360:rx_slot', 'headerName': 'RX Slot'},
                {'field': 'global.he360:rx_channel', 'headerName': 'RX Channel'},
                {'field': 'global.he360:rx_gain', 'headerName': 'RX Gain'},
                {'field': 'global.he360:rx_lo_offset', 'headerName': 'RX LO Offset'},
                {'field': 'global.he360:rx_master_clock', 'headerName': 'RX Master Clock'},
                {'field': 'global.he360:rx_antenna_feed', 'headerName': 'RX Antenna Feed'},
                {'field': 'global.he360:analog_bandwidth', 'headerName': 'Analog Bandwidth'},
                {'field': 'global.he360:sw_version', 'headerName': 'SW Version'},
            ],
        },
        {
            'headerName': 'Captures[0]',
            'children': [
                {'field': 'captures.0.core:datetime', 'headerName': 'Datetime'},
                {'field': 'captures.0.core:frequency', 'headerName': 'Frequency'},
                {'field': 'captures.0.core:sample_start', 'headerName': 'Sample Start', 'initialHide': True},
                {'field': 'captures.0.he360:timesource', 'headerName': 'HE360 Timesource'},
            ],
        },
    ]

    grid_component = html.Div([
        dag.AgGrid(
            id='grid',
            columnDefs=columnDefs,
            rowData=df.to_dict('records'),
            dashGridOptions={
                'rowSelection': 'multiple',
                'rowMultiSelectWithClick': True,
                'suppressFieldDotNotation': True,
            },
            columnSize='responsiveSizeToFit',
            defaultColDef={
                'resizable': True,
                'sortable': True,
                'filter': True,
            },
            suppressDragLeaveHidesColumns=False,
            style={'width': '100vw', 'height': '80vh'},
        ),
    ])

    app.layout = html.Div(
        [
            html.H1('PYQ Explorer'),
            html.Hr(),
            dbc.Tabs(
                [
                    dbc.Tab(
                        label='Table',
                        tab_id='table',
                        children=grid_component,
                    ),
                    dbc.Tab(
                        label='Frequency',
                        tab_id='frequency',
                        children=dcc.Graph(
                            id='graph',
                            style={'width': '100vw', 'height': '80vh'},
                        ),
                    ),
                ],
                id='tabs',
                active_tab='table',
            ),
        ],
    )

    app.run(debug=True, host='0.0.0.0')
