import streamlit as st
import networkx as nx
import pandas as pd
import pydeck as pdk

# Localizações com coordenadas simuladas
locations = {
    "Centro": (-15.793889, -47.882778),
    "Hospital": (-15.795000, -47.880000),
    "Escola": (-15.800000, -47.885000),
    "Estádio": (-15.798000, -47.890000),
    "Shopping": (-15.796000, -47.895000)
}

# Criar grafo com pesos simulando tempo/distância
G = nx.DiGraph()
edges = [
    ("Centro", "Hospital", 5),
    ("Centro", "Escola", 10),
    ("Hospital", "Escola", 3),
    ("Escola", "Estádio", 4),
    ("Estádio", "Shopping", 2),
    ("Centro", "Shopping", 20)
]
for u, v, w in edges:
    G.add_edge(u, v, weight=w)
    G.add_edge(v, u, weight=w)  # Grafo não direcionado

st.title("Procurando menor caminho motoboy - Menor Caminho (Dijkstra)")

origem = st.selectbox("Escolha o ponto de partida", list(locations.keys()))
destino = st.selectbox("Escolha o destino", list(locations.keys()))

if origem != destino:
    try:
        caminho = nx.dijkstra_path(G, origem, destino)
        custo = nx.dijkstra_path_length(G, origem, destino)
        st.success(f"Caminho: {' ➡️ '.join(caminho)} (Custo: {custo})")
    except nx.NetworkXNoPath:
        st.error("Não há caminho entre os pontos selecionados.")
        caminho = []
else:
    caminho = []

# Nós
nodes_df = pd.DataFrame([
    {"name": name, "lat": lat, "lon": lon} for name, (lat, lon) in locations.items()
])

# Arestas de todas as conexões no grafo
all_edges_df = pd.DataFrame([
    {
        "from_lat": locations[u][0], "from_lon": locations[u][1],
        "to_lat": locations[v][0], "to_lon": locations[v][1]
    }
    for u, v in G.edges
])

# Arestas do caminho encontrado
edges_df = []
for i in range(len(caminho) - 1):
    a, b = caminho[i], caminho[i + 1]
    from_lat, from_lon = locations[a]
    to_lat, to_lon = locations[b]
    edges_df.append({
        "from_lat": from_lat, "from_lon": from_lon,
        "to_lat": to_lat, "to_lon": to_lon
    })

edges_df = pd.DataFrame(edges_df)

# Camada de todas as arestas (cinza)
all_edges_layer = pdk.Layer(
    "LineLayer",
    data=all_edges_df,
    get_source_position='[from_lon, from_lat]',
    get_target_position='[to_lon, to_lat]',
    get_color=[200, 200, 200],  # Cinza
    get_width=2
)

# Camada de arestas do caminho encontrado (vermelho)
path_edges_layer = pdk.Layer(
    "LineLayer",
    data=edges_df,
    get_source_position='[from_lon, from_lat]',
    get_target_position='[to_lon, to_lat]',
    get_color=[255, 0, 0],  # Vermelho
    get_width=4
)

# Camada de nós (pontos)
points_layer = pdk.Layer(
    "ScatterplotLayer",
    data=nodes_df,
    get_position='[lon, lat]',
    get_color='[0, 0, 255]',  # Azul
    get_radius=70
)

# Mapa
st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=pdk.ViewState(
        latitude=-15.796,
        longitude=-47.885,
        zoom=13,
        pitch=0
    ),
    layers=[all_edges_layer, points_layer, path_edges_layer]
))
