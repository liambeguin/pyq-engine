from dash import html
import dash_bootstrap_components as dbc

modal = html.Div(
    [
        dbc.Modal(
            id="warning-modal",
            size="xl",
            is_open=False,
        ),
    ],
)


def warn(title, message):
    return [
        dbc.ModalHeader(dbc.ModalTitle(title)),
        dbc.ModalBody(message),
    ]
