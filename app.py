import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
from datetime import datetime, date
import requests
import pdfplumber
import numpy as np
from fpdf import FPDF
import io
import google.generativeai as genai
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json

# --- CONFIGURAÇÃO INICIAL ---
st.set_page_config(page_title="Blue System", layout="wide", page_icon="🟦")

# --- ESTILOS VISUAIS (DARK MODE ELITE) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    .stApp { background-color: #0b1120; color: #e6f1ff; font-family: 'Inter', sans-serif; }
    .blue-logo { font-family: 'Inter', sans-serif; font-weight: 200; font-size: 3rem; color: #e6f1ff; letter-spacing: -3px; margin-bottom: -10px; }
    .blue-dot { color: #00f2ff; font-weight: bold; }
    .blue-sub { font-family: 'Inter', sans-serif; font-weight: 400; font-size: 0.8rem; letter-spacing: 4px; color: #00f2ff; text-transform: uppercase; margin-left: 5px; opacity: 0.9; }
    div[data-testid="stMetric"] { background: linear-gradient(145deg, #161b2e 0%, #0b1120 100%); border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.05); padding: 20px; }
    .stButton > button { background: linear-gradient(90deg, #00f2ff 0%, #0066ff 100%); color: #fff; border: none; border-radius: 8px; font-weight: 700; text-transform: uppercase; width: 100%; transition: all 0.3s ease; }
    .stButton > button:hover { transform: scale(1.02); box-shadow: 0 0 20px rgba(0, 242, 255, 0.5); }
    .status-box { padding: 15px; border-radius: 12px; text-align: center; font-weight: 800; font-size: 1.2rem; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; }
    [data-testid="stSidebar"] { background-color: #0f172a; border-right: 1px solid #1e293b; }
    
    /* Progress Bar Custom */
    .stProgress > div > div > div > div { background-color: #00f2ff; }
    </style>
""", unsafe_allow_html=True)

# --- SISTEMA DE LOGIN ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_system' not in st.session_state: st.session_state.current_system = None

def check_login():
    # Tenta pegar senha do Secrets, se não tiver usa padrão
    senha = st.secrets["password"] if "password" in st.secrets else "blue2026"
    if st.session_state.pass_input == senha: st.session_state.logged_in = True
    else: st.error("Senha incorreta.")

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
        if st.button("ACESSAR FINANCEIRO"): st.session_state.current_system = "Financeiro"; st.rerun()
    with c2:
        st.info("💎 DEPARTAMENTO COMERCIAL")
        if st.button("ACESSAR COMERCIAL"): st.session_state.current_system = "Comercial"; st.rerun()
    if st.sidebar.button("Sair"): st.session_state.logged_in = False; st.rerun()
    st.stop()

with st.sidebar:
    if st.button("⬅️ VOLTAR AO MENU"): st.session_state.current_system = None; st.rerun()
    st.markdown("---")

# ==============================================================================
# SISTEMA FINANCEIRO (BLUEFIN)
# ==============================================================================
if st.session_state.current_system == "Financeiro":
    DATA_FILE = "financeiro_blue.csv"
    HISTORICO_FILES = ["fechamento-de-caixa-57191-6a9ad554-2fa6-41ba-b652-ea0b4c6805e9.xlsx - sheet1.csv", "fechamento-de-caixa-57191-83a36dcc-011c-4146-a04a-1c7fb0101e42.xlsx - sheet1.csv", "fechamento-de-caixa-57191-f6c1cd85-0cf2-4258-9503-b1120442cbb3.xlsx - sheet1.csv"]

    def normalize_columns_fin(df):
        df.columns = [str(c).strip().lower() for c in df.columns]
        mapping = {'vencimento': 'Data', 'data de pagamento': 'Data', 'pagamento': 'Data', 'dt': 'Data', 'date': 'Data', 'data': 'Data', 'valor líquido r$': 'Valor', 'valor original r$': 'Valor', 'valor_pago': 'Valor', 'total': 'Valor', 'valor': 'Valor', 'vl pago': 'Valor', 'valor$': 'Valor', 'valor r$': 'Valor', 'pago a / recebido de': 'Subcategoria', 'favorecido': 'Subcategoria', 'cliente': 'Subcategoria', 'paciente': 'Subcategoria', 'nome': 'Subcategoria', 'descrição': 'Descrição', 'histórico': 'Descrição'}
        df = df.rename(columns=mapping)
        df = df.loc[:, ~df.columns.duplicated()]
        for col in ["Data", "Tipo", "Categoria", "Subcategoria", "Descrição", "Valor", "Status"]: 
            if col not in df.columns: df[col] = ""
        
        def clean_val(x):
            try: return float(str(x).replace('R$','').replace(' ','').replace('.','').replace(',','.'))
            except: return 0.0
            
        df['Valor'] = df['Valor'].apply(clean_val)
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Data'])
        def get_type(row):
            val = row['Valor']; desc = str(row.get('Descrição', '')).lower() + str(row.get('Tipo', '')).lower()
            if val < 0 or any(x in desc for x in ['saída', 'saida', 'despesa', 'pgto', 'pagamento', 'sangria']): return 'Saída'
            return 'Entrada'
        df['Tipo'] = df.apply(get_type, axis=1); df['Valor'] = df['Valor'].abs(); df['Mês'] = df['Data'].dt.strftime("%Y-%m"); df['Ano'] = df['Data'].dt.year
        return df

    def read_any_file(uploaded_file):
        try:
            if uploaded_file.name.endswith('.csv'): 
                try: return pd.read_csv(uploaded_file)
                except: return pd.read_csv(uploaded_file, sep=';')
            elif uploaded_file.name.endswith(('.xls', '.xlsx')): return pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith('.pdf'):
                with pdfplumber.open(uploaded_file) as pdf: text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()]); return pd.DataFrame({'Dados Extraídos': text.split('\n')})
        except: return pd.DataFrame()

    class PDFReceipt(FPDF):
        def header(self):
            self.set_font('Arial', '', 32); self.set_text_color(0, 0, 0); self.cell(0, 15, 'blue .', 0, 1, 'C'); self.ln(5); self.set_draw_color(200, 200, 200); self.line(20, self.get_y(), 190, self.get_y()); self.ln(10)

    def generate_receipt_pro(tipo, nome, valor, ref, dt):
        pdf = PDFReceipt(); pdf.add_page(); pdf.set_y(50); pdf.set_font("Arial", 'B', 14); pdf.set_text_color(20, 20, 20)
        titulo = "COMPROVANTE" if tipo == "Pagamento" else "RECIBO"
        pdf.cell(0, 10, titulo, 0, 1, 'C'); pdf.ln(5); pdf.set_font("Arial", 'B', 28); pdf.cell(0, 15, f"R$ {valor:,.2f}", 0, 1, 'C')
        pdf.ln(15); pdf.set_font("Arial", '', 11); pdf.set_text_color(60, 60, 60)
        cnpj_blue, nome_blue = "48.459.860/0001-14", "BLUE CLINICA MEDICA E CIRURGICA LTDA"
        texto = f"Recebemos de {nome.upper()}, a quantia de R$ {valor:,.2f}, referente a: {ref}." if tipo == "Recebimento" else f"Pagamos a {nome.upper()}, a quantia de R$ {valor:,.2f}, referente a: {ref}."
        p1, p2 = ("Pagador:", "Beneficiário:") if tipo == "Recebimento" else ("Pagador:", "Beneficiário:")
        pdf.set_x(25); pdf.multi_cell(160, 8, texto.encode('latin-1','replace').decode('latin-1'), 0, 'C')
        pdf.ln(30); pdf.set_font("Arial", 'B', 9); pdf.cell(95, 5, p1, 0, 0, 'L'); pdf.cell(95, 5, p2, 0, 1, 'L')
        pdf.set_font("Arial", '', 9); pdf.cell(95, 5, nome.upper() if tipo=="Recebimento" else nome_blue, 0, 0, 'L'); pdf.cell(95, 5, f"{nome_blue} - {cnpj_blue}" if tipo=="Recebimento" else nome.upper(), 0, 1, 'L')
        pdf.set_y(230); pdf.cell(0, 5, f"Rio de Janeiro, {dt.strftime('%d de %B de %Y')}", 0, 1, 'C'); pdf.ln(20); pdf.cell(0, 5, "_________________________________", 0, 1, 'C'); pdf.cell(0, 5, "Assinatura", 0, 1, 'C')
        return pdf.output(dest='S').encode('latin-1', 'replace')

    if 'db_fin' not in st.session_state:
        if os.path.exists(DATA_FILE): st.session_state.db_fin = pd.read_csv(DATA_FILE); st.session_state.db_fin['Data'] = pd.to_datetime(st.session_state.db_fin['Data'])
        else:
            dfs = []
            for f in HISTORICO_FILES:
                if os.path.exists(f): 
                    try: dfs.append(normalize_columns_fin(pd.read_csv(f, sep=';') if ';' in open(f).readline() else pd.read_csv(f)))
                    except: pass
            if dfs: st.session_state.db_fin = pd.concat(dfs, ignore_index=True); st.session_state.db_fin.to_csv(DATA_FILE, index=False)
            else: st.session_state.db_fin = pd.DataFrame(columns=["Data", "Tipo", "Valor", "Categoria", "Descrição", "Subcategoria", "Mês", "Ano"])

    df = st.session_state.db_fin
    st.markdown("<div class='blue-logo'>blue<span class='blue-dot'>.</span></div><div class='blue-sub'>Financeiro</div><hr>", unsafe_allow_html=True)
    if 'cofre' not in st.session_state: st.session_state.cofre = 0.0
    st.session_state.cofre = st.sidebar.number_input("Valor Cofre (R$)", value=st.session_state.cofre)
    
    tab1, tab2, tab3 = st.tabs(["Dashboard", "Lançamentos", "Automação"])
    with tab1:
        rec, desp = df[df['Tipo']=='Entrada']['Valor'].sum(), df[df['Tipo']=='Saída']['Valor'].sum(); saldo = rec - desp; total = saldo + st.session_state.cofre
        st.markdown(f"<div class='status-box' style='color:{'#00ff88' if total>0 else '#ff3333'}; border:1px solid {'#00ff88' if total>0 else '#ff3333'}'>SALDO TOTAL: R$ {total:,.2f}</div>", unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3); c1.metric("Receita", f"R$ {rec:,.2f}"); c2.metric("Despesas", f"R$ {desp:,.2f}"); c3.metric("No Banco", f"R$ {saldo:,.2f}")
        if not df.empty: st.bar_chart(df, x='Mês', y='Valor', color='Tipo')
    with tab2:
        edited = st.data_editor(df, num_rows="dynamic", use_container_width=True)
        if st.button("Salvar Fin"): edited.to_csv(DATA_FILE, index=False); st.session_state.db_fin = edited; st.success("Salvo!"); st.rerun()
    with tab3:
        # RECIBOS
        with st.expander("Gerar Recibo"):
            with st.form("rec"):
                tp = st.radio("Tipo", ["Recebimento", "Pagamento"], horizontal=True); nm = st.text_input("Nome"); vl = st.number_input("Valor"); rf = st.text_area("Ref"); dt = st.date_input("Data")
                if st.form_submit_button("Gerar PDF"):
                   pdf_bytes = generate_receipt_pro(tp, nm, vl, rf, dt); st.download_button("Baixar PDF", pdf_bytes, "recibo.pdf", "application/pdf")

        # CONCILIAÇÃO
        st.markdown("### Conciliação Bancária")
        up = st.file_uploader("Extrato Banco", type=['csv', 'xlsx', 'pdf'])
        if up and st.button("Conciliar"):
             clean = normalize_columns_fin(read_any_file(up))
             if not clean.empty:
                s_ent = df[df['Tipo']=='Entrada']['Valor'].sum(); b_ent = clean[clean['Tipo']=='Entrada']['Valor'].sum()
                st.metric("Diferença Entradas", f"R$ {s_ent - b_ent:,.2f}")
                st.dataframe(clean)

# ==============================================================================
# SISTEMA COMERCIAL (BLUECRM) - SUPER ATUALIZADO
# ==============================================================================
elif st.session_state.current_system == "Comercial":
    DATA_FILE_CRM = "comercial_blue.csv"
    
    # --- FUNÇÕES COMERCIAIS ---
    def load_crm():
        if os.path.exists(DATA_FILE_CRM): 
            df = pd.read_csv(DATA_FILE_CRM)
            cols_new = ["Tipo Procedimento", "Plano de Saúde", "Desconto (%)", "Sinal Pago (R$)", "Anotações", "Data Cirurgia", "Data Consulta"]
            for c in cols_new:
                if c not in df.columns: df[c] = "" if "R$" not in c and "%" not in c else 0.0
            return df
        return pd.DataFrame({
            "Nome": ["Paciente Exemplo"], "Status": ["Negociação"], "Valor Total": [0.0], "Pago": [0.0],
            "Tipo Procedimento": ["Lipedema"], "Plano de Saúde": ["Não"], "Sinal Pago (R$)": [0.0],
            "Data Consulta": [datetime.now().strftime("%Y-%m-%d")], "Anotações": ["Interessada no Morpheus"]
        })

    def save_crm(df): df.to_csv(DATA_FILE_CRM, index=False)
    
    if 'db_crm' not in st.session_state: st.session_state.db_crm = load_crm()
    df_crm = st.session_state.db_crm.copy()
    
    # --- BARRA LATERAL ---
    st.markdown("<div class='blue-logo'>blue<span class='blue-dot'>.</span></div><div class='blue-sub'>Comercial & CRM</div><hr>", unsafe_allow_html=True)
    
    # KPIs de Conversão
    try:
        total_consultas = len(df_crm)
        fechados = len(df_crm[df_crm['Status'].isin(["Fechado", "Cirurgia Realizada", "Sinal Pago"])])
        taxa_conv = (fechados / total_consultas * 100) if total_consultas > 0 else 0
        
        c1, c2, c3 = st.sidebar.columns(3)
        c1.metric("Leads", total_consultas)
        c2.metric("Fechados", fechados)
        c3.metric("Conv.", f"{taxa_conv:.0f}%")
        st.sidebar.markdown("---")
        
        # Resumo Financeiro Comercial
        pipeline = df_crm[~df_crm['Status'].isin(['Lost'])]['Valor Total'].sum()
        recebido = df_crm['Pago'].sum() + df_crm['Sinal Pago (R$)'].sum()
        st.sidebar.metric("Pipeline (Potencial)", f"R$ {pipeline:,.2f}")
        st.sidebar.metric("Já Recebido (Sinais)", f"R$ {recebido:,.2f}")
    except: pass
    
    st.sidebar.markdown("---")
    st.sidebar.link_button("📅 Abrir TimeTree", "https://treeapp.com/")
    
    # --- ABAS DO COMERCIAL ---
    t1, t2, t3, t4, t5 = st.tabs(["📊 Pipeline Geral", "📋 Patient Tracker", "💰 Simulador", "📥 Importar/Exportar", "🤖 Blue AI & Nuvem"])
    
    # 1. PIPELINE GERAL
    with t1:
        st.subheader("Funil de Vendas")
        
        # Filtros
        c1, c2 = st.columns(2)
        f_status = c1.multiselect("Filtrar Status", ["1ª Consulta", "Orçamento Aberto", "Negociação", "Sinal Pago", "Cirurgia Agendada", "Fechado", "Lost"])
        f_proc = c2.multiselect("Filtrar Procedimento", ["Lipedema", "Botox", "Morpheus", "Bioestimulador", "Vibrofit", "Sublift", "Outro"])
        
        df_view = df_crm.copy()
        if f_status: df_view = df_view[df_view['Status'].isin(f_status)]
        if f_proc: df_view = df_view[df_view['Tipo Procedimento'].isin(f_proc)]
        
        edited_crm = st.data_editor(
            df_view, 
            num_rows="dynamic", 
            use_container_width=True,
            column_config={
                "Valor Total": st.column_config.NumberColumn(format="R$ %.2f"),
                "Pago": st.column_config.NumberColumn(format="R$ %.2f"),
                "Sinal Pago (R$)": st.column_config.NumberColumn(format="R$ %.2f"),
                "Desconto (%)": st.column_config.NumberColumn(format="%.0f%%"),
                "Status": st.column_config.SelectboxColumn(
                    options=["1ª Consulta", "Orçamento Aberto", "Negociação", "Sinal Pago", "Cirurgia Agendada", "Fechado", "Lost"],
                    required=True
                ),
                "Tipo Procedimento": st.column_config.SelectboxColumn(
                    options=["Lipedema", "Botox", "Morpheus", "Bioestimulador", "Vibrofit", "Sublift", "Outro"]
                ),
                "Plano de Saúde": st.column_config.SelectboxColumn(options=["Não", "Sim (Reembolso)", "Sim (Direto)"]),
                "Data Consulta": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Data Cirurgia": st.column_config.DateColumn(format="DD/MM/YYYY"),
                "Anotações": st.column_config.TextColumn(width="large")
            }
        )
        
        if not edited_crm.equals(df_view):
            if st.button("💾 SALVAR CRM", type="primary"):
                st.session_state.db_crm = edited_crm
                save_crm(edited_crm)
                st.success("CRM Atualizado!")
                st.rerun()

    # 2. PATIENT TRACKER
    with t2:
        st.subheader("Rastreador de Paciente")
        paciente = st.selectbox("Selecione a Paciente", df_crm['Nome'].unique())
        
        if paciente:
            p_data = df_crm[df_crm['Nome'] == paciente].iloc[0]
            
            # Barra de Status
            status_map = {"1ª Consulta": 10, "Orçamento Aberto": 30, "Negociação": 50, "Sinal Pago": 70, "Cirurgia Agendada": 90, "Fechado": 100, "Lost": 0}
            progresso = status_map.get(p_data['Status'], 0)
            
            st.write(f"**Status Atual:** {p_data['Status']}")
            st.progress(progresso)
            
            c1, c2, c3 = st.columns(3)
            c1.info(f"**Procedimento:** {p_data.get('Tipo Procedimento', '-')}")
            c2.warning(f"**Valor Total:** R$ {p_data.get('Valor Total', 0):,.2f}")
            c3.success(f"**Pago (Sinal+Total):** R$ {p_data.get('Pago', 0) + p_data.get('Sinal Pago (R$)', 0):,.2f}")
            
            st.markdown("#### Detalhes")
            col_check, col_note = st.columns(2)
            with col_check:
                st.checkbox("Orçamento Enviado", value=progresso >= 30, disabled=True)
                st.checkbox("Sinal Recebido", value=progresso >= 70, disabled=True)
                st.checkbox("Termos Assinados", value=progresso >= 90)
                st.checkbox("Exames Pré-Op OK", value=progresso >= 90)
                st.text(f"Plano: {p_data.get('Plano de Saúde', 'Não')}")
            with col_note:
                st.text_area("Anotações (Visualização)", value=str(p_data.get('Anotações', '')), height=150, disabled=True)
                st.caption("Edite as notas na aba 'Pipeline Geral'")

    # 3. SIMULADOR
    with t3:
        st.subheader("Simulador LipeDefinition®")
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
        
        if st.button("Salvar Simulação no CRM"):
            novo = pd.DataFrame([{"Nome": "Novo Orçamento", "Status": "Orçamento Aberto", "Valor Total": total, "Tipo Procedimento": "Lipedema", "Data Consulta": datetime.now().strftime("%Y-%m-%d")}])
            st.session_state.db_crm = pd.concat([st.session_state.db_crm, novo], ignore_index=True)
            save_crm(st.session_state.db_crm)
            st.success("Salvo no Funil!")

    # 4. IMPORTAR/EXPORTAR
    with t4:
        st.subheader("Central de Arquivos")
        c_imp, c_exp = st.columns(2)
        
        with c_imp:
            st.markdown("#### 📥 Importar Inteligente")
            up_crm = st.file_uploader("Arquivo (Excel/CSV/PDF)", type=['csv', 'xlsx', 'pdf'], key="crm_up")
            if up_crm:
                try:
                    df_imp = pd.DataFrame()
                    if up_crm.name.endswith('.pdf'):
                        with pdfplumber.open(up_crm) as pdf: 
                            txt = "\n".join([p.extract_text() for p in pdf.pages])
                            # Tenta extrair dados básicos do texto
                            st.info("Texto extraído do PDF. Revise antes de importar.")
                            st.text_area("Prévia", txt[:500] + "...", height=100)
                            # Simulação de extração
                            if "Total" in txt: val_est = 0.0
                            else: val_est = 0.0
                            df_imp = pd.DataFrame([{"Nome": "Paciente PDF Importado", "Anotações": "Importado via PDF", "Status": "1ª Consulta"}])
                    else:
                        df_imp = pd.read_excel(up_crm) if up_crm.name.endswith('.xlsx') else pd.read_csv(up_crm)
                        st.dataframe(df_imp.head(3))
                        
                    if st.button("Confirmar Importação"):
                        # Mapeamento Genérico
                        novo_df = pd.DataFrame()
                        novo_df['Nome'] = df_imp.iloc[:, 0] if not df_imp.empty else ["Desconhecido"] # Pega primeira coluna como nome
                        novo_df['Status'] = '1ª Consulta'
                        for c in ["Tipo Procedimento", "Plano de Saúde", "Anotações"]: novo_df[c] = ""
                        for c in ["Valor Total", "Pago", "Sinal Pago (R$)"]: novo_df[c] = 0.0
                        
                        st.session_state.db_crm = pd.concat([st.session_state.db_crm, novo_df], ignore_index=True)
                        save_crm(st.session_state.db_crm)
                        st.success("Importado!")
                except Exception as e: st.error(f"Erro: {e}")

        with c_exp:
            st.markdown("#### 📤 Exportar Backup")
            st.download_button("Baixar CSV Completo", df_crm.to_csv(index=False).encode('utf-8'), "crm_backup.csv", "text/csv")

    # 5. IA & INTEGRAÇÕES
    with t5:
        st.title("🤖 Blue Intelligence & Nuvem")
        
        c1, c2 = st.columns(2)
        
        with c1:
            st.markdown("### ☁️ Google Sheets Sync")
            sheet_id = st.text_input("ID da Planilha Google", placeholder="Ex: 1BxiMVs...")
            
            if st.button("🔄 Sincronizar CRM Agora"):
                if "GOOGLE_SHEETS_KEY" in st.secrets and sheet_id:
                    try:
                        creds_dict = json.loads(st.secrets["GOOGLE_SHEETS_KEY"])
                        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
                        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
                        client = gspread.authorize(creds)
                        sh = client.open_by_key(sheet_id)
                        try: worksheet = sh.worksheet("CRM_Backup")
                        except: worksheet = sh.add_worksheet(title="CRM_Backup", rows="1000", cols="20")
                        worksheet.clear()
                        worksheet.update([df_crm.columns.values.tolist()] + df_crm.astype(str).values.tolist())
                        st.success("✅ Enviado para o Google Sheets!")
                    except Exception as e: st.error(f"Erro: {e}")
                else: st.warning("Configure o Secrets (GOOGLE_SHEETS_KEY) e informe o ID.")

        with c2:
            st.markdown("### 🧠 Gemini Sales Coach")
            api_key = st.text_input("Chave API Gemini", type="password")
            if not api_key and "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]
            
            proc_ia = st.selectbox("Procedimento", ["Lipedema", "Botox", "Morpheus", "Outro"])
            obj_ia = st.text_input("Objeção da Paciente", placeholder="Ex: Achou caro...")
            
            if st.button("Gerar Script"):
                if api_key:
                    try:
                        genai.configure(api_key=api_key)
                        model = genai.GenerativeModel('gemini-pro')
                        resp = model.generate_content(f"Aja como consultora de luxo da Blue Clinic. A paciente quer {proc_ia} mas disse: '{obj_ia}'. Crie resposta curta e persuasiva p/ WhatsApp.")
                        st.info(resp.text)
                    except Exception as e: st.error(f"Erro IA: {e}")
                else: st.warning("Insira a Chave API ou configure nos Secrets.")
