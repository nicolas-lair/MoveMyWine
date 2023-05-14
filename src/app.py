from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc

from stef import Stef
from geodis import Geodis
from dbschenker import DBSchenker

from departement import DEPARTMENTS_TO_CODE
from app_constant import Id
from constant import N_EXPEDITION

import comparison_tab as comp_tab

transporter_dict = {
    Stef.name: Stef(),
    Geodis.name: Geodis(),
    DBSchenker.name: DBSchenker()
}

app = Dash(__name__, title="MoveMyWine",
           external_stylesheets=[dbc.themes.BOOTSTRAP],
           suppress_callback_exceptions=True)
server = app.server

transporter_dropdown = html.Div(
    [
        html.H4("Transporteur"),
        html.Label("Choix du transporteur"),
        dcc.Dropdown(
            list(transporter_dict.keys()),
            Stef.name,
            id=Id.transporter_dropdown,
            clearable=False
        )
    ]
)

# destination_dropdown = html.Div(
#     [
#         html.H3("Destination"),
#         html.Label("Choix du département de destination", htmlFor="department-dropdown"),
#         dcc.Dropdown(DEPARTMENTS_TO_CODE, '75', id="department-dropdown"),
#     ]
# )

destination_dropdown = html.Div(
    [
        dbc.Col(
            [
                html.H4("Origine / Destination"),
                dbc.Row(
                    [
                        html.Label("Origine"),
                        html.Br(),
                        dcc.Dropdown(DEPARTMENTS_TO_CODE, '49', id=Id.origin_dropdown, disabled=True)
                    ]
                ),
                dbc.Row(
                    [
                        html.Label("Destination"),
                        html.Br(),
                        dcc.Dropdown(DEPARTMENTS_TO_CODE, '75', id=Id.destination_dropdown)
                    ]
                )
            ]
        )
    ]
)

quantity_selector = html.Div(
    [
        html.H4("Quantités"),
        dbc.Row([dbc.Col([html.Label("Nombre de bouteilles", htmlFor="bottles-selector"),
                          html.Br(),
                          dcc.Input(id=Id.bottles_selector, type='number', min=1, max=2000, step=1)]),
                 ]
                )
    ]
)

n_expedition_slider = html.Div(
    [
        dbc.Row([dbc.Col([html.Label("Nombre d'expéditions par mois"),
                          html.Br(),
                          dcc.Slider(id=Id.n_expedition_slider, min=1, max=15, step=1,
                                     value=N_EXPEDITION)]),
                 ]
                )
    ]
)

# total_cost = dbc.Card(dcc.Graph(id="total-cost-graph", figure=px.scatter(title="figure title")), className="mt-2")
# cost_by_bottle = dbc.Card(dcc.Graph(id="cost-by-bottle-graph", figure=px.scatter(title="figure title")),
#                           className="mt-2")

app.layout = dbc.Container(
    [
        html.H1("Move My Wine", className="text-center"),
        html.P("Cette application permet de faire des comparaison de prix sur les transporteurs",
               className="text-center"),
        dcc.Tabs(id="tabs-example-graph", value='tab-1-example-graph', children=[
            dcc.Tab(label='Comparaison par transporteur', value='tab-1-transporter-comparison'),
            dcc.Tab(label='Calculateur de coût', value='tab-2-cost-calculator'),
        ]),
        html.Div(id='tabs-content-example-graph'),
    ],
    fluid=True,
)
total_cost, cost_by_bottle, update_cost = comp_tab.build_graphs_and_callbacks(app, transporter_dict)
transporter_comparison_layout = html.Div([
    dbc.Row([
        dbc.Col([
            comp_tab.build_transporter_dropdown(transporter_dict),
            n_expedition_slider
        ]),
        dbc.Col(destination_dropdown),
        dbc.Col(comp_tab.build_params_selector(app, transporter_dict))
    ]),
    dbc.Row(dbc.Col(cost_by_bottle)),
    dbc.Row(dbc.Col(total_cost)),
])

cost_calc_layout = html.Div([
    dbc.Row([dbc.Col(transporter_dropdown),
             # dbc.Col(quantity_selector),
             dbc.Col(destination_dropdown),
             # dbc.Col(params_selector)
             ]), dbc.Row(dbc.Col(total_cost)),
    dbc.Row(dbc.Col(cost_by_bottle)),
])

app.validation_layout = html.Div([
    app.layout,
    transporter_comparison_layout,
    cost_calc_layout,
    # params_selector,
])


@app.callback(Output('tabs-content-example-graph', 'children'),
              Input('tabs-example-graph', 'value'))
def render_content(tab):
    if tab == 'tab-1-transporter-comparison':
        return transporter_comparison_layout
    elif tab == 'tab-2-cost-calculator':
        return cost_calc_layout


# @callback(
#     Output('total-cost-graph', 'figure'),
#     Output('cost-by-bottle-graph', 'figure'),
#     Input(Id.transporter_dropdown, 'value'),
#     Input(Id.gas_price_input, 'value'),
#     Input(Id.gas_factor_input, 'value'),
#     Input(Id.destination_dropdown, 'value'),
# )
# def update_cost(transporter, gas_price, gas_factor, dept):
#     df = transporter_dict[transporter].get_total_cost(department=dept, gas_factor=1 + gas_factor / 100,
#                                                       gas_price=gas_price)
#     return px.bar(df), px.bar(df / df.index)

if __name__ == '__main__':
    app.run_server(debug=True)
