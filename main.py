import streamlit as st
import networkx as nx
import pandas as pd
import pydeck as pdk
from geopy.distance import geodesic
import osmnx as ox

# Configuração da página
st.set_page_config(page_title="Menor Caminho Manual", layout="wide")
st.title("📍 Menor Caminho em Brasília (via ruas reais)")

# 1. Definir localizações manuais
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

# 2. Baixar o grafo real de ruas de Brasília
with st.spinner("Carregando ruas de Brasília..."):
    centro = locations["Rodoviária do Plano Piloto"]
    G_real = ox.graph_from_point(centro, dist=15000, network_type='drive')
    G_real = G_real.to_undirected()

# 3. Interface de seleção
pontos = list(locations.keys())
origem = st.selectbox("📍 Origem", pontos, index=0)
destino = st.selectbox("📍 Destino", pontos, index=1)

# 4. Calcular menor caminho real (Dijkstra nas ruas)
caminho = []
custo_total = 0

if origem != destino:
    try:
        # Converter coordenadas para nós mais próximos no grafo
        no_origem = ox.distance.nearest_nodes(G_real, locations[origem][1], locations[origem][0])
        no_destino = ox.distance.nearest_nodes(G_real, locations[destino][1], locations[destino][0])

        caminho = nx.shortest_path(G_real, no_origem, no_destino, weight='length')
        custo_total = nx.shortest_path_length(G_real, no_origem, no_destino, weight='length')
        st.success(f"🚗 Menor caminho (via ruas): {origem} ➡️ {destino} — {custo_total:.0f} metros")

    except nx.NetworkXNoPath:
        st.error("❌ Não há caminho viável entre os pontos.")

# 5. Preparar dados para o mapa
nodes_df = pd.DataFrame([
    {"name": nome, "lat": lat, "lon": lon}
    for nome, (lat, lon) in locations.items()
])

edges_df = pd.DataFrame([
    {
        "from_lat": G_real.nodes[u]['y'], "from_lon": G_real.nodes[u]['x'],
        "to_lat": G_real.nodes[v]['y'], "to_lon": G_real.nodes[v]['x']
    }
    for u, v in G_real.edges()
])

path_df = pd.DataFrame([
    {
        "from_lat": G_real.nodes[a]['y'], "from_lon": G_real.nodes[a]['x'],
        "to_lat": G_real.nodes[b]['y'], "to_lon": G_real.nodes[b]['x']
    }
    for a, b in zip(caminho, caminho[1:])
])

# 6. Mapas com Pydeck
layer_ruas = pdk.Layer(
    "LineLayer", data=edges_df,
    get_source_position='[from_lon, from_lat]',
    get_target_position='[to_lon, to_lat]',
    get_color=[180, 180, 180], get_width=1
)

layer_caminho = pdk.Layer(
    "LineLayer", data=path_df,
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

# 7. Renderização
st.pydeck_chart(pdk.Deck(
    map_style="mapbox://styles/mapbox/light-v9",
    initial_view_state=pdk.ViewState(
        latitude=centro[0], longitude=centro[1], zoom=12
    ),
    layers=[layer_ruas, layer_pontos, layer_caminho],
    tooltip={"text": "{name}"}
), height=800)
