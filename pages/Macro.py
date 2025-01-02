import streamlit as st
import ipeadatapy as ipea
# Configuração do layout
st.set_page_config(layout="wide")


import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px

for k, v in st.session_state.items():
    st.session_state[k] = v

curdir=os.getcwd()
path = os.path.join(os.getcwd(), "data/")

st.logo(curdir+'/logo.jpg', size='large')

if os.path.exists('styles.css'):
    with open('styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
else:
    st.warning("Arquivo 'styles.css' não encontrado.")

selection=[]

@st.cache_data

def load_data():
    dwh=pd.read_csv(path+'Data_Warehouse.csv', sep=';', encoding='utf-8', index_col=0)
    return dwh

data_stock =load_data()

work_data=data_stock[['CODE','NAME','COMMENT','FREQUENCY','THEME','LAST UPDATE','SOURCE ACRONYM','SOURCE','SERIES STATUS','COUNTRY']]

recorte=work_data.copy()
recorte.columns=['Código','Nome', 'Descrição','Frequência', 'Tema', 'Atualização', 'Fonte', 'Nome da Fonte', 'Status', 'País']

with st.sidebar:
    if st.toggle('Filtrar por tema'):
        recorte=recorte[recorte.Tema==st.selectbox('Tema',work_data.THEME.unique())]
    if st.toggle('Filtrar por frenquência'):
        recorte=recorte[recorte.Frequência==st.selectbox('Frequência',work_data.FREQUENCY.unique())]
    if st.toggle('Filtrar por país'):
        recorte=recorte[recorte.País==st.selectbox('País',work_data.COUNTRY.unique())]
    if st.checkbox('Somente séries ativas?'):
        recorte=recorte[recorte.Status=='A']

st.header("Base de dados", divider=True)
sel=['ANBIMA12_IBVSP12']
event = st.dataframe(
    recorte,
    use_container_width=True,
    hide_index=True,
    on_select="rerun",
    selection_mode="multi-row",
)

st.subheader("Indicadores selecionados", divider=True)

sel=sel+list(recorte.iloc[event.selection.rows].Código.values)

st.session_state.selected=sel

ts=[pd.Series(ipea.timeseries(item).iloc[:,-1]) for item in list(st.session_state.selected)]
df=pd.DataFrame()
for item in range(len(ts)):
    df[st.session_state.selected[item]]=ts[item].loc[~ts[item].index.duplicated(keep='first')]

ensaio=df.dropna()/df.dropna().iloc[0]

esq, dir= st.columns(2)
with esq:
    if len(sel)>1:
        st.plotly_chart(px.imshow(ensaio.corr(),text_auto=True,color_continuous_scale='RdBu_r'))
    df
with dir:
    st.plotly_chart(px.line(ensaio,labels=dict(DATE='',value='')).update_layout(legend=dict(orientation="h",yanchor="bottom",yref= "container")))

