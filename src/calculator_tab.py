from dash import html, dcc

from app_constant import Id
from app_utils import build_component_id


def build_transporter_dropdown(transporter_dict):
    transporter_dropdown = html.Div(
        [
            html.H4("Transporteur"),
            html.Label("Choix du transporteur"),
            dcc.Dropdown(
                list(transporter_dict.keys()),
                id=build_component_id(Id.calculator_tab, Id.transporter_dropdown),
                clearable=False,
            ),
        ]
    )
    return transporter_dropdown


def build_params_selector(app, transporter_dict):
    params_selector, params_callbacks = zip(
        *[
            transporter.build_params_selector_object(
                app=app, location=Id.calculator_tab, hidden=True
            )
            for transporter in transporter_dict.values()
        ]
    )
    params_selector = html.Div([html.H4("Paramètres")] + list(params_selector))
    return params_selector, params_callbacks
