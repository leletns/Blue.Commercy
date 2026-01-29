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

# --- CONFIGURAÇÃO INICIAL (GLOBAL) ---
st.set_page_config(page_title="Blue System", layout="wide", page_icon="🟦")

# --- ESTILO VISUAL (GLOBAL) ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;800&display=swap');
    .stApp { background-color: #0b1120; color: #e6f1ff; font-family: 'Inter', sans-serif; }
    
    /* Logo */
    .blue-logo { font-family: 'Inter', sans-serif; font-weight: 200; font-size: 3rem; color: #e6f1ff; letter-spacing: -3px; margin-bottom: -10px; text-shadow: 0 0 10px rgba(0, 242, 255, 0.3); }
    .blue-dot { color: #00f2ff; font-weight: bold; }
    .blue-sub { font-family: 'Inter', sans-serif; font-weight: 400; font-size: 0.8rem; letter-spacing: 4px; color: #00f2ff; text-transform: uppercase; margin-left: 5px; opacity: 0.9; }
    
    /* Login Box */
    .login-box { background: linear-gradient(145deg, #161b2e 0%, #0b1120 100%); padding: 40px; border-radius: 20px; border: 1px solid rgba(0, 242, 255, 0.1); box-shadow: 0 20px 50px rgba(0,0,0,0.5); text-align: center; }
    
    /* Métricas */
    div[data-testid="stMetric"] { background: linear-gradient(145deg, #161b2e 0%, #0b1120 100%); border-radius: 15px; border: 1px solid rgba(255, 255, 255, 0.05); padding: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 800 !important; color: #fff !important; }
    
    /* Botões */
    .stButton > button { background: linear-gradient(90deg, #00f2ff 0%, #0066ff 100%); color: #fff; border: none; border-radius: 8px; font-weight: 700; text-transform: uppercase; transition: all 0.3s ease; width: 100%; }
    .stButton > button:hover { transform: scale(1.02); box-shadow: 0 0 20px rgba(0, 242, 255, 0.5); }
    
    /* Inputs */
    [data-testid="stDataFrame"], [data-testid="stDataEditor"] { border: 1px solid #1f2937; border-radius: 10px; background-color: #111827; }
    .stTextInput input, .stNumberInput input, .stSelectbox div, .stDateInput input, .stTextArea textarea { background-color: #1f2937 !important; color: #fff !important; border: 1px solid #374151 !important; border-radius: 8px; }
    
    /* Status Box */
    .status-box { padding: 15px; border-radius: 12px; text-align: center; font-weight: 800; font-size: 1.2rem; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px; box-shadow: 0 5px 15px rgba(0,0,0,0.3); }
    </style>
    """, unsafe_allow_html=True)

# --- SISTEMA DE LOGIN E NAVEGAÇÃO ---
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'current_system' not in st.session_state: st.session_state.current_system = None # None, 'Financeiro', 'Comercial'

def check_login():
    senha_correta = "blue2026" # Senha fixa para facilitar
    # Tenta ler do secrets se existir
    if "password" in st.secrets: senha_correta = st.secrets["password"]
    
    if st.session_state.password_input == senha_correta:
        st.session_state.logged_in = True
    else:
        st.error("Senha incorreta.")

if not st.session_state.logged_in:
    # TELA DE LOGIN
    st.markdown("<br><br>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.markdown("<div class='blue-logo' style='text-align:center'>blue<span class='blue-dot'>.</span></div>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; letter-spacing: 3px; color: #00f2ff; opacity: 0.7; text-transform: uppercase; margin-bottom: 40px;'>Operating System</p>", unsafe_allow_html=True)
        st.text_input("CHAVE DE ACESSO", type="password", key="password_input", on_change=check_login)
        st.button("ENTRAR", on_click=check_login)
    st.stop() # Para o código aqui se não estiver logado

# SELEÇÃO DE MÓDULO (Menu Principal)
if st.session_state.current_system is None:
    st.sidebar.markdown("<div class='blue-logo'>blue<span class='blue-dot'>.</span></div>", unsafe_allow_html=True)
    st.title("Bem-vinda ao Ecossistema Blue")
    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.info("💰 GESTÃO FINANCEIRA")
        if st.button("ACESSAR FINANCEIRO"): st.session_state.current_system = "Financeiro"; st.rerun()
    with c2:
        st.info("💎 GESTÃO COMERCIAL")
        if st.button("ACESSAR COMERCIAL"): st.session_state.current_system = "Comercial"; st.rerun()
    st.markdown("---")
    if st.button("Sair"): st.session_state.logged_in = False; st.rerun()
    st.stop()

# Botão de Voltar no Sidebar
with st.sidebar:
    if st.button("⬅️ Voltar ao Menu Principal"):
        st.session_state.current_system = None
        st.rerun()

# ==============================================================================
# MÓDULO FINANCEIRO (Código Completo)
# ==============================================================================
if st.session_state.current_system == "Financeiro":
    
    # ... FUNÇÕES DO FINANCEIRO ...
    DATA_FILE = "financeiro_blue.csv"
    HISTORICO_FILES = [
        "fechamento-de-caixa-57191-6a9ad554-2fa6-41ba-b652-ea0b4c6805e9.xlsx - sheet1.csv",
        "fechamento-de-caixa-57191-83a36dcc-011c-4146-a04a-1c7fb0101e42.xlsx - sheet1.csv",
        "fechamento-de-caixa-57191-f6c1cd85-0cf2-4258-9503-b1120442cbb3.xlsx - sheet1.csv"
    ]

    def smart_categorize_fin(row):
        text = (str(row.get('Descrição', '')) + " " + str(row.get('Categoria', '')) + " " + str(row.get('Subcategoria', ''))).lower()
        if 'lipedema' in text: return 'Consulta Lipedema'
        if 'cirurgia' in text: return 'Cirurgia'
        if 'consulta' in text: return 'Consulta Clínica'
        if any(x in text for x in ['botox', 'preenchimento', 'cosmiatria', 'estetica', 'procedimento']): return 'Procedimento Estético'
        if any(x in text for x in ['remedio', 'medicamento', 'farmacia', 'drogaria', 'estoque']): return 'Estoque/Medicamento'
        if any(x in text for x in ['material', 'luva', 'gaze', 'seringa']): return 'Material Cirúrgico'
        if any(x in text for x in ['aluguel', 'condominio', 'luz', 'agua', 'internet', 'vivo', 'claro']): return 'Custos Fixos'
        if any(x in text for x in ['pro-labore', 'pro labore', 'salario', 'folha']): return 'Pessoal/Salários'
        if any(x in text for x in ['sangria', 'retirada', 'sócio', 'distribuição', 'cofre']): return 'Retirada de Caixa/Sangria'
        if any(x in text for x in ['taxa', 'imposto', 'simples', 'das']): return 'Impostos/Taxas'
        return row.get('Categoria', 'Outros')

    def normalize_columns_fin(df):
        df.columns = [str(c).strip().lower() for c in df.columns]
        mapping = {
            'vencimento': 'Data', 'data de pagamento': 'Data', 'pagamento': 'Data', 'dt': 'Data', 'date': 'Data', 'data': 'Data',
            'valor líquido r$': 'Valor', 'valor original r$': 'Valor', 'valor_pago': 'Valor', 'total': 'Valor', 'amount': 'Valor', 'valor': 'Valor', 
            'vl pago': 'Valor', 'valor$': 'Valor', 'valor $': 'Valor', 'valor (r$)': 'Valor', 'vl.': 'Valor', 'preço': 'Valor',
            'pago a / recebido de': 'Subcategoria', 'favorecido': 'Subcategoria', 'cliente': 'Subcategoria', 'paciente': 'Subcategoria', 'nome': 'Subcategoria',
            'descrição': 'Descrição', 'histórico': 'Descrição', 'description': 'Descrição'
        }
        df = df.rename(columns=mapping)
        df = df.loc[:, ~df.columns.duplicated()]
        
        for col in ["Data", "Tipo", "Categoria", "Subcategoria", "Descrição", "Valor", "Status", "Forma Pagamento"]:
            if col not in df.columns: df[col] = datetime.now() if col == "Data" else (0.0 if col == "Valor" else "")

        def clean_currency(x):
            if isinstance(x, (int, float)): return float(x)
            s = str(x).replace('R$', '').replace('$', '').replace(' ', '')
            if ',' in s and '.' in s: s = s.replace('.', '').replace(',', '.')
            elif ',' in s: s = s.replace(',', '.')
            try: return float(s)
            except: return 0.0
            
        df['Valor'] = df['Valor'].apply(clean_currency)
        df['Data'] = pd.to_datetime(df['Data'], dayfirst=True, errors='coerce')
        df = df.dropna(subset=['Data'])

        def determine_type(row):
            valor = row['Valor']
            desc = (str(row.get('Descrição', '')) + " " + str(row.get('Tipo', '')) + " " + str(row.get('Subcategoria', ''))).lower()
            if valor < 0: return 'Saída'
            if any(k in desc for k in ['saída', 'saida', 'despesa', 'débito', 'sangria', 'pagamento', 'pgto', 'boleto', 'conta', 'taxa', 'imposto', 'fornecedor', 'aluguel', 'luz']): return 'Saída'
            return 'Entrada'

        df['Tipo'] = df.apply(determine_type, axis=1)
        df['Valor'] = df['Valor'].abs()
        
        if 'Categoria' not in df.columns or df['Categoria'].isnull().all():
             df['Categoria'] = df.apply(smart_categorize_fin, axis=1)
        else:
             df['Categoria'] = df.apply(lambda row: smart_categorize_fin(row) if row['Categoria'] in ['', 'Outros', 'nan', None] else row['Categoria'], axis=1)

        df['Mês'] = df['Data'].dt.strftime("%Y-%m")
        df['Ano'] = df['Data'].dt.year.astype(int)
        return df

    def init_db_from_history():
        dfs = []
        found = 0
        for file in HISTORICO_FILES:
            if os.path.exists(file):
                try:
                    try: df_t = pd.read_csv(file)
                    except: df_t = pd.read_csv(file, sep=';')
                    if not df_t.empty:
                        dfs.append(normalize_columns_fin(df_t))
                        found += 1
                except: pass
        if dfs:
            full_df = pd.concat(dfs, ignore_index=True).sort_values(by="Data")
            full_df.to_csv(DATA_FILE, index=False)
            return True, found
        return False, 0

    def load_data_fin():
        if not os.path.exists(DATA_FILE):
            success, count = init_db_from_history()
            if success: st.toast(f"Banco restaurado de {count} arquivos!", icon="♻️")
        if os.path.exists(DATA_FILE): return normalize_columns_fin(pd.read_csv(DATA_FILE))
        return pd.DataFrame(columns=["Data", "Tipo", "Categoria", "Subcategoria", "Descrição", "Valor", "Status", "Forma Pagamento", "Mês", "Ano"])

    def save_data_fin(df): df.to_csv(DATA_FILE, index=False)

    def get_market_data():
        try:
            r = requests.get("https://economia.awesomeapi.com.br/last/USD-BRL,EUR-BRL", timeout=2).json()
            return float(r['USDBRL']['bid']), float(r['USDBRL']['pctChange']), float(r['EURBRL']['bid']), float(r['EURBRL']['pctChange'])
        except: return None, 0, None, 0

    class PDFReceipt(FPDF):
        def header(self):
            self.set_font('Arial', '', 32); self.set_text_color(0, 0, 0); self.cell(0, 15, 'blue .', 0, 1, 'C')
            self.ln(5); self.set_draw_color(200, 200, 200); self.set_line_width(0.1); self.line(20, self.get_y(), 190, self.get_y()); self.ln(10)

    def generate_receipt_pro(tipo, nome, valor, ref, dt):
        pdf = PDFReceipt(); pdf.add_page(); pdf.set_y(50); pdf.set_font("Arial", 'B', 14); pdf.set_text_color(20, 20, 20)
        titulo = "COMPROVANTE" if tipo == "Pagamento" else "RECIBO"
        pdf.cell(0, 10, titulo, 0, 1, 'C'); pdf.ln(5); pdf.set_font("Arial", 'B', 28); pdf.cell(0, 15, f"R$ {valor:,.2f}", 0, 1, 'C')
        pdf.ln(15); pdf.set_font("Arial", '', 11); pdf.set_text_color(60, 60, 60)
        cnpj_blue, nome_blue = "48.459.860/0001-14", "BLUE CLINICA MEDICA E CIRURGICA LTDA"
        if tipo == "Recebimento": texto = f"Recebemos de {nome.upper()}, a quantia de R$ {valor:,.2f}, referente a: {ref}."; p1, p2 = "Pagador:", "Beneficiário:"
        else: texto = f"Pagamos a {nome.upper()}, a quantia de R$ {valor:,.2f}, referente a: {ref}."; p1, p2 = "Pagador:", "Beneficiário:"
        pdf.set_x(25); pdf.multi_cell(160, 8, texto.encode('latin-1','replace').decode('latin-1'), 0, 'C')
        pdf.ln(30); pdf.set_font("Arial", 'B', 9); pdf.cell(95, 5, p1, 0, 0, 'L'); pdf.cell(95, 5, p2, 0, 1, 'L')
        pdf.set_font("Arial", '', 9); pdf.cell(95, 5, nome.upper() if tipo=="Recebimento" else nome_blue, 0, 0, 'L'); pdf.cell(95, 5, f"{nome_blue} - {cnpj_blue}" if tipo=="Recebimento" else nome.upper(), 0, 1, 'L')
        pdf.set_y(230); pdf.cell(0, 5, f"Rio de Janeiro, {dt.strftime('%d de %B de %Y')}", 0, 1, 'C')
        pdf.ln(20); pdf.cell(0, 5, "__________________________________________________", 0, 1, 'C'); pdf.cell(0, 5, "Assinatura", 0, 1, 'C')
        return pdf.output(dest='S').encode('latin-1', 'replace')

    def read_any_file(uploaded_file):
        try:
            if uploaded_file.name.endswith('.csv'): try: return pd.read_csv(uploaded_file)
            except: return pd.read_csv(uploaded_file, sep=';')
            elif uploaded_file.name.endswith(('.xls', '.xlsx')): return pd.read_excel(uploaded_file)
            elif uploaded_file.name.endswith('.pdf'):
                with pdfplumber.open(uploaded_file) as pdf: text = "\n".join([p.extract_text() for p in pdf.pages if p.extract_text()])
                return pd.DataFrame({'Dados Extraídos': text.split('\n')})
        except: return pd.DataFrame()

    # --- INÍCIO FINANCEIRO ---
    if 'db' not in st.session_state: st.session_state.db = load_data_fin()
    df = st.session_state.db.copy()
    if 'cofre_valor' not in st.session_state: st.session_state.cofre_valor = 0.0

    with st.sidebar:
        st.markdown("<div class='blue-logo'>blue<span class='blue-dot'>.</span></div><div class='blue-sub'>Financeiro Pro</div>", unsafe_allow_html=True)
        st.markdown("---")
        usd, usd_var, eur, eur_var = get_market_data()
        if usd:
            st.caption("🌐 MERCADO"); c1, c2 = st.columns(2); c1.metric("USD", f"R$ {usd:.2f}", f"{usd_var}%"); c2.metric("EUR", f"R$ {eur:.2f}", f"{eur_var}%"); st.markdown("---")
        st.caption("🔒 COFRE (DINHEIRO)"); st.session_state.cofre_valor = st.number_input("Valor Físico (R$)", min_value=0.0, value=st.session_state.cofre_valor, step=100.0); st.markdown(f"**Total:** R$ {st.session_state.cofre_valor:,.2f}"); st.markdown("---")
        menu_fin = st.radio("MENU FINANCEIRO", ["Dashboard", "Lançamentos (Data Center)", "Automação & Conciliação"])

    if menu_fin == "Dashboard":
        t1, t2 = st.tabs(["📊 Visão Geral", "📈 Análise"])
        with t1:
            try:
                rec, desp = df[df['Tipo'] == "Entrada"]['Valor'].sum(), df[df['Tipo'] == "Saída"]['Valor'].sum()
                saldo, saldo_tot = rec - desp, rec - desp + st.session_state.cofre_valor
                if saldo_tot < 0: s_msg, s_bg = "CRÍTICO 🚨", "rgba(255, 51, 51, 0.2)"
                elif 0 <= saldo_tot < 20000: s_msg, s_bg = "EM EQUILÍBRIO ⚠️", "rgba(255, 204, 0, 0.2)"
                elif 20000 <= saldo_tot < 150000: s_msg, s_bg = "SAUDÁVEL ✅", "rgba(0, 255, 136, 0.2)"
                else: s_msg, s_bg = "EXCELENTE 💎", "rgba(0, 242, 255, 0.2)"
                st.markdown(f"<div class='status-box' style='background-color:{s_bg}; color:white;'>STATUS: {s_msg}</div>", unsafe_allow_html=True)
                c1, c2, c3, c4 = st.columns(4)
                c1.metric("Receita", f"R$ {rec:,.2f}", delta="Entradas"); c2.metric("Despesas", f"R$ {desp:,.2f}", delta="-Saídas", delta_color="inverse")
                c3.metric("Saldo Banco", f"R$ {saldo:,.2f}"); c4.metric("Patrimônio (c/ Cofre)", f"R$ {saldo_tot:,.2f}")
                st.markdown("---")
                c1, c2 = st.columns([1, 2])
                with c1: st.subheader("Balanço"); st.plotly_chart(go.Figure(data=[go.Pie(labels=['Entradas', 'Saídas'], values=[rec, desp], hole=.7, marker=dict(colors=['#00ff88', '#ff3333']))]).update_layout(template="plotly_dark", height=300, paper_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
                with c2: 
                    st.subheader("Fluxo Mensal"); df_c = df.groupby(['Ano', 'Mês']).agg({'Valor': lambda x: x[df.loc[x.index, 'Tipo']=='Entrada'].sum() - x[df.loc[x.index, 'Tipo']=='Saída'].sum()}).reset_index().sort_values(['Ano', 'Mês'])
                    st.plotly_chart(go.Figure(go.Scatter(x=df_c['Mês']+"/"+df_c['Ano'].astype(str), y=df_c['Valor'], mode='lines+markers', line=dict(color='#00f2ff'), fill='tozeroy')).update_layout(template="plotly_dark", height=300, paper_bgcolor='rgba(0,0,0,0)'), use_container_width=True)
            except: st.warning("Processando...")

    elif menu_fin == "Lançamentos (Data Center)":
        st.title("Data Center & Filtros")
        c1, c2, c3 = st.columns(3)
        ft_tipo = c1.multiselect("Filtrar Tipo", ["Entrada", "Saída"]); ft_cat = c2.multiselect("Filtrar Categoria", df['Categoria'].unique()); ft_search = c3.text_input("Buscar")
        df_view = df.copy()
        if ft_tipo: df_view = df_view[df_view['Tipo'].isin(ft_tipo)]
        if ft_cat: df_view = df_view[df_view['Categoria'].isin(ft_cat)]
        if ft_search: df_view = df_view[df_view['Descrição'].str.contains(ft_search, case=False, na=False)]
        
        with st.expander("➕ Novo Lançamento Manual"):
            with st.form("manual"):
                c1, c2, c3, c4 = st.columns(4); dt = c1.date_input("Data"); tp = c2.selectbox("Tipo", ["Entrada", "Saída"]); vl = c3.number_input("Valor"); cat = c4.selectbox("Categoria", ["Consulta", "Cirurgia", "Custos", "Pessoal", "Outros"]); desc = st.text_input("Descrição")
                if st.form_submit_button("Lançar"):
                    st.session_state.db = pd.concat([st.session_state.db, normalize_columns_fin(pd.DataFrame([{"Data": pd.to_datetime(dt), "Tipo": tp, "Valor": vl, "Categoria": cat, "Descrição": desc, "Subcategoria": "Manual"}]))], ignore_index=True)
                    save_data_fin(st.session_state.db); st.success("Salvo!"); st.rerun()
        
        edited = st.data_editor(df_view.sort_values("Data", ascending=False), use_container_width=True, num_rows="dynamic", column_config={"Valor": st.column_config.NumberColumn(format="R$ %.2f"), "Data": st.column_config.DateColumn(format="DD/MM/YYYY")})
        if not edited.equals(df_view):
            if st.button("💾 SALVAR EDIÇÕES"):
                if len(df_view)==len(df): 
                    edited['Data'] = pd.to_datetime(edited['Data']); st.session_state.db = edited; save_data_fin(edited); st.success("Salvo!"); st.rerun()
                else: st.warning("Remova filtros para editar.")
        st.download_button("⬇️ Exportar CSV", df_view.to_csv(index=False).encode('utf-8'), "financeiro.csv", "text/csv")

    elif menu_fin == "Automação & Conciliação":
        t1, t2, t3 = st.tabs(["🧾 Recibos", "📥 Importar", "⚖️ Conciliação"])
        with t1:
            if 'pdf_buffer' not in st.session_state: st.session_state.pdf_buffer = None
            with st.form("rec"):
                tp = st.radio("Tipo", ["Recebimento", "Pagamento"], horizontal=True); nm = st.text_input("Nome"); vl = st.number_input("Valor"); rf = st.text_area("Ref"); dt = st.date_input("Data")
                if st.form_submit_button("Gerar"):
                    row = {"Data": pd.to_datetime(dt), "Tipo": "Entrada" if tp=="Recebimento" else "Saída", "Valor": vl, "Subcategoria": nm, "Descrição": rf, "Categoria": "Outros"}
                    st.session_state.db = pd.concat([st.session_state.db, normalize_columns_fin(pd.DataFrame([row]))], ignore_index=True); save_data_fin(st.session_state.db)
                    st.session_state.pdf_buffer = generate_receipt_pro(tp, nm, vl, rf, dt); st.success("Gerado!")
            if st.session_state.pdf_buffer: st.download_button("⬇️ Baixar PDF", st.session_state.pdf_buffer, "recibo.pdf", "application/pdf")
        with t2:
            up = st.file_uploader("Arquivo Financeiro", type=['xlsx', 'csv', 'pdf'])
            if up:
                new = read_any_file(up); norm = normalize_columns_fin(new)
                dup = norm['Subcategoria'].value_counts()
                norm.insert(0, "Atenção", norm['Subcategoria'].apply(lambda x: f"⚠️ {dup.get(x,0)}x" if dup.get(x,0)>1 else "OK"))
                st.dataframe(norm); 
                if st.button("Confirmar Importação"): st.session_state.db = pd.concat([st.session_state.db, norm.drop(columns=['Atenção'])], ignore_index=True); save_data_fin(st.session_state.db); st.success("Importado!"); st.rerun()
        with t3:
            up_b = st.file_uploader("Extrato Banco", type=['xlsx', 'csv', 'pdf'], key='banc')
            if up_b:
                db_b = normalize_columns_fin(read_any_file(up_b))
                if not db_b.empty:
                    d_sys = df[(df['Data']>=db_b['Data'].min()) & (df['Data']<=db_b['Data'].max())]
                    s_ent, s_sai = d_sys[d_sys['Tipo']=='Entrada']['Valor'].sum(), d_sys[d_sys['Tipo']=='Saída']['Valor'].sum()
                    b_ent, b_sai = db_b[db_b['Tipo']=='Entrada']['Valor'].sum(), db_b[db_b['Tipo']=='Saída']['Valor'].sum()
                    c1, c2, c3 = st.columns(3)
                    c1.metric("Sistema (Ent)", f"R$ {s_ent:,.2f}"); c2.metric("Banco (Ent)", f"R$ {b_ent:,.2f}"); c3.metric("Diferença", f"R$ {s_ent-b_ent:,.2f}", delta_color="off")

# ==============================================================================
# MÓDULO COMERCIAL (Código Completo)
# ==============================================================================
elif st.session_state.current_system == "Comercial":
    
    DATA_FILE_CRM = "comercial_blue.csv"
    def load_crm():
        if os.path.exists(DATA_FILE_CRM): return pd.read_csv(DATA_FILE_CRM)
        return pd.DataFrame({"Nome": ["Laita Biano"], "Status": ["Em Negociação"], "Valor Total": [50000.0], "Pago": [0.0], "Hospital": ["Copa Star"], "Obs": ["Exemplo"]})
    def save_crm(df): df.to_csv(DATA_FILE_CRM, index=False)
    
    if 'crm' not in st.session_state: st.session_state.crm = load_crm()
    df_crm = st.session_state.crm.copy()
    
    with st.sidebar:
        st.markdown("<div class='blue-logo'>blue<span class='blue-dot'>.</span></div><div class='blue-sub'>Commercial</div>", unsafe_allow_html=True); st.markdown("---")
        st.metric("Pipeline (A Receber)", f"R$ {(df_crm['Valor Total'].sum() - df_crm['Pago'].sum()):,.2f}"); st.markdown("---")
        menu_com = st.radio("MENU COMERCIAL", ["Pipeline", "Simulador Orçamento", "Sales Coach (IA)", "Integrações"])
        st.markdown("---")
        st.markdown("""<a href="https://treeapp.com/" target="_blank" style="text-decoration: none;"><div style="background: #1e293b; color: #fff; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #00f2ff;">📅 Agendar (TimeTree)</div></a>""", unsafe_allow_html=True)

    if menu_com == "Pipeline":
        st.title("Gestão de Pacientes")
        edited_crm = st.data_editor(df_crm, num_rows="dynamic", use_container_width=True, column_config={"Valor Total": st.column_config.NumberColumn(format="R$ %.2f"), "Pago": st.column_config.NumberColumn(format="R$ %.2f"), "Status": st.column_config.SelectboxColumn(options=["1ª Consulta", "Negociação", "Fechado", "Cirurgia", "Lost"])})
        if not edited_crm.equals(df_crm):
            if st.button("💾 ATUALIZAR CRM"): st.session_state.crm = edited_crm; save_crm(edited_crm); st.success("Atualizado!"); st.rerun()

    elif menu_com == "Simulador Orçamento":
        st.title("Simulador LipeDefinition®")
        c1, c2 = st.columns(2)
        with c1:
            st.subheader("1. Equipe & Hospital")
            v_eq = st.number_input("Equipe (Anest/Aux/Instr)", value=8150.0)
            hosp = st.selectbox("Hospital", ["Perinatal", "Barra D'or", "Copa Star"]); v_hosp = st.number_input("Valor Hospital", value=5988.0 if hosp=="Perinatal" else (14000.0 if hosp=="Barra D'or" else 23108.0))
        with c2:
            st.subheader("2. Tecnologias")
            v_tec = st.number_input("Tecnologias (Argo/Morpheus)", value=35400.0); v_pos = st.number_input("Pós (Fisio/Cinta)", value=12050.0)
        
        total = v_eq + v_hosp + v_tec + v_pos
        st.markdown("---"); st.markdown(f"<h2 style='text-align:center'>Total Estimado: R$ {total:,.2f}</h2>", unsafe_allow_html=True)
        if st.button("Salvar no CRM"):
            st.session_state.crm = pd.concat([st.session_state.crm, pd.DataFrame([{"Nome": "Novo (Simulação)", "Status": "Negociação", "Valor Total": total, "Pago": 0.0, "Hospital": hosp}])], ignore_index=True)
            save_crm(st.session_state.crm); st.success("Salvo!")

    elif menu_com == "Sales Coach (IA)":
        st.title("🤖 Sales Coach")
        obj = st.selectbox("Objeção", ["Valor Alto", "Falar com Marido", "Medo"]); 
        if st.button("Gerar Script"):
            if "Valor" in obj: st.info("Sugestão: 'Entendo. Mas dividindo pelo tempo que você sofre com Lipedema, o custo diário é mínimo perto da liberdade.'")
            else: st.info("Sugestão: 'O que te impede de tomar essa decisão hoje?'")

    elif menu_com == "Integrações":
        st.title("Conectividade"); st.success("TimeTree: Conectado"); st.warning("Sheets: Aguardando API")
