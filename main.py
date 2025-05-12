import streamlit as st
import networkx as nx
import pandas as pd
import pydeck as pdk
from geopy.distance import geodesic

# Configuração da página
st.set_page_config(page_title="Menor Caminho Manual", layout="wide")
st.title("📍 Menor Caminho em Brasília (Plano Piloto)")

# 1. Definir os nós manualmente
locations = {
    "Rodoviária do Plano Piloto": (-15.7938, -47.8825),
    "UnB - Campus Darcy Ribeiro": (-15.754100460854655, -47.87513611438155),
    "UnB - Campus Gama": (-15.989299, -48.044103),
    "Palácio do Planalto": (-15.7997, -47.8645),
    "Torre de TV": (-15.7896, -47.8916),
    "Congresso Nacional": (-15.7995, -47.8646),
    "Esplanada dos Ministérios": (-15.7991, -47.8616),
    "Hospital de Base": (-15.7912, -47.8996),
    "Shopping Conjunto Nacional": (-15.7882, -47.8926),
    "Museu Nacional": (-15.7980, -47.8666),
    "Catedral de Brasília": (-15.7989, -47.8750),
}

# 2. Criar grafo e adicionar arestas manualmente com pesos (distância em metros)
G = nx.DiGraph()

for nome, coord in locations.items():
    G.add_node(nome, pos=coord)

# Conexões (arestas manuais) com pesos de distância
def conectar(a, b):
    dist = geodesic(locations[a], locations[b]).meters
    G.add_edge(a, b, weight=dist)
    G.add_edge(b, a, weight=dist)

# Conectar manualmente
conectar("UnB - Campus Gama", "Rodoviária do Plano Piloto")
conectar("Rodoviária do Plano Piloto", "Shopping Conjunto Nacional")
conectar("Rodoviária do Plano Piloto", "UnB - Campus Darcy Ribeiro")
conectar("Rodoviária do Plano Piloto", "Catedral de Brasília")
conectar("Torre de TV", "Hospital de Base")
conectar("Torre de TV", "Catedral de Brasília")
conectar("Catedral de Brasília", "Museu Nacional")
conectar("Museu Nacional", "Congresso Nacional")
conectar("Congresso Nacional", "Palácio do Planalto")
conectar("Palácio do Planalto", "Esplanada dos Ministérios")
conectar("Hospital de Base", "Shopping Conjunto Nacional")

# 3. Interface de seleção
nodos_disponiveis = list(locations.keys())
origem = st.selectbox("Origem", nodos_disponiveis, index=0)
destino = st.selectbox("Destino", nodos_disponiveis, index=1)

# 4. Cálculo do menor caminho
caminho, custo = [], 0
if origem != destino:
    try:
        caminho = nx.dijkstra_path(G, origem, destino)
        custo = nx.dijkstra_path_length(G, origem, destino)
        st.success(f"📍 Menor caminho: {' ➡️ '.join(caminho)} — Total: {custo:.0f} m")
    except nx.NetworkXNoPath:
        st.error("❌ Não há caminho entre os pontos selecionados.")

# 5. Dados para visualização no mapa
nodes_df = pd.DataFrame([
    {"name": name, "lat": lat, "lon": lon}
    for name, (lat, lon) in locations.items()
])

edges_df = pd.DataFrame([
    {
        "from_lat": locations[u][0], "from_lon": locations[u][1],
        "to_lat": locations[v][0], "to_lon": locations[v][1]
    }
    for u, v in G.edges
])

path_edges_df = pd.DataFrame([
    {
        "from_lat": locations[a][0], "from_lon": locations[a][1],
        "to_lat": locations[b][0], "to_lon": locations[b][1]
    }
    for a, b in zip(caminho, caminho[1:])
])
# 6. Mapa interativo com Pydeck
layer_arestas = pdk.Layer(
    "LineLayer", data=edges_df,
    get_source_position='[from_lon, from_lat]',
    get_target_position='[to_lon, to_lat]',
    get_color=[150, 150, 150], get_width=2
)

layer_caminho = pdk.Layer(
    "LineLayer", data=path_edges_df,
    get_source_position='[from_lon, from_lat]',
    get_target_position='[to_lon, to_lat]',
    get_color=[255, 0, 0], get_width=4
)

layer_pontos = pdk.Layer(
    "ScatterplotLayer", data=nodes_df,
    get_position='[lon, lat]',
    get_color='[0, 100, 255]', get_radius=100,
    pickable=True
)

st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state=pdk.ViewState(
        latitude=-15.79, longitude=-47.88, zoom=12
    ),
    layers=[layer_arestas, layer_pontos, layer_caminho],
    tooltip={"text": "{name}"}
), height=800)  # Aumenta o eixo Y do mapa
