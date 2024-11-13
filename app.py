# Inicializar la aplicación Dash con Bootstrap
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.title = "Dashboard Financiero"

# Lista de acciones
stocks = ["PG", "KO", "PEP", "MMM", "HON", "CAT"]

# Definir el rango de los últimos 5 años
end_date = datetime.datetime.now()
start_date = end_date - datetime.timedelta(days=5*365)

# Descargar datos de precios ajustados limitados a los últimos 5 años
historical_data = yf.download(stocks, start=start_date, end=end_date)["Adj Close"]

# Calcular los retornos diarios
returns_data = historical_data.pct_change().dropna()

# Lista de variables para el análisis
sales_list = ["Precio de Cierre", "Retornos Diarios"]

# Layout de la aplicación
app.layout = html.Div([
    html.H1("Dashboard Financiero", style={"textAlign": "center"}),

    # Fila con dropdowns para selección de acciones y métrica
    html.Div([
        html.Div([
            # Dropdown para seleccionar las empresas a visualizar
            dcc.Dropdown(
                id="stockdropdown", 
                value=stocks, 
                clearable=False, 
                multi=True,
                options=[{"label": x, "value": x} for x in stocks]
            ),
        ], className="six columns", style={"width": "50%"}),

        # Dropdown para seleccionar la variable financiera
        html.Div([
            dcc.Dropdown(
                id="metricdropdown", 
                value="Precio de Cierre", 
                clearable=False,
                options=[{"label": x, "value": x} for x in sales_list]
            ),
        ], className="six columns", style={"width": "50%"})
    ], className="row"),

    # Slicer de fechas con rango de los últimos 5 años
    dcc.DatePickerRange(
        id="date_picker",
        start_date=historical_data.index.min(),
        end_date=historical_data.index.max(),
        min_date_allowed=historical_data.index.min(),
        max_date_allowed=historical_data.index.max()
    ),

    # Gráficos
    html.Div([dcc.Graph(id="bar", figure={})]),
    html.Div([dcc.Graph(id="boxplot", figure={})]),

    # Tabla de datos
    html.Div(id="table-container_1", style={"marginBottom": "15px", "marginTop": "0px"})
])

# Callback para actualizar los gráficos y la tabla
@app.callback(
    [Output("bar", "figure"), Output("boxplot", "figure"), Output("table-container_1", "children")],
    [Input("stockdropdown", "value"), Input("metricdropdown", "value"), Input("date_picker", "start_date"), Input("date_picker", "end_date")]
)
def display_value(selected_stock, selected_metric, start_date, end_date):
    # Filtrar datos según las empresas seleccionadas y el rango de fechas
    if len(selected_stock) == 0:
        selected_stock = stocks  # Si no hay selección, mostrar todas las acciones

    # Filtrar datos por la métrica seleccionada y el rango de fechas
    if selected_metric == "Precio de Cierre":
        dfv_fltrd = historical_data.loc[start_date:end_date, selected_stock].reset_index()
        y_label = "Precio de Cierre"
    elif selected_metric == "Retornos Diarios":
        dfv_fltrd = returns_data.loc[start_date:end_date, selected_stock].reset_index()
        y_label = "Retornos Diarios"
    else:
        dfv_fltrd = historical_data.loc[start_date:end_date, selected_stock].reset_index()
        y_label = selected_metric

    # Gráfico de líneas
    fig = px.line(dfv_fltrd.melt(id_vars="Date", var_name="Company", value_name=y_label),
                  x="Date", y=y_label, color="Company",
                  title=f"{selected_metric} para {', '.join(selected_stock)}",
                  width=1000, height=500)

    # Gráfico de caja (boxplot)
    fig2 = px.box(dfv_fltrd.melt(id_vars="Date", var_name="Company", value_name=y_label),
                  x="Company", y=y_label, color="Company",
                  title=f"Distribución de {selected_metric} por Compañía",
                  width=1000, height=500)

    # Modificar el DataFrame para hacer una tabla de precios o retornos por fechas
    df_reshaped = dfv_fltrd.set_index("Date")
    df_reshaped2 = df_reshaped[selected_stock].reset_index()

    # Crear la tabla de datos
    data_table = dash_table.DataTable(
        columns=[{"name": i, "id": i} for i in df_reshaped2.columns],
        data=df_reshaped2.to_dict("records"),
        export_format="csv",
        fill_width=True,
        style_cell={"font-size": "12px"},
        style_table={"maxWidth": 1000},
        style_header={"backgroundColor": "blue", "color": "white"},
        style_data_conditional=[{"backgroundColor": "white", "color": "black"}]
    )

    return fig, fig2, data_table

# Ejecutar la aplicación en el puerto 8053
if __name__ == "__main__":
    app.run_server(debug=True, port=8053)
