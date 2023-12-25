from dash import callback, dcc, html, Input, Output, State
import dash_bootstrap_components as dbc


annotations = html.Div(
    [
        dcc.Store(id='annotations-store'),
        dbc.Button(
            [
                "Annotations",
                dbc.Badge(id='annotations-count', color='danger', className="ms-1"),
            ],
            id="annotations-button",
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
                dbc.ModalHeader(dbc.ModalTitle('Annotations')),
                dbc.ModalBody(id='annotations'),
            ],
            id="annotations-modal",
            size="xl",
            is_open=False,
        ),
    ],
)


@callback(
    Output("annotations-modal", "is_open"),
    [Input("annotations-button", "n_clicks")],
    [State("annotations-modal", "is_open")],
)
def show_annotations_modal(n, is_open):
    if n:
        return not is_open
    return is_open


@callback(
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
