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
path = os.path.join(os.getcwd(), "data/")

st.logo(curdir+'/logo.jpg', size='large')

# Carrega as variáveis da sessão por causa da recarga da página
for k, v in st.session_state.items():
    st.session_state[k] = v

# Carrega base de dados no cache
@st.cache_data
def load_data():
    df_Macro_Mensais=pd.read_csv(path+'Macro_Mensais.csv', sep=';', encoding='utf-8', index_col=0)
    df_Macro_Mensais.index = pd.to_datetime(df_Macro_Mensais.index,format='%Y-%m-%d')
    ativos=pd.read_csv(path+'Mercados.csv',sep ='\t',encoding='utf-8',index_col=0)
    dados=pd.read_csv(path+'Dados_Mercados.csv',sep =';',encoding='utf-8',index_col=0)
    dados.index = pd.to_datetime(dados.index,format='%Y-%m-%d')
    ativos=ativos[ativos.index.isin(dados.columns)]
    dados.columns=ativos.sort_values('Cod').Nome
    return df_Macro_Mensais, ativos,dados

if 'df_Macro_Mensais' not in st.session_state:
    st.session_state.df_Macro_Mensais, st.session_state.ativos, st.session_state.dados = load_data()

diarios=pd.read_csv(path+'Macro_Diarios.csv', sep=';', encoding='utf-8', index_col=0)
diarios.index = pd.to_datetime(diarios.index,format='%Y-%m-%d')


# Valida datas
def datas_validas (inicio, fim):
    if (inicio>fim):
        st.warning('A data inicial não pode ser posterior à data final',icon=":material/error:")
    elif(fim>st.session_state.df_Macro_Mensais.index[-1].date()):
        st.warning('A data final escolhida é posterior à útlima atualização',icon=":material/error:")
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
        recorte=st.session_state.df_Macro_Mensais.ffill().loc[st.session_state.start_date:st.session_state.end_date]
        daily=diarios.loc[st.session_state.start_date:st.session_state.end_date].resample('M').last()
    else:
        st.date_input("De", format="DD/MM/YYYY", key='start_date')
        st.date_input("Até", format="DD/MM/YYYY", key='end_date')

        if datas_validas (st.session_state.start_date, st.session_state.end_date):
            recorte=st.session_state.df_Macro_Mensais.ffill().loc[st.session_state.start_date:st.session_state.end_date]
            daily=diarios.loc[st.session_state.start_date:st.session_state.end_date].resample('M').last()
            st.session_state.old_start=st.session_state.start_date
            st.session_state.old_end=st.session_state.end_date
        else:
            recorte=st.session_state.df_Macro_Mensais.ffill().loc[st.session_state.old_start:st.session_state.old_end]
            daily=diarios.loc[st.session_state.old_start:st.session_state.old_end].resample('M').last()
    
# Função para criar quadro de métricas
def quadro_metricas (dados, metrica, unidade, medida,acumulado):
    memoria=st.session_state.df_Macro_Mensais[dados.name].loc[:dados.index[-1]].copy()
    if acumulado :
        legenda='Acumulado'
        trimestre=memoria.iloc[-3:].sum()
        ano=memoria.iloc[-12:].sum()
    else:
        legenda='Variação'
        trimestre=100*(memoria.iloc[-1]/memoria.iloc[-3]-1)
        ano=100*(memoria.iloc[-1]/memoria.iloc[-12]-1)
        medida='%'
    
    quadro =f'{legenda} em 3 meses: {trimestre:.2f}{medida} | 12 meses: {ano:.2f}{medida} | atualização: {dados.index[-1].date()}'
    return quadro

# Função para plotar métricas
def plotar_metrica(metrica, dados, unidade, medida, acumulado):
    serie=dados.ffill()
    atual=serie.iloc[-1]
    st.subheader(f'{metrica}: {unidade}{atual:.2f} ({medida})')
    st.write(quadro_metricas(dados, metrica, unidade, medida, acumulado))
    st.plotly_chart(px.line(serie,serie.index,serie,labels=dict(DATE='', y='')))

#.............................................PRINCIPAL .............................................
st.header('Sinopse Macroeconômica', divider=True)

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Atividade Econômica"," Emprego e Renda","Preços, Juros e Câmbio","Balanço de pagamentos","Expectativas e Confiança"])
col_metricas=st.columns (3)

