import streamlit as st
import networkx as nx
import pandas as pd
import pydeck as pdk
from geopy.distance import geodesic
import osmnx as ox
import heapq  # Para implementar a fila de prioridade
from shapely.geometry import Point  # Importar Point do shapely

# Configuração da página
st.set_page_config(page_title="99Grafos", layout="wide")
st.title("📍 99Grafos - calcule a sua viagem com o algoritmo Dijkstra")
st.markdown("""
            Com o algoritmo de Dijkstra, você pode encontrar o caminho mais curto entre dois pontos em Brasília, utilizando o grafo real de ruas.
            """)

# 1. Definir localizações manuais
locations = {
    "Rodoviária do Plano Piloto": (-15.7938, -47.8825),
    "UnB - Campus Darcy Ribeiro": (-15.754100460854655, -47.87513611438155),
    "Palácio do Planalto": (-15.7997, -47.8645),
    "Torre de TV": (-15.7896, -47.8916),
    "Congresso Nacional": (-15.7995, -47.8646),
    "Esplanada dos Ministérios": (-15.7991, -47.8616),
    "Hospital de Brasília": (-15.843808272983713, -47.88262833462165),
    "Shopping Conjunto Nacional": (-15.7882, -47.8926),
    "Museu Nacional": (-15.7980, -47.8666),
    "Catedral de Brasília": (-15.7989, -47.8750),
    "Estádio Nacional Mané Garrincha": (-15.7835, -47.8992),
    "Praça dos Três Poderes": (-15.8009, -47.8609),
    "Setor Comercial Sul": (-15.7921, -47.8847),
    "Setor Hoteleiro Norte": (-15.7893, -47.8911),
    "Setor Hoteleiro Sul": (-15.7942, -47.8918),
    "Parque Olhos D'Água": (-15.7489, -47.8858),
    "Patio Brasil Shopping": (-15.79585078452096, -47.892051990468275),
    "Parque da Cidade": (-15.800625435221287, -47.90449744025181),
    "Hospital Santa Lúcia": (-15.827571722176934, -47.931268716593245),
    "Terraço Shopping": (-15.803246369681947, -47.94008953086486),
    "Hospital da Criança": (-15.75758688366676, -47.91644562555905),
    "Pier 21": (-15.816228030908151, -47.87370194313569),
    "Park Shopping": (-15.832413299991769, -47.95421112788403),
    "Riacho Fundo I": (-15.88305460913746, -48.01648103305345),
    "Guará I": (-15.819009371543782, -47.982788310807095),
    "Gaura II": (-15.835735695465734, -47.97995812217213),
    "Sudoeste": (-15.79553832032996, -47.923489119757896),
    "Cidade Estrutural": (-15.782310341931979, -47.9941090647448),
    "Feira dos Importados": (-15.796526535467832, -47.950744744182465),
    "Shopping Boulevard": (-15.731471908246464, -47.89850604098915),
    "Igrejinha Nossa Senhora de Fátima": (-15.812315562362476, -47.90395016806459),
    "Hospital das Forças Armadas": (-15.799845174275168, -47.93459172372393),
    "Banco do Brasil": (-15.783739894442814, -47.87648434780573),
}

# 2. Baixar o grafo real de ruas de Brasília
@st.cache_resource
def carregar_grafo():
    with st.spinner("Carregando ruas de Brasília..."):
        centro = locations["Rodoviária do Plano Piloto"]
        # Obter o grafo
        G_real = ox.graph_from_point(centro, dist=15000, network_type='drive')
        
        # Usar o grafo não projetado para evitar erros de projeção
        # Vamos instalar scikit-learn em vez de projetar o grafo
        G_real = G_real.to_undirected()
        return G_real

# Implementação manual do algoritmo de Dijkstra
def dijkstra(G, origem, destino):
    """
    Implementação manual do algoritmo de Dijkstra para encontrar o caminho mais curto
    entre origem e destino em um grafo G, usando o atributo 'length' como peso.
    
    Parâmetros:
    G - Grafo NetworkX com pesos nas arestas
    origem - Nó de origem
    destino - Nó de destino
    
    Retorna:
    caminho - Lista de nós que formam o caminho mais curto
    custo - Custo total do caminho
    """
    # Inicialização
    distancias = {node: float('infinity') for node in G.nodes()}
    distancias[origem] = 0
    
    # Fila de prioridade (nó, distância)
    pq = [(0, origem)]
    
    # Para reconstruir o caminho
    predecessores = {node: None for node in G.nodes()}
    
    # Nós visitados
    visitados = set()
    
    while pq:
        # Pega o nó com menor distância
        dist_atual, no_atual = heapq.heappop(pq)
        
        # Se chegamos ao destino, terminamos
        if no_atual == destino:
            break
            
        # Se já visitamos este nó, pulamos
        if no_atual in visitados:
            continue
            
        # Marca como visitado
        visitados.add(no_atual)
        
        # Explora os vizinhos
        for vizinho in G.neighbors(no_atual):
            # Pega o peso da aresta (comprimento)
            try:
                peso = G[no_atual][vizinho][0]['length']  # Para grafos com múltiplas arestas entre nós
            except (KeyError, IndexError):
                try:
                    peso = G[no_atual][vizinho]['length']  # Para grafos simples
                except KeyError:
                    continue  # Se não há peso 'length', pula
            
            # Calcula nova distância
            distancia = dist_atual + peso
            
            # Se encontramos um caminho mais curto para o vizinho
            if distancia < distancias[vizinho]:
                distancias[vizinho] = distancia
                predecessores[vizinho] = no_atual
                # Adiciona à fila de prioridade
                heapq.heappush(pq, (distancia, vizinho))
    
    # Reconstrói o caminho do destino até a origem
    caminho = []
    no_atual = destino
    
    # Se não há caminho para o destino
    if predecessores[destino] is None and destino != origem:
        return [], float('infinity')
        
    while no_atual is not None:
        caminho.append(no_atual)
        no_atual = predecessores[no_atual]
        
    # Inverte o caminho para ficar da origem ao destino
    caminho.reverse()
    
    return caminho, distancias[destino]

