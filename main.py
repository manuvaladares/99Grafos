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

# Arestas do caminho encontrado
edges_df = []
for i in range(len(caminho)-1):
    a, b = caminho[i], caminho[i+1]
    from_lat, from_lon = locations[a]
    to_lat, to_lon = locations[b]
    edges_df.append({
        "from_lat": from_lat, "from_lon": from_lon,
        "to_lat": to_lat, "to_lon": to_lon
    })

edges_df = pd.DataFrame(edges_df)

# Camadas do mapa
points_layer = pdk.Layer(
    "ScatterplotLayer",
    data=nodes_df,
    get_position='[lon, lat]',
    get_color='[0, 0, 255]',
    get_radius=70
)

edges_layer = pdk.Layer(
    "LineLayer",
    data=edges_df,
    get_source_position='[from_lon, from_lat]',
    get_target_position='[to_lon, to_lat]',
    get_color=[255, 0, 0],
    get_width=4
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
    layers=[points_layer, edges_layer]
))