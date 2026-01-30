import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime
import requests
import pdfplumber
import numpy as np
from fpdf import FPDF
import io

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Blue System", layout="wide", page_icon="🟦")

# --- ESTILOS ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    .stApp { background-color: #0b1120; color: #e6f1ff; font-family: 'Inter', sans-serif; }
    .blue-logo { font-family: 'Inter', sans-serif; font-weight: 200; font-size: 3rem; color: #e6f1ff; letter-spacing: -3px; margin-bottom: -10px; }
    .blue-dot { color: #00f2ff; font-weight: bold; }
    .blue-sub { font-family: 'Inter', sans-serif; font-weight: 400; font-size: 0.8rem; letter-spacing: 4px; color: #00f2ff; text-transform: uppercase; margin-left: 5px; opacity: 0.9; }
    div[data-testid="stMetric"] { background: linear-gradient(145deg, #161b2e 0%, #0b1120 100%); border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.05); padding: 20px; }
    .stButton > button { background: linear-gradient(90deg, #00f2ff 0%, #0066ff 100%); color: #fff; border: none; border-radius: 8px; font-weight: 700; text-transform: uppercase; width: 100%; }
    .status-box { padding: 15px; border-radius: 12px; text-align: center; font-weight: 800; font-size: 1.2rem; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; }
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e293b; }
    </style>
""", unsafe_allow_html=True)

# --- SISTEMA DE LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_system' not in st.session_state: st.session_state.current_system = None

def check_login():
    senha = st.secrets["password"] if "password" in st.secrets else "blue2026"
    if st.session_state.pass_input == senha:
        st.session_state.logged_in = True
    else:
        st.error("Senha incorreta.")

if not st.session_state.logged_in:
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div class='blue-logo' style='text-align:center'>blue<span class='blue-dot'>.</span></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center; color:#00f2ff; opacity:0.7;'>OPERATING SYSTEM</p>", unsafe_allow_html=True)
        st.text_input("SENHA DE ACESSO", type="password", key="pass_input", on_change=check_login)
        st.button("ENTRAR", on_click=check_login)
    st.stop()

# --- MENU PRINCIPAL ---
if st.session_state.current_system is None:
    st.sidebar.markdown("<div class='blue-logo'>blue<span class='blue-dot'>.</span></div>", unsafe_allow_html=True)
    st.title("Central de Comando")
    c1, c2 = st.columns(2)
    with c1:
        st.info("💰 DEPARTAMENTO FINANCEIRO")
        if st.button("ACESSAR FINANCEIRO"): 
            st.session_state.current_system = "Financeiro"
            st.rerun()
    with c2:
        st.info("💎 DEPARTAMENTO COMERCIAL")
        if st.button("ACESSAR COMERCIAL"): 
            st.session_state.current_system = "Comercial"
            st.rerun()
    if st.sidebar.button("Sair"): 
        st.session_state.logged_in = False
        st.rerun()
    st.stop()

# --- BARRA LATERAL COMUM ---
with st.sidebar:
    if st.button("⬅️ VOLTAR AO MENU"): 
        st.session_state.current_system = None
        st.rerun()
    st.markdown("---")

# ==============================================================================
# SISTEMA FINANCEIRO
# ==============================================================================
if st.session_state.current_system == "Financeiro":
    DATA_FILE = "financeiro_blue.csv"
    
    HISTORICO_FILES = [
        "fechamento-de-caixa-57191-6a9ad554-2fa6-41ba-b652-ea0b4c6805e9.xlsx - sheet1.csv",
        "fechamento-de-caixa-57191-83a36dcc-011c-4146-a04a-1c7fb0101e42.xlsx - sheet1.csv",
        "fechamento-de-caixa-57191-f6c1cd85-0cf2-4258-9503-b1120442cbb3.xlsx - sheet1.csv"
    ]

    def normalize_columns_fin(df):
        df.columns = [str(c).strip().lower() for c in df.columns]
        mapping = {
            'vencimento': 'Data', 'data de pagamento': 'Data', 'pagamento': 'Data', 'dt': 'Data', 'date': 'Data', 'data': 'Data',
            'valor líquido r$': 'Valor', 'valor original r$': 'Valor', 'valor_pago': 'Valor', 'total': 'Valor', 'valor': 'Valor', 'vl pago': 'Valor', 'valor$': 'Valor', 'valor r$': 'Valor',
            'pago a / recebido de': 'Subcategoria', 'favorecido': 'Subcategoria', 'cliente': 'Subcategoria', 'paciente': 'Subcategoria', 'nome': 'Subcategoria',
            'descrição': 'Descrição', 'histórico': 'Descrição'
        }
        df = df.rename(columns=mapping)
        df = df.loc[:, ~df.columns.duplicated()]
        
        required = ["Data", "Tipo", "Categoria", "Subcategoria", "Descrição", "Valor", "Status"]
        for col in required:
            if col not in df.columns: 
                df[col] = ""

        def clean_curr(x):
            try:
                return float(str(x).replace('R$','').replace(' ','').replace('.','').replace(',','.'))
            except:
                return 0.0

        df['Valor'] = df['Valor'].apply(clean_curr)
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Data'])
        
        def get_type(row):
            val = row['Valor']
            desc = str(row.get('Descrição', '')).lower() + str(row.get('Tipo', '')).lower()
            if val < 0: return 'Saída'
            if any(x in desc for x in ['saída', 'saida', 'despesa', 'pgto', 'pagamento', 'sangria']): return 'Saída'
            return 'Entrada'
            
        df['Tipo'] = df.apply(get_type, axis=1)
        df['Valor'] = df['Valor'].abs()
        df['Mês'] = df['Data'].dt.strftime("%Y-%m")
        df['Ano'] = df['Data'].dt.year
        return df

    def read_any_file(uploaded_file):
        # AQUI ESTAVA O ERRO, AGORA ESTÁ CORRIGIDO COM ESPAÇAMENTO
        try:
            if uploaded_file.name.endswith('.csv'):
                try:
                    return pd.read_csv(uploaded_file)
                except:
                    return pd.read_csv(uploaded_file, sep=';')
            elif uploaded_file.name.endswith(('.xls', '.xlsx')):
                return pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith('.pdf'):
                with pdfplumber.open(uploaded_file) as pdf:
                    text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                return pd.DataFrame({'Dados Extraídos': text.split('\n')})
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")
            return pd.DataFrame()

    # Carregamento
    if 'db_fin' not in st.session_state:
        if os.path.exists(DATA_FILE):
            st.session_state.db_fin = pd.read_csv(DATA_FILE)
            st.session_state.db_fin['Data'] = pd.to_datetime(st.session_state.db_fin['Data'])
        else:
            dfs = []
            for f in HISTORICO_FILES:
                if os.path.exists(f):
                    try: 
                        temp = pd.read_csv(f, sep=';') if ';' in open(f).readline() else pd.read_csv(f)
                        dfs.append(normalize_columns_fin(temp))
                    except: pass
            
            if dfs:
                st.session_state.db_fin = pd.concat(dfs, ignore_index=True)
                st.session_state.db_fin.to_csv(DATA_FILE, index=False)
            else:
                st.session_state.db_fin = pd.DataFrame(columns=["Data", "Tipo", "Valor", "Categoria", "Descrição", "Subcategoria", "Mês", "Ano"])

    df = st.session_state.db_fin
    
    st.markdown("<div class='blue-logo'>blue<span class='blue-dot'>.</span></div><div class='blue-sub'>Financeiro</div><hr>", unsafe_allow_html=True)
    
    if 'cofre' not in st.session_state: st.session_state.cofre = 0.0
    st.sidebar.caption("COFRE FÍSICO")
    st.session_state.cofre = st.sidebar.number_input("Valor R$", value=st.session_state.cofre)
    
    tab1, tab2, tab3 = st.tabs(["Dashboard", "Lançamentos", "Automação"])
    
    with tab1:
        rec = df[df['Tipo']=='Entrada']['Valor'].sum()
        desp = df[df['Tipo']=='Saída']['Valor'].sum()
        saldo = rec - desp
        total = saldo + st.session_state.cofre
        
        status_color = "#00ff88" if total > 0 else "#ff3333"
        st.markdown(f"<div class='status-box' style='color:{status_color}; border:1px solid {status_color}'>SALDO TOTAL: R$ {total:,.2f}</div>", unsafe_allow_html=True)
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Receita", f"R$ {rec:,.2f}")
        c2.metric("Despesas", f"R$ {desp:,.2f}")
        c3.metric("No Banco", f"R$ {saldo:,.2f}")
        
        st.subheader("Fluxo")
        if not df.empty:
            st.bar_chart(df, x='Mês', y='Valor', color='Tipo')

    with tab2:
        st.subheader("Data Center")
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("Salvar Alterações"):
            edited.to_csv(DATA_FILE, index=False)
            st.session_state.db_fin = edited
            st.success("Salvo!")
            st.rerun()
            
    with tab3:
        st.subheader("Importar Extrato")
        up = st.file_uploader("Arquivo", type=['csv', 'xlsx', 'pdf'])
        if up:
            new_data = read_any_file(up)
            if not new_data.empty:
                st.dataframe(new_data.head())
                if st.button("Confirmar Importação"):
                    clean = normalize_columns_fin(new_data)
                    st.session_state.db_fin = pd.concat([st.session_state.db_fin, clean], ignore_index=True)
                    st.session_state.db_fin.to_csv(DATA_FILE, index=False)
                    st.success("Importado!")
                    st.rerun()

# ==============================================================================
# SISTEMA COMERCIAL
# ==============================================================================
elif st.session_state.current_system == "Comercial":
    DATA_FILE_CRM = "comercial_blue.csv"
    
    if 'db_crm' not in st.session_state:
        if os.path.exists(DATA_FILE_CRM):
            st.session_state.db_crm = pd.read_csv(DATA_FILE_CRM)
        else:
            st.session_state.db_crm = pd.DataFrame({"Nome": ["Exemplo"], "Status": ["Negociação"], "Valor": [0.0]})
            
    df_crm = st.session_state.db_crm
    
    st.markdown("<div class='blue-logo'>blue<span class='blue-dot'>.</span></div><div class='blue-sub'>Comercial</div><hr>", unsafe_allow_html=True)
    st.sidebar.link_button("📅 Abrir TimeTree", "https://treeapp.com/")
    
    tab1, tab2 = st.tabs(["Pipeline", "Simulador LipeDefinition®"])
    
    with tab1:
        st.subheader("Gestão de Pacientes")
        edited_crm = st.data_editor(df_crm, num_rows="dynamic", use_container_width=True)
        if st.button("Salvar CRM"):
            edited_crm.to_csv(DATA_FILE_CRM, index=False)
            st.session_state.db_crm = edited_crm
            st.success("Salvo!")
    
    with tab2:
        st.subheader("Simulador de Orçamento")
        c1, c2 = st.columns(2)
        with c1:
            eq = st.number_input("Equipe Médica", value=8150.0)
            hosp = st.selectbox("Hospital", ["Perinatal (R$ 5.988)", "Barra D'or (R$ 14.000)", "Copa Star (R$ 23.108)"])
            val_hosp = 5988.0 if "Perinatal" in hosp else (14000.0 if "Barra" in hosp else 23108.0)
        with c2:
            tec = st.number_input("Tecnologias (Argo/Morpheus)", value=35400.0)
            pos = st.number_input("Pós (Fisio/Cinta)", value=12050.0)
            
        total = eq + val_hosp + tec + pos
        st.markdown(f"### Total Estimado: R$ {total:,.2f}")
        if st.button("Enviar para Pipeline"):
            novo = pd.DataFrame([{"Nome": "Novo Orçamento", "Status": "Negociação", "Valor": total}])
            st.session_state.db_crm = pd.concat([st.session_state.db_crm, novo], ignore_index=True)
            st.session_state.db_crm.to_csv(DATA_FILE_CRM, index=False)
            st.success("Enviado!")
