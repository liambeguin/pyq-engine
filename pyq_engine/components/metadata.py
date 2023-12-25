from dash import callback, html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

metadata = html.Div(
    [
        dcc.Store(id='metadata-store'),
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
        dbc.Modal(
            [
                dbc.ModalHeader(dbc.ModalTitle('Metadata')),
                dbc.ModalBody(id='metadata'),
            ],
            id="metadata-modal",
            size="xl",
            is_open=False,
        ),
    ],
)


@callback(
    Output("metadata-modal", "is_open"),
    [Input("metadata-button", "n_clicks")],
    [State("metadata-modal", "is_open")],
)
def show_metadata_modal(n, is_open):
    if n:
        return not is_open
    return is_open

@callback(
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

