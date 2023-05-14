import pandas as pd
from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px

from departement import DEPARTMENTS_TO_CODE
from app_constant import Id
from app_utils import build_component_id


def build_transporter_dropdown(transporter_dict):
    transporter_dropdown = html.Div(
        [
            html.H4("Transporteur"),
            html.Label("Choix du transporteur"),
            dcc.Dropdown(
                options=list(transporter_dict.keys()),
                id=build_component_id(Id.comparison_tab, Id.transporter_dropdown), multi=True,
                value=tuple(transporter_dict.keys())
            )
        ]
    )
    return transporter_dropdown


def build_params_selector(app, transporter_dict):
    params_selector, _ = zip(*[
        transporter.build_params_selector_object(app=app, location=Id.comparison_tab, hidden=False) for transporter in
        transporter_dict.values()]
                             )
    params_selector = html.Div([html.H4("Paramètres")] + list(params_selector))
    return params_selector


def build_graphs_and_callbacks(app, transporter_dict):
    total_cost_id = build_component_id(Id.comparison_tab, Id.total_cost_graph)
    total_cost = dbc.Card(dcc.Graph(id=total_cost_id,
                                    figure=px.scatter(title="Coût d'une expédition")),
                          className="mt-2")

    cost_by_bottle_id = build_component_id(Id.comparison_tab, Id.cost_by_bottle_graph)
    cost_by_bottle = dbc.Card(dcc.Graph(id=cost_by_bottle_id,
                                        figure=px.scatter(title="Coût par bouteille")),
                              className="mt-2")

    @app.callback(
        Output(total_cost_id, 'figure'),
        Output(cost_by_bottle_id, 'figure'),
        Input(build_component_id(Id.comparison_tab, Id.transporter_dropdown), 'value'),
        Input(build_component_id(Id.comparison_tab, Id.gas_price_input), 'value'),
        Input(build_component_id(Id.comparison_tab, Id.gas_factor_input), 'value'),
        Input(Id.destination_dropdown, 'value'),
        Input(Id.n_expedition_slider, 'value'),
    )
    def update_cost(selected_transporter, gas_price, gas_factor, dept, n_expedition):
        all_df = []
        for transporter in selected_transporter:
            df = transporter_dict[transporter].get_total_cost(department=dept, gas_factor=1 + gas_factor / 100,
                                                              gas_price=gas_price, n_client=n_expedition)
            df = pd.DataFrame(df)
            df["Transporteur"] = transporter
            all_df.append(df)
        all_df = pd.concat(all_df)
        all_df = all_df.rename(columns={dept: "Coût"})
        all_df["Coût par bouteille"] = all_df["Coût"] / all_df.index
        # TODO Add range options
        all_df = all_df[all_df.index <= 150]
        return (px.bar(all_df, y="Coût", color="Transporteur", barmode='group', ),
                px.bar(all_df, y="Coût par bouteille", color="Transporteur", barmode='group', ))

    return total_cost, cost_by_bottle, update_cost
