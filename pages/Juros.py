import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px

# Configuração da página
st.set_page_config(layout="wide")

if os.path.exists('styles.css'):
    with open('styles.css') as f:
        st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
else:
    st.warning("Arquivo 'styles.css' não encontrado.")
    
curdir=os.getcwd()
path = os.path.join(os.getcwd(), "data\\")

st.logo(curdir+'\\LogoTransparente.png', size='large')

# Carrega as variáveis da sessão por causa da recarga da página
for k, v in st.session_state.items():
    st.session_state[k] = v

# Recupera dados e ativos
futuros_juros=st.session_state.ativos.loc[st.session_state.ativos.index.isin(['ZB=F','ZN=F','ZF=F','ZT=F'])]

dados_futuros=st.session_state.dados[futuros_juros.Nome.values]
dados_futuros.index=pd.to_datetime(dados_futuros.index)

ativos=st.session_state.ativos.loc[st.session_state.ativos['Mercados']=='Juros']
dados=st.session_state.dados[ativos.Nome]
dados.index=pd.to_datetime(dados.index)


# Valida datas
def datas_validas (inicio, fim):
    if (inicio>fim):
        st.warning('A data inicial não pode ser posterior à data final',icon=":material/error:")
    elif(fim>datetime.today().date()):
        st.warning('A data final não pode ser futura',icon=":material/error:")
    else:
        return True
    return False

# Sidebar
with st.sidebar:
    if 'start_date' not in st.session_state:
        primeira=datetime(2015,1,2)
        última=st.session_state.dados.index[-1]
        st.date_input("De", format="DD/MM/YYYY", value=primeira,key='start_date')
        st.date_input("Até", format="DD/MM/YYYY", value=última, key='end_date')
        dados=dados.loc[st.session_state.start_date:st.session_state.end_date].ffill()
        dados_futuros=dados_futuros.loc[st.session_state.start_date:st.session_state.end_date].ffill()
    else:
        st.date_input("De", format="DD/MM/YYYY", key='start_date')
        st.date_input("Até", format="DD/MM/YYYY", key='end_date')

        if datas_validas(st.session_state.start_date, st.session_state.end_date):
            dados=dados.loc[st.session_state.start_date:st.session_state.end_date].ffill()
            dados_futuros=dados_futuros.loc[st.session_state.start_date:st.session_state.end_date].ffill()
            st.session_state.old_start=st.session_state.start_date
            st.session_state.old_end=st.session_state.end_date
        else:
             dados=dados.loc[st.session_state.old_start:st.session_state.old_end].ffill()
             dados_futuros=dados_futuros.loc[st.session_state.old_start:st.session_state.old_end].ffill()       
   
    atualização=dados.index[-1].date()

#.............................................PRINCIPAL .............................................
st.header(f'Juros americanos', divider=True)

# Prepara métricas e quador de variações
memoria=st.session_state.dados[ativos.Nome].loc[:dados.index[-1]].copy()
Q,Y5,Y10,Y30= st.session_state.dados[ativos.Nome].iloc[-1]
st.write(f'13 semanas: {Q:.2f}% | 5 anos: {Y5:.2f}% | 10 anos: {Y10:.2f}% | 30 anos: {Y30:.2f}% || Atualizado em {atualização}')

Esq, Dir = st.columns(2)

var=memoria.iloc[-1]/memoria.iloc[-2]-1
var_semana=(memoria.iloc[-1]/memoria.loc[memoria.index[-5]])-1
var_mes=(memoria.iloc[-1]/memoria.loc[memoria.index[-21]])-1
var_3meses=(memoria.iloc[-1]/memoria.loc[memoria.index[-63]])-1
var_6meses=(memoria.iloc[-1]/memoria.loc[memoria.index[-128]])-1
var_1ano=(memoria.iloc[-1]/memoria.loc[memoria.index[-252]])-1


status=pd.DataFrame({'Mercado':memoria.iloc[-1].index,
					 'Último':memoria.iloc[-1].values,
					 '%(dia)':var,
					 '%(semana)':var_semana,
					 '%(mês)':var_mes.values,
					 '%(3 meses)':var_3meses.values,
					 '%(6 meses)':var_6meses.values,
					 '%(1 ano)':var_1ano.values})
status.index=status.Mercado
status.drop('Mercado',axis=1,inplace=True)

# Prepara Curva de Juros
Curva_Juros=pd.DataFrame({'Prêmio de risco':status.Último})
Esq, Dir = st.columns(2)

# Gráficos de evolução histórica
with Esq:
	st.subheader('Treasury yelds' )
	chart=dados.dropna()
	st.plotly_chart(px.line(chart,chart.index,chart.columns,labels=dict(Nome='',value='')).update_layout(legend=dict(orientation="h",yanchor="bottom",yref= "container")))
	
with Dir:
	st.subheader('Futuros de Juros' )
	chart_futuros=dados_futuros.dropna()
	st.plotly_chart(px.line(chart_futuros,chart_futuros.index,chart_futuros.columns,labels=dict(Nome='',value='')).update_layout(legend=dict(orientation="h",yanchor="bottom",yref= "container")))
	
	
# Quadro de Variações e curva de juros
Esq, Dir = st.columns(2)

with Esq:	
	st.subheader('Variações')
	estilo = status.dropna().style.map(lambda x: f"background-color: {'green' if x>0 else 'red'}", subset=['%(dia)','%(semana)','%(mês)','%(3 meses)','%(6 meses)','%(1 ano)'])
	st.dataframe(estilo)


with Dir:
	st.subheader('Curva de juros')
	st.plotly_chart(px.line(dados.resample('M').last().T,labels=dict(Nome='', value='Taxa anual (%)'),animation_frame='Date').
				 update_layout(showlegend=False,yaxis_range=[0,7],transition = {'duration': 10}))