import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
import plotly.express as px
import webbrowser as web

if len(st.session_state.items())==0:    
    web.open('/mount/src/macro/Home.py')


# Configuração da página
st.set_page_config(layout="wide")

if os.path.exists('styles.css'):
    with open('styles.css') as f:
	    st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
else:
    st.warning("Arquivo 'styles.css' não encontrado.")
    
curdir=os.getcwd()
path = os.path.join(os.getcwd(), "data/")

st.logo(curdir+'/logo.jpg', size='large')


# Carrega as variáveis da sessão por causa da recarga da página
for k, v in st.session_state.items():
    st.session_state[k] = v

# Recupera dados e ativos
ativos=st.session_state.ativos
dados=st.session_state.dados
dados.index=pd.to_datetime(dados.index)

lista_default=['IBOVESPA', 
	       'USD/Real',
		'S&P 500', 
		'NASDAQ Composite',
		'Dow Jones Industrial Average',
		'Shenzhen Component',
		'Nikkei 225',
		'Euronext 100 Index',
		'Ouro',
		'Petróleo BRENT',
		'Milho',
		'Soja',
		'Gado']

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
	    última=st.session_state.df_Macro_Mensais.index[-1]
	    st.date_input("De", format="DD/MM/YYYY", value=primeira,key='start_date')
	    st.date_input("Até", format="DD/MM/YYYY", value=última, key='end_date')
	    st.session_state.portfolio_bolsas=st.multiselect('Ativos', ativos.Nome, default=lista_default, key='option_bolsas')
	    recorte=dados[st.session_state.portfolio_bolsas].loc[st.session_state.start_date:st.session_state.end_date]
	    vix=dados.Vix.ffill().loc[st.session_state.start_date:st.session_state.end_date] 
    else:
	    st.date_input("De", format="DD/MM/YYYY", key='start_date')
	    st.date_input("Até", format="DD/MM/YYYY", key='end_date')
	    if datas_validas (st.session_state.start_date, st.session_state.end_date):
		    recorte=dados[st.session_state.portfolio_bolsas].loc[st.session_state.start_date:st.session_state.end_date]
		    vix=dados.Vix.ffill().loc[st.session_state.start_date:st.session_state.end_date]
		    st.session_state.old_start=st.session_state.start_date
		    st.session_state.old_end=st.session_state.end_date
	    else:
		    recorte=dados[st.session_state.portfolio_bolsas].loc[st.session_state.old_start:st.session_state.old_end]
		    vix=dados.Vix.ffill().loc[st.session_state.old_start:st.session_state.old_end]

#.............................................PRINCIPAL .............................................
st.header('Mercado Global', divider=True)

Esq, Dir = st.columns(2)
memoria=st.session_state.dados.loc[:dados.index[-1]].copy()
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

df=recorte.copy().ffill().bfill()
retornos=(df/df.iloc[0])-1

normalizado=retornos-retornos.min()

RR=pd.DataFrame({'Item':df.columns,'Retorno':retornos.iloc[-1], 'Risco':df.std(), 'Ret_Normal':normalizado.iloc[-1]}, index=df.columns)

with Esq:
	st.subheader(f'Variações (referente ao dia {dados.index[-1].date()})')
	estilo = status.dropna().style.map(lambda x: f"background-color: {'green' if x>0 else 'red'}", subset=['%(dia)','%(semana)','%(mês)','%(3 meses)','%(6 meses)','%(1 ano)'])
	st.dataframe(estilo)
	
		 
with Dir:
	st.subheader('Risco/Retorno')
	st.plotly_chart(px.scatter(RR, x='Risco',y='Retorno',color='Item',size='Ret_Normal'))

	
Esq, Dir = st.columns(2)
with Esq:
    st.subheader('Correlação com o IBOV')
    comparado=recorte.copy()
    if 'IBOVESPA' not in comparado.columns:
	    comparado['IBOVESPA']=dados.IBOVESPA
	    matriz = comparado.corr().IBOVESPA.drop('IBOVESPA').sort_values()
    st.plotly_chart(px.bar(matriz, text_auto=True, labels=dict(Nome='',value=''), orientation='h').update_layout(showlegend=False))
    

    
with Dir:
	valor_recente = vix.iloc[-1]  # Selecionando o último valor dos dados
	situação = 'tranquila'
	if valor_recente > 30: situação ='arriscada'
	elif valor_recente > 20: situação ='exige atenção'

	st.subheader(f'VIX do S&P 500: {valor_recente:.0f} - Situação {situação}')
	dfVix= pd.DataFrame({'Vix':vix,'tranquilidade':20, 'perigo':30})
	st.plotly_chart(px.line(dfVix,dfVix.index,dfVix.columns,labels=dict(Date='',value='')).update_layout(legend=dict(orientation="h",yanchor="bottom",yref= "container")))

st.subheader('Evolução')
chart=recorte/recorte.dropna().iloc[0]
st.plotly_chart(px.line(chart,chart.index,chart.columns,labels=dict(Date='',value='')))
