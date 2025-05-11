import streamlit as st
import networkx as nx
import pandas as pd
import pydeck as pdk
import overpy
from geopy.distance import geodesic

# Configuração da página
st.set_page_config(page_title="Menor Caminho Motoboy", layout="wide")
st.title("📍 Encontrar Menor Caminho entre Pizzarias, Hospitais ou Farmácias")

# 1. Seleção do tipo de amenidade
tipo = st.selectbox("Escolha o tipo de amenidade", ["Pizzarias", "Hospitais", "Farmácias"])

# 2. Filtro Overpass conforme tipo
if tipo == "Pizzarias":
    overpass_filter = """
    (
      node["amenity"="restaurant"]["cuisine"="pizza"](area.searchArea);
      node["amenity"="fast_food"]["cuisine"="pizza"](area.searchArea);
    );
    """
elif tipo == "Hospitais":
    overpass_filter = 'node["amenity"="hospital"](area.searchArea);'
else:  # Farmácias
    overpass_filter = 'node["amenity"="pharmacy"](area.searchArea);'

# 3. Consulta à API Overpass
with st.spinner(f"Consultando {tipo.lower()} no OpenStreetMap..."):
    api = overpy.Overpass()
    query = f"""
    area["name"="Plano Piloto"]->.searchArea;
    {overpass_filter}
    out body;
    """
    result = api.query(query)

# 4. Extrair locais com nome definido
locations = {}
for i, node in enumerate(result.nodes):
    name = node.tags.get("name")
    if name:
        locations[name] = (float(node.lat), float(node.lon))

if not locations:
    st.error(f"Nenhum {tipo.lower()} com nome encontrado no Plano Piloto.")
    st.stop()

# 5. Construir grafo com distâncias geográficas
G = nx.DiGraph()
location_names = list(locations.keys())

distancia_maxima = st.sidebar.slider(
    "Distância máxima para conectar nós (em metros)",
    min_value=500, max_value=50000, value=1000, step=100
)

for i, loc1 in enumerate(location_names):
    for j, loc2 in enumerate(location_names):
        if i != j:
            dist = geodesic(locations[loc1], locations[loc2]).meters
            if dist <= distancia_maxima:
                G.add_edge(loc1, loc2, weight=dist)

# 6. Nós isolados
nodos_conectados = set(G.nodes)
nodos_isolados = set(location_names) - nodos_conectados

if nodos_isolados:
    st.warning("Locais não conectados (distância > limite): " + ", ".join(nodos_isolados))

# 7. Seleção de origem e destino entre nós conectados
grafo_ativos = list(G.nodes)
if len(grafo_ativos) < 2:
    st.error("Poucos pontos conectados para calcular rotas.")
    st.stop()

origem = st.selectbox("Origem", grafo_ativos, index=0)
destino = st.selectbox("Destino", grafo_ativos, index=1)

# 8. Cálculo do menor caminho
caminho, custo = [], 0
if origem != destino:
    try:
        caminho = nx.dijkstra_path(G, origem, destino)
        custo = nx.dijkstra_path_length(G, origem, destino)
        st.success(f"📍 Menor caminho: {' ➡️ '.join(caminho)} — Total: {custo:.0f} m")
    except nx.NetworkXNoPath:
        st.error("❌ Não há caminho entre os pontos selecionados.")

# 9. Dados para visualização no mapa
nodes_df = pd.DataFrame([
    {"name": name, "lat": lat, "lon": lon}
    for name, (lat, lon) in locations.items()
])

all_edges_df = pd.DataFrame([
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

# 10. Camadas Pydeck
layer_arestas = pdk.Layer(
    "LineLayer", data=all_edges_df,
    get_source_position='[from_lon, from_lat]',
    get_target_position='[to_lon, to_lat]',
    get_color=[200, 200, 200], get_width=2
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
    get_color='[0, 0, 255]', get_radius=70,
    pickable=True
)

# 11. Mapa interativo
st.pydeck_chart(pdk.Deck(
    map_style='mapbox://styles/mapbox/light-v9',
    initial_view_state=pdk.ViewState(
        latitude=-15.796, longitude=-47.885, zoom=13
    ),
    layers=[layer_arestas, layer_pontos, layer_caminho],
    tooltip={"text": "{name}"}
))
