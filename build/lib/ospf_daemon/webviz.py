import dash
from dash import dcc, html
import dash_cytoscape as cyto
import threading

def generar_cytoscape_data(lsdb):
    nodes = []
    edges = []
    links = lsdb.get_links()
    for router in links:
        nodes.append({'data': {'id': router, 'label': router}})
        for vecino, costo in links[router]:
            edges.append({
                'data': {
                    'source': router,
                    'target': vecino,
                    'label': str(costo)
                }
            })
    return nodes + edges

def iniciar_dashboard(lsdb):
    app = dash.Dash(__name__)
    app.title = "OSPF Topología"
    elements = generar_cytoscape_data(lsdb)
    app.layout = html.Div([
        html.H1("🌐 OSPF Topología en Tiempo Real"),
        cyto.Cytoscape(
            id='grafo-ospf',
            layout={'name': 'cose'},
            style={'width': '100%', 'height': '600px'},
            elements=elements,
            stylesheet=[
                {'selector': 'node', 'style': {'label': 'data(label)', 'background-color': '#0074D9'}},
                {'selector': 'edge', 'style': {'label': 'data(label)', 'curve-style': 'bezier'}}
            ]
        ),
        dcc.Interval(id='intervalo', interval=5000, n_intervals=0)
    ])
    @app.callback(
        dash.dependencies.Output('grafo-ospf', 'elements'),
        [dash.dependencies.Input('intervalo', 'n_intervals')]
    )
    def actualizar_grafo(n):
        return generar_cytoscape_data(lsdb)
    threading.Thread(target=lambda: app.run_server(debug=False, port=8050, host='0.0.0.0'), daemon=True).start()