# Tab de Atividade Econômica
with tab1:
    columns_daily = st.columns(2)

    with columns_daily[0]:
        plotar_metrica("PIB", recorte['PIB'], 'R$','milhões', False)
        
    with columns_daily[1]:
        plotar_metrica("IBC-Br", recorte['IBC-Br'], '', '2002=100', False)

    columns_daily = st.columns(2)
    with columns_daily[0]:
        plotar_metrica("Produção Industrial",recorte['PI_Indústria'], '', '2002=100', False)

    with columns_daily[1]:
        plotar_metrica("Vendas no varejo (reais dessazonalizadas)",recorte['Vendas_Reais_Dessazonalizado'], '', '2002=100', False)

    columns_daily = st.columns(2)
    with columns_daily[0]:
        plotar_metrica("Papelão para embalagem",recorte['Papelão_Embalagem'], '', ' Toneladas', False)

    with columns_daily[1]:
        plotar_metrica("Receita de Serviços (reais dessazonalizadas)",recorte['Receita_Serviços_Real_Dessazonalizado'], '', '2002=100', False)

    columns_daily = st.columns(2)
    with columns_daily[0]:
        plotar_metrica("Tarifa de energia elétrica",recorte['Eletricidade_Tarifa'], 'R$', 'MWh', False)

    with columns_daily[1]:
        consumidor, comercio, Indústria=recorte[['Eletricidade_Consumo','Eletricidade_Comércio','Eletricidade_Indústria']].dropna().iloc[-1]
        st.subheader("Consumo de energia")
        st.write(f'Consumidor: {consumidor:.0f} GWh | Comércio: {comercio:.0f} GWh| Indústria: {Indústria:.0f} GWh')
        st.plotly_chart(px.area(recorte,recorte.index,['Eletricidade_Consumo','Eletricidade_Comércio','Eletricidade_Indústria'],labels=dict(DATE='', value='')).update_layout(legend=dict(orientation="h",yanchor="bottom",yref= "container")))
# Tab de Emprego e Renda        
with tab2:
    columns_monthly = st.columns(2)

    with columns_monthly[0]:
        memoria=st.session_state.df_Macro_Mensais.loc[:recorte.index[-1]].copy()
        saldo=memoria['Ocupação_Mensalizada_Dessazonalizada'].ffill()-memoria['Desocupação_Mensalizada_Dessazonalizada'].ffill()
        st.subheader(f"Saldo da Ocupação/Desocupação {saldo.iloc[-1]:.2f} (p.p.)")
        emprego=recorte[['Ocupação_Mensalizada_Dessazonalizada','Desocupação_Mensalizada_Dessazonalizada']].ffill()
        emprego.columns=['Ocupação','Desocupação']
        st.write(f'Variação em 3 meses:{100*(saldo.iloc[-1]/saldo.iloc[-3]-1):.2f} p.p. |  12 meses: {100*(saldo.iloc[-1]/saldo.iloc[-12]-1):.2f} p.p. | atualização: {emprego.index[-1].date()}')
        st.plotly_chart(px.area(emprego,emprego.index,['Ocupação','Desocupação'],labels=dict(DATE='', value='')))

    with columns_monthly[1]:
        st.subheader(f"Saldo Novo CAGED {recorte['CAGED_Saldo'].dropna().iloc[-1]:.0f} pessoas")
        st.write(f'Acumulado em 3 meses:{recorte['CAGED_Saldo'].dropna().iloc[-3:].sum():.0f} |  12 meses: {recorte['CAGED_Saldo'].dropna().iloc[-12:].sum():.0f} | atualização: {recorte.index[-1].date()}')
        st.plotly_chart(px.bar(recorte,recorte.index,'CAGED_Saldo',labels=dict(DATE='', CAGED_Saldo='')))

    columns_monthly = st.columns(2)
    
    with columns_monthly[0]:
        plotar_metrica("Massa Salarial", recorte['Massa_Salarial_Real_Indústria'],'','média 2006=100', False)

    with columns_monthly[1]:
        plotar_metrica("Rendimento Médio", recorte['Rendimento_Médio'],'R$','penúltimo mês', False)
# Tab de Preços, Juros e Câmbio        
with tab3:
    columns_monthly2 = st.columns(2)

    with columns_monthly2[0]:
        plotar_metrica("IPCA", recorte['IPCA'],'','% a.m.', True)
        
    with columns_monthly2[1]:
        metaSelic=daily['Selic_COPOM'].iloc[-1]
        atualização=daily.index[-1].date()
        memoria_daily=diarios.loc[:atualização]
        trimestre=memoria_daily['Selic_COPOM'].iloc[-1]-memoria_daily['Selic_COPOM'].iloc[-3]
        ano=memoria_daily['Selic_COPOM'].iloc[-1]-memoria_daily['Selic_COPOM'].iloc[-12]
        st.subheader(f'SELIC: {metaSelic:.2f} (% a.a.)')
        st.write(f'Variação 3 meses: {trimestre:.2f}% | 12 meses: {ano:.2f}% | Atualizaçaõ:{atualização}')
        st.plotly_chart(px.line(daily,daily.index,'Selic_COPOM',labels=dict(DATE='', Selic_COPOM='')))

    columns_monthly2 = st.columns(2)
    
    with columns_monthly2[0]:
        plotar_metrica('IPP', recorte['IPP'],'','% a.m.', True)
        
    
    with columns_monthly2[1]:
        plotar_metrica("IGP-M", recorte['IGP-M'],'','% a.m.', True)

    columns_monthly2 = st.columns(2)
    with columns_monthly2[0]:
        plotar_metrica("CDI", recorte['CDI'],'','% a.m.', True)
        
    with columns_monthly2[1]:
        Dólar=daily['Câmbio_Dólar'].iloc[-1]
        #atualização=daily.index[-1].date()
        trimestre=memoria_daily['Câmbio_Dólar'].iloc[-1]/memoria_daily['Câmbio_Dólar'].iloc[-3]-1
        ano=memoria_daily['Câmbio_Dólar'].iloc[-1]/memoria_daily['Câmbio_Dólar'].iloc[-12]-1
        st.subheader(f'Câmbio Dólar/Real: R$ {Dólar:.2f}')
        st.write(f'Variação 3 meses: {100* trimestre:.2f}% | 12 meses: {100*ano:.2f}% | Atualizaçaõ:{atualização}')
        st.plotly_chart(px.line(daily,daily.index,'Câmbio_Dólar',labels=dict(DATE='', Câmbio_Dólar='')))       
