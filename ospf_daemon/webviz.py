import dash
from dash import dcc, html
import dash_cytoscape as cyto
import threading

def generar_cytoscape_data(lsdb):
    nodos = set()
    edges = []

    for origen, vecinos in lsdb.get_links().items():
        nodos.add(origen)
        for destino, costo in vecinos:
            nodos.add(destino)
            edges.append({
                'data': {
                    'source': origen,
                    'target': destino,
                    'label': f'cost={costo}'
                }
            })

    elementos = [{'data': {'id': n, 'label': n}} for n in nodos]
    elementos += edges
    return elementos

def iniciar_dashboard(lsdb):
    app = dash.Dash(__name__)
    app.title = "OSPF Topología"
    elements = generar_cytoscape_data(lsdb)
    app.layout = html.Div([
        html.H1("🌐 OSPF Topology in real time"),
        cyto.Cytoscape(
            id='grafo-ospf',
            layout={'name': 'breadthfirst'},
            style={'width': '100%', 'height': '600px'},
            elements=elements,
            stylesheet=[
    {
        'selector': 'node',
        'style': {
            'label': 'data(label)',
            'background-color': '#0074D9',
            'width': 30,       # ← más pequeño
            'height': 30,
            'font-size': '10px',
        }
    },
    {
        'selector': 'edge',
        'style': {
            'label': 'data(label)',
            'font-size': '8px',
            'curve-style': 'bezier',
            'line-color': '#999',
            'target-arrow-color': '#999',
            'target-arrow-shape': 'vee',
            'width': 2
        }
    }
]
        ),
        dcc.Interval(id='intervalo', interval=5000, n_intervals=0)
    ])
    @app.callback(
        dash.dependencies.Output('grafo-ospf', 'elements'),
        [dash.dependencies.Input('intervalo', 'n_intervals')]
    )
    def actualizar_grafo(n):
        elementos = generar_cytoscape_data(lsdb)
        print("[♻️] Actualización del grafo:", elementos)
        return elementos
    threading.Thread(target=lambda: app.run(debug=False, port=8050, host='0.0.0.0'), daemon=True).start()