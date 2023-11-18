import pandas as pd
from dash import html, dcc, callback, Output, Input, State
import dash_bootstrap_components as dbc
import plotly.express as px

from app_constant import Id
from app_utils import build_component_id
from src.cost_calculator.constant import CostType


def build_transporter_dropdown(transporter_dict):
    transporter_dropdown = html.Div(
        [
            html.H4("Transporteur"),
            html.Label("Choix du transporteur"),
            dcc.Dropdown(
                options=list(transporter_dict.keys()),
                id=build_component_id(Id.comparison_tab, Id.transporter_dropdown),
                multi=True,
                value=tuple(transporter_dict.keys()),
            ),
        ]
    )
    return transporter_dropdown


def build_params_selector(app, transporter_dict):
    params_selector, _ = zip(
        *[
            transporter.build_params_selector_object(
                app=app, location=Id.comparison_tab, hidden=False
            )
            for transporter in transporter_dict.values()
        ]
    )
    params_selector = html.Div([html.H4("Paramètres")] + list(params_selector))
    return params_selector


def build_graphs_and_callbacks(app, transporter_dict):
    total_cost_id = build_component_id(Id.comparison_tab, Id.total_cost_graph)
    total_cost = dbc.Card(
        dcc.Graph(id=total_cost_id, figure=px.scatter(title="Coût d'une expédition")),
        className="mt-2",
    )

    cost_by_bottle_id = build_component_id(Id.comparison_tab, Id.cost_by_bottle_graph)
    cost_by_bottle = dbc.Card(
        dcc.Graph(id=cost_by_bottle_id, figure=px.scatter(title="Coût par bouteille")),
        className="mt-2",
    )

    best_transporter_id = build_component_id(Id.comparison_tab, Id.best_transporter)
    best_transporter = dbc.Card(
        dcc.Graph(
            id=best_transporter_id, figure=px.scatter(title="Meilleur transporteur")
        ),
        className="mt-2",
    )

    @app.callback(
        Output(total_cost_id, "figure"),
        Output(cost_by_bottle_id, "figure"),
        Output(best_transporter_id, "figure"),
        Output("data_df_id", "data"),
        Input(build_component_id(Id.comparison_tab, Id.transporter_dropdown), "value"),
        Input(build_component_id(Id.comparison_tab, Id.gas_price_input), "value"),
        Input(build_component_id(Id.comparison_tab, Id.gas_factor_input), "value"),
        Input(Id.destination_dropdown, "value"),
        Input(Id.n_expedition_slider, "value"),
    )
    def update_cost(selected_transporter, gas_price, gas_factor, dept, n_expedition):
        all_df = []
        for transporter in selected_transporter:
            print(f"Computing costs for {transporter}")
            df = transporter_dict[transporter].compute_cost_by_bottle(
                department=dept,
                gas_factor=1 + gas_factor / 100,
                gas_price=gas_price,
                n_expedition_by_month=n_expedition,
            )
            df = pd.DataFrame(df)
            df["Transporteur"] = transporter
            all_df.append(df)
        all_df = pd.concat(all_df)
        all_df = all_df.rename(columns={CostType.Total: "Coût"})
        all_df["Coût par bouteille"] = all_df["Coût"] / all_df.index
        # TODO Add range options
        all_df = all_df[all_df.index <= 198]
        return (
            px.bar(all_df, y="Coût", color="Transporteur", barmode="group"),
            px.bar(
                all_df, y="Coût par bouteille", color="Transporteur", barmode="group"
            ),
            px.bar(
                (
                    all_df.reset_index()
                    .sort_values(["index", "Coût"], ascending=True)
                    .drop_duplicates(subset=["index"], keep="first")
                    .set_index("index")
                ),
                y="Coût",
                color="Transporteur",
                category_orders={"Transporteur": list(transporter_dict.keys())},
            ),
            all_df.reset_index()
            .rename(columns={"index": "n_bottles"})
            .to_dict("records"),
        )

    @callback(
        Output(Id.best_transporter + "_copy", "content"),
        Input(Id.best_transporter + "_copy", "n_clicks"),
        State("data_df_id", "data"),
        prevent_initial_call=True,
    )
    def copy_best_transporter_table(_, data):
        dff = pd.DataFrame(data)
        dff = dff.sort_values(["n_bottles", "Coût"], ascending=True).drop_duplicates(
            subset=["n_bottles"], keep="first"
        )
        # See options for .to_csv() or .to_excel() or .to_string() in the  pandas documentation
        dff["Coût"] = dff["Coût"].round()
        return dff.to_csv(index=False)  # includes headers

    return (
        total_cost,
        cost_by_bottle,
        best_transporter,
        update_cost,
        copy_best_transporter_table,
    )
