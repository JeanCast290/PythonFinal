import dash
from dash import dcc, html, dash_table
import pandas as pd
import yfinance as yf
import plotly.express as px
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output
import datetime 

# Inicializar la aplicación Dash con Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

# Exponer el servidor para que Gunicorn pueda encontrarlo
server = app.server

app.title = "Dashboard Financiero"

# Lista de acciones
stocks = ["PG", "KO", "PEP", "MMM", "HON", "CAT"]

# Definir el rango de los últimos 5 años
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=5*365)

# Descargar datos de precios ajustados limitados a los últimos 5 años
historical_data = yf.download(stocks, start=start_date, end=end_date)["Adj Close"]
print("Datos descargados:", historical_data.head())  # Debugging

# Calcular los retornos diarios
returns_data = historical_data.pct_change().dropna()
print("Datos de retornos:", returns_data.head())  # Debugging

# Lista de variables para el análisis
sales_list = ["Precio de Cierre", "Retornos Diarios"]

# Layout de la aplicación
app.layout = html.Div([
    html.H1("Dashboard Financiero", style={"textAlign": "center"}),

    html.Div([
        html.Div([
            dcc.Dropdown(
                id="stockdropdown", 
                value=stocks, 
                clearable=False, 
                multi=True,
                options=[{"label": x, "value": x} for x in stocks]
            ),
        ], className="six columns", style={"width": "50%"}),

        html.Div([
            dcc.Dropdown(
                id="metricdropdown", 
                value="Precio de Cierre", 
                clearable=False,
                options=[{"label": x, "value": x} for x in sales_list]
            ),
        ], className="six columns", style={"width": "50%"})
    ], className="row"),

    html.Div([dcc.Graph(id="bar", figure={})]),
    html.Div([dcc.Graph(id="boxplot", figure={})]),

    html.Div(id="table-container_1", style={"marginBottom": "15px", "marginTop": "0px"})
])

# Callback para actualizar los gráficos y la tabla
@app.callback(
    [Output("bar", "figure"), Output("boxplot", "figure"), Output("table-container_1", "children")],
    [Input("stockdropdown", "value"), Input("metricdropdown", "value")]
)
def display_value(selected_stock, selected_metric):
    start_date = historical_data.index.min()
    end_date = historical_data.index.max()

    if len(selected_stock) == 0:
        selected_stock = stocks

    if selected_metric == "Precio de Cierre":
        dfv_fltrd = historical_data.loc[start_date:end_date, selected_stock].reset_index()
        y_label = "Precio de Cierre"
    else:
        dfv_fltrd = returns_data.loc[start_date:end_date, selected_stock].reset_index()
        y_label = "Retornos Diarios"

    if dfv_fltrd.empty:
        return (
            px.scatter(title="No hay datos disponibles."),
            px.scatter(title="No hay datos disponibles."),
            html.Div("No hay datos disponibles para mostrar en la tabla.")
        )

    fig = px.line(dfv_fltrd.melt(id_vars="Date", var_name="Company", value_name=y_label),
                  x="Date", y=y_label, color="Company",
                  title=f"{selected_metric} para {', '.join(selected_stock)}",
                  width=800, height=400)

    fig2 = px.box(dfv_fltrd.melt(id_vars="Date", var_name="Company", value_name=y_label),
                  x="Company", y=y_label, color="Company",
                  title=f"Distribución de {selected_metric}",
                  width=800, height=400)

    df_reshaped = dfv_fltrd.set_index("Date")
    df_reshaped2 = df_reshaped[selected_stock].reset_index()

    data_table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in df_reshaped2.columns],
        data=df_reshaped2.to_dict("records"),
        export_format="csv",
        fill_width=True,
        style_cell={"font-size": "12px"},
        style_table={"maxWidth": 800},
        style_header={"backgroundColor": "blue", "color": "white"},
        style_data_conditional=[{"backgroundColor": "white", "color": "black"}]
    )

    return fig, fig2, data_table

if __name__ == "__main__":
    app.run_server(debug=False, host="0.0.0.0", port=8053)