# Tab de Balanço de Pagamentos
with tab4:
    columns_quarterly = st.columns(2)

    with columns_quarterly[0]:
        plotar_metrica("Saldo da Balança", recorte['Saldo_Balança'],'US$', 'milhões', False)
        
    with columns_quarterly[1]:
        im,ex=recorte[['Importações','Exportações']].iloc[-1]
        st.subheader("Importação e Exportação (US$ - milhões)")
        st.write(f'Importações: US\\${im:.2f} milhões | Exportações: US\\${ex:.2f} milhões')
        st.plotly_chart(px.line(recorte,recorte.index,['Importações','Exportações'],labels=dict(DATE='',value='')))
        

    columns_quarterly = st.columns(2)

    with columns_quarterly[0]:
        plotar_metrica ("Transações Correntes", recorte['Transações_Correntes_Saldo'],'US$','milhões', True)

    with columns_quarterly[1]:
        st.subheader("Investimento Direto (US$ - milhões)")
        investimentos=recorte[['Investimento_Direto_País','Investimento_Direto_Ingressos']].dropna()
        investimentos.columns=['País','Ingressos']
        pais,ingressos=investimentos.iloc[-1]
        st.write(f'Investimento do país: US\\${im:.2f} milhões | Ingressos: U\\${ex:.2f} milhões')
        st.plotly_chart(px.line(investimentos,investimentos.index, investimentos.columns,labels=dict(DATE='',value='')))

    columns_quarterly = st.columns(2)

    with columns_quarterly[0]:
        plotar_metrica('Resultado Primário', recorte['NFSP_Resultado_Primário'],'R$','milhões', False)

    with columns_quarterly[1]:
        plotar_metrica("Resultados Primário/PIB", recorte['NFSP_Resultado_Primário_PIB'],'','% PIB', False)

    columns_quarterly = st.columns(2)

    with columns_quarterly[0]:
        st.subheader("Endividamento Líquido (R$ - milhões)")
        endividamento=recorte[['DLSP_Externa','DLSP_Interna']].dropna()
        endividamento.columns=['Externa','Interna']
        externa,interna=endividamento.dropna().iloc[-1]
        st.write(f'Interna: R\\${interna:.2f} milhões | Externa: R\\$ {externa:.2f} milhões')
        st.plotly_chart(px.area(endividamento,endividamento.index, endividamento.columns,labels=dict(DATE='',value='')))

    with columns_quarterly[1]:
        st.subheader("Endividamento (% PIB)")
        endividamentoPIB=recorte[['DLSP_Externa_PIB','DLSP_Interna_PIB']].dropna()
        endividamentoPIB.columns=['Externa','Interna']
        externa,interna=endividamentoPIB.dropna().iloc[-1]
        st.write(f'Interna: {interna:.2f} % PIB | Externa: {externa:.2f} % PIB')
        st.plotly_chart(px.area(endividamentoPIB,endividamentoPIB.index, endividamentoPIB.columns,labels=dict(DATE='',value='')))
# Tab de Expectativas e Confiança
with tab5: 
    columns_monthly2 = st.columns(2)
    with columns_monthly2[0]:
        plotar_metrica("Intenção de consumo", recorte['Intenção_Consumo_Famílias'],'','100 = neutro', False)
        
    with columns_monthly2[1]:
        plotar_metrica("Intenção de investimento", recorte['Intenções_Investimento_Comércio'],'','índice', False)
    
    
    columns_monthly2 = st.columns(2)

    with columns_monthly2[0]:
        
        plotar_metrica("Expectativas de Inflação",  recorte['Expectativa_IPCA_Acumulada_12m'],'','% a.a.', False)

    with columns_monthly2[1]:
        plotar_metrica('Renda comprometida', recorte['Renda_Comprometida_Dívidas'],'','% a.m.', False)
    
    
    consumidor, comercio, Indústria=recorte[['ICC','ICEC','ICEI']].dropna().iloc[-1]
    st.subheader("Confiança dos agentes econômicos(100=neutro)")
    st.write(f'Confiança do Consumidor (ICC): {consumidor:.2f} | Confiança do Empresário do Comércio (ICEC): {comercio:.2f} | Confiança do Empresário da Indústria (ICEI): {Indústria:.2f}')
    st.plotly_chart(px.line(recorte,recorte.index,['ICC','ICEC','ICEI'],labels=dict(DATE='', y='')))
     
        
