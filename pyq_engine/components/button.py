from dash import callback, Input, Output, State, MATCH
import dash_bootstrap_components as dbc


def OnOff(label, id, on):
    n = 1 if on else 0
    color = 'primary' if on else 'secondary'

    return dbc.Button(
        children=label,
        id={
            'type': 'pyq-engine-onoff-button',
            'id': id,
        },
        className="me-1",
        color="primary",
        n_clicks=n,
        style={
            'width': '100%',
            'margin-bottom': '10px',
        },
    )

@callback(
    Output(dict(id=MATCH, type='pyq-engine-onoff-button'), "color"),
    Input(dict(id=MATCH, type='pyq-engine-onoff-button'), "n_clicks"),
)
def toggle_on_offbutton(n_clicks):
    if n_clicks % 2:
        return 'primary'
    else:
        return 'secondary'
