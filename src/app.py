from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
import dash_daq as daq

from stef.stef import Stef

from departement import DEPARTMENTS_TO_CODE

transporter_dict = {
    "Stef": Stef(),
    # "DHL"
}

app = Dash(__name__, title="MoveMyWine",
           external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

transporter_dropdown = html.Div(
    [
        html.H3("Transporteur"),
        html.Label("Choix du transporteur", htmlFor="transporter-dropdown"),
        dcc.Dropdown(list(transporter_dict.keys()), 'Stef', id="transporter-dropdown", clearable=False),
    ]
)

destination_dropdown = html.Div(
    [
        html.H3("Destination"),
        html.Label("Choix du département de destination", htmlFor="department-dropdown"),
        dcc.Dropdown(DEPARTMENTS_TO_CODE, '75', id="department-dropdown"),
    ]
)

quantity_selector = html.Div(
    [
        html.H3("Quantités"),
        dbc.Row([dbc.Col([html.Label("Nombre de bouteilles", htmlFor="bottles-selector"),
                          html.Br(),
                          dcc.Input(id='bottles', type='number', min=1, max=600, step=1)]),

                 dbc.Col([html.Label("Nombre de palettes", htmlFor="palet-selector"),
                          html.Br(),
                          dcc.Input(id='palets', type='number', min=1, max=20, step=1)])])
    ]
)

params_selector = html.Div(
    [
        html.H3("Paramètres"),
        html.Label(["Prix du Gaz CNR, disponible ", html.A('ici', href='https://www.cnr.fr/espaces/13/indicateurs/41', target="_blank")]),
        daq.NumericInput(id="gas-modulation-input",
                         min=0.981, #TODO make params
                         max=2.3307, #TODO make params
                         value=1.409,
                         labelPosition="top",
                         size=150
                         ),
    ])
total_cost = dbc.Card(dcc.Graph(id="total-cost-graph", figure=px.scatter(title="figure title")), className="mt-2")
cost_by_bottle = dbc.Card(dcc.Graph(id="cost-by-bottle-graph", figure=px.scatter(title="figure title")),
                          className="mt-2")

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

transporter_comparison_layout = html.Div([
    html.H3('Comparaison par transporteur'),
    dbc.Row([dbc.Col(transporter_dropdown),
             # dbc.Col(quantity_selector),
             dbc.Col(destination_dropdown),
             dbc.Col(params_selector)
             ]),
    dbc.Row(dbc.Col(total_cost)),
    dbc.Row(dbc.Col(cost_by_bottle)),
])

cost_calc_layout = html.Div([
    html.H3('Calculateur de coût'),
    dbc.Row([dbc.Col(transporter_dropdown),
             # dbc.Col(quantity_selector),
             dbc.Col(destination_dropdown),
             dbc.Col(params_selector)
             ]),    dbc.Row(dbc.Col(total_cost)),
    dbc.Row(dbc.Col(cost_by_bottle)),
])

app.validation_layout = html.Div([
    app.layout,
    transporter_comparison_layout,
    cost_calc_layout

])


@app.callback(Output('tabs-content-example-graph', 'children'),
              Input('tabs-example-graph', 'value'))
def render_content(tab):
    if tab == 'tab-1-transporter-comparison':
        return transporter_comparison_layout
    elif tab == 'tab-2-cost-calculator':
        return cost_calc_layout


@callback(
    Output('total-cost-graph', 'figure'),
    Input('transporter-dropdown', 'value'),
    Input('gas-modulation-input', 'value'),
    Input('department-dropdown', 'value')
)
def update_total_cost(transporter, gas_price, dept):
    df = transporter_dict[transporter].get_total_cost(department=dept, gas_price=gas_price)
    return px.bar(df)


@callback(
    Output('cost-by-bottle-graph', 'figure'),
    Input('transporter-dropdown', 'value'),
    Input('gas-modulation-input', 'value'),
    Input('department-dropdown', 'value')
)
def update_cost_by_bottle(transporter, gas_price, dept):
    df = transporter_dict[transporter].get_cost_by_bottle(department=dept, gas_price=gas_price)
    return px.bar(df)


if __name__ == '__main__':
    app.run_server(debug=True)
