import streamlit as st
import networkx as nx
import pandas as pd
import pydeck as pdk
import overpy
from geopy.distance import geodesic  # Para calcular distâncias geográficas

# Consulta à API Overpass
api = overpy.Overpass()
result = api.query("""
area["name"="Distrito Federal"]->.searchArea;
(
  node["amenity"="restaurant"]["cuisine"="pizza"](area.searchArea);
  node["amenity"="fast_food"]["cuisine"="pizza"](area.searchArea);
);
out body;
""")

# Criar dicionário de localizações a partir dos dados da API
locations = {
    node.tags.get("name", f"Sem nome {i}"): (float(node.lat), float(node.lon))
    for i, node in enumerate(result.nodes)
}

# Exibir os nós no console para depuração
for name, (lat, lon) in locations.items():
    print(name, lat, lon)

# Criar grafo com pesos baseados na distância geográfica
G = nx.DiGraph()
location_names = list(locations.keys())

# Definir uma distância máxima para conectar os nós (em metros)
distancia_maxima = 1000  # Exemplo: 1000 metros (1 km)

for i, loc1 in enumerate(location_names):
    for j, loc2 in enumerate(location_names):
        if i != j:  # Evitar laços
            coord1 = locations[loc1]
            coord2 = locations[loc2]
            distance = geodesic(coord1, coord2).meters  # Distância em metros
            if distance <= distancia_maxima:  # Conectar apenas se a distância for menor ou igual ao limite
                G.add_edge(loc1, loc2, weight=distance)

# Interface do Streamlit
st.title("Procurando menor caminho motoboy - Menor Caminho (Dijkstra)")

origem = st.selectbox("Escolha o ponto de partida", location_names)
destino = st.selectbox("Escolha o destino", location_names)

if origem != destino:
    try:
        caminho = nx.dijkstra_path(G, origem, destino)
        custo = nx.dijkstra_path_length(G, origem, destino)
        st.success(f"Caminho: {' ➡️ '.join(caminho)} (Custo: {custo:.2f} metros)")
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