# 3. Interface de seleção
pontos = list(locations.keys())
origem_plan = st.selectbox("📍 Origem", pontos, index=0)
destino_plan = st.selectbox("📍 Destino", pontos, index=1)

calcular = st.button("Calcular Menor Caminho")

# 4. Calcular menor caminho real (Dijkstra nas ruas)
caminho = []
custo_total = 0
path_df = pd.DataFrame()  # Inicializa vazio
G_real = None

if calcular:
    # Carrega o grafo apenas quando o botão é clicado
    G_real = carregar_grafo()
    
    # Obter coordenadas dos pontos selecionados
    origem = locations[origem_plan]
    destino = locations[destino_plan]
    
    if origem != destino:
        try:
            # Converter coordenadas para nós mais próximos no grafo
            # Como estamos usando um grafo não projetado, precisamos de scikit-learn
            # A instalação de scikit-learn é necessária: pip install scikit-learn
            no_origem = ox.distance.nearest_nodes(G_real, origem[1], origem[0])
            no_destino = ox.distance.nearest_nodes(G_real, destino[1], destino[0])
            
            caminho, custo_total = dijkstra(G_real, no_origem, no_destino)
            
            if caminho:
                st.success(f"🚗 Menor caminho (via ruas): {origem_plan} ➡️ {destino_plan} — {custo_total:.0f} metros")
                
                # Se temos um caminho válido, criar dataframe para o caminho
                if len(caminho) > 1:
                    path_df = pd.DataFrame([
                        {
                            "from_lat": G_real.nodes[a]['y'],
                            "from_lon": G_real.nodes[a]['x'],
                            "to_lat": G_real.nodes[b]['y'],
                            "to_lon": G_real.nodes[b]['x']
                        }
                        for a, b in zip(caminho, caminho[1:])
                    ])
            else:
                st.error("❌ Não há caminho viável entre os pontos.")
        except Exception as e:
            st.error(f"❌ Erro ao calcular o caminho: {e}")
            st.exception(e)  # Isso mostra o traceback do erro para depuração

# Mostrar o mapa apenas se o botão foi clicado e o grafo foi carregado
if calcular and G_real is not None:
    # 5. Preparar dados para o mapa
    nodes_df = pd.DataFrame([
        {"name": nome, "lat": lat, "lon": lon} 
        for nome, (lat, lon) in locations.items()
    ])

    # Preparar as arestas do grafo para visualização
    edges_df = pd.DataFrame([
        {
            "from_lat": G_real.nodes[u]['y'],
            "from_lon": G_real.nodes[u]['x'],
            "to_lat": G_real.nodes[v]['y'],
            "to_lon": G_real.nodes[v]['x']
        }
        for u, v in G_real.edges()
    ])

    # 6. Mapas com Pydeck
    centro = locations["Rodoviária do Plano Piloto"]
    
    layer_ruas = pdk.Layer(
        "LineLayer",
        data=edges_df,
        get_source_position='[from_lon, from_lat]',
        get_target_position='[to_lon, to_lat]',
        get_color=[180, 180, 180],
        get_width=1
    )

    layers = [layer_ruas]

    # Adicionar camada do caminho se existir
    if not path_df.empty:
        layer_caminho = pdk.Layer(
            "LineLayer",
            data=path_df,
            get_source_position='[from_lon, from_lat]',
            get_target_position='[to_lon, to_lat]',
            get_color=[255, 0, 0],
            get_width=4
        )
        layers.append(layer_caminho)

    layer_pontos = pdk.Layer(
        "ScatterplotLayer",
        data=nodes_df,
        get_position='[lon, lat]',
        get_color='[0, 100, 255]',
        get_radius=100,
        pickable=True
    )
    layers.append(layer_pontos)

    # 7. Renderização
    st.pydeck_chart(pdk.Deck(
        map_style="mapbox://styles/mapbox/light-v9",
        initial_view_state=pdk.ViewState(
            latitude=centro[0],
            longitude=centro[1],
            zoom=12
        ),
        layers=layers,
        tooltip={"text": "{name}"}
    ), height=800)

    # Mostrar o custo da viagem, se o caminho foi calculado
    if calcular and custo_total > 0:
        preco_por_km = 2 
        custo_viagem = (custo_total / 1000) * preco_por_km
        st.markdown(f"### 💰 Custo estimado da viagem: **R$ {custo_viagem:.2f}**")

# Informações adicionais sobre o algoritmo de Dijkstra
st.markdown("""
## Sobre o Algoritmo de Dijkstra

Neste aplicativo, implementamos manualmente o **algoritmo de Dijkstra** para encontrar o caminho mais curto entre dois pontos em Brasília, utilizando o grafo real de ruas.

### Como o algoritmo funciona:

1. **Inicialização**: Todas as distâncias são definidas como infinito, exceto a origem (distância 0)
2. **Processo iterativo**: A cada passo, escolhemos o nó não visitado com menor distância
3. **Relaxamento**: Atualizamos as distâncias dos vizinhos se encontrarmos um caminho mais curto
4. **Término**: Paramos quando chegamos ao destino ou visitamos todos os nós alcançáveis

O algoritmo garante o caminho mais curto em grafos com pesos positivos, como é o caso das distâncias nas ruas.
""")