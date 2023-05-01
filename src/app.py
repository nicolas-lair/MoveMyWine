from dash import Dash, html, dcc, callback, Output, Input
import dash_bootstrap_components as dbc
import plotly.express as px
from stef.stef import Stef

transporter_dict = {
    "Stef": Stef(),
    # "DHL"
}

app = Dash(__name__, title="MoveMyWine", external_stylesheets=[dbc.themes.BOOTSTRAP])

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
        dcc.Dropdown(list(range(95)), 75, id="department-dropdown"),
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

total_cost = dbc.Card(dcc.Graph(id="total-cost-graph", figure=px.scatter(title="figure title")), className="mt-2")
cost_by_bottle = dbc.Card(dcc.Graph(id="cost-by-bottle-graph", figure=px.scatter(title="figure title")), className="mt-2")

app.layout = dbc.Container(
    [
        html.H1("Move My Wine", className="text-center"),
        html.P("Cette application permet de faire des comparaison de prix sur les transporteurs", className="text-center"),
        dbc.Row([dbc.Col(transporter_dropdown), dbc.Col(quantity_selector), dbc.Col(destination_dropdown)]),
        dbc.Row(dbc.Col(total_cost)),
        dbc.Row(dbc.Col(cost_by_bottle)),
    ],
    fluid=True,
)



@callback(
    Output('total-cost-graph', 'figure'),
    Input('transporter-dropdown', 'value'),
    Input('department-dropdown', 'value')
)
def update_total_cost(transporter, value):
    df = transporter_dict[transporter].get_total_cost(department=value)
    return px.line(df)

@callback(
    Output('cost-by-bottle-graph', 'figure'),
    Input('transporter-dropdown', 'value'),
    Input('department-dropdown', 'value')
)
def update_cost_by_bottle(transporter, value):
    df = transporter_dict[transporter].get_cost_by_bottle(department=value)
    return px.line(df)


if __name__ == '__main__':
    app.run_server(debug=True)
