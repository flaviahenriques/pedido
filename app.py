import streamlit as st
from datetime import datetime
import openai
from supabase import create_client
import base64

# #########################################################
# 1) CONFIGURAÇÕES
# #########################################################
st.set_page_config(page_title="PROFIX - Gestão", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# =========================================================
# 2) LAYOUT DA PROPOSTA (FOTOS ANTES DO PREÇO)
# =========================================================
def montar_layout_proposta(r_social, cnpj_val, empreend, local, cuidados, escopo, lista_itens, lista_fotos, valor_total):
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    partes = escopo.split("|||")
    s1, s2, s3, s4 = (partes + ["", "", "", ""])[:4]

    fotos_html = ""
    if lista_fotos:
        fotos_html += "<b style='color:#002d5b; font-size:16px;'>4. RELATÓRIO FOTOGRÁFICO</b><br><br>"
        fotos_html += '<div style="display: flex; flex-wrap: wrap; gap: 4%;">'
        for f in lista_fotos:
            url = f.get('url_foto') or f.get('file')
            if hasattr(url, "read"): continue
            fotos_html += f"""
            <div style="width: 48%; margin-bottom:20px; page-break-inside: avoid;">
                <img src="{url}" style="width:100%; height:200px; object-fit: cover; border-radius:5px; border:1px solid #ddd;">
                <p style="text-align:center; font-size:11px; font-weight:bold; color:#002d5b;">{f.get('nome','Item')}</p>
            </div>"""
        fotos_html += '</div>'

    itens_html = "".join([f"<div style='display:flex; justify-content:space-between; border-bottom:1px solid #eee; padding:8px 0;'><span>{i['serv']} (x{i['qtd']})</span><b>R$ {i['total']:,.2f}</b></div>" for i in lista_itens])

    return f"""
    <html>
    <head>
        <style>
            .secao-titulo {{ color:#002d5b; font-size:16px; text-transform: uppercase; margin-top: 20px; display:block; }}
            .texto {{ text-align: justify; font-size: 13px; white-space: pre-wrap; margin-top:5px; }}
        </style>
    </head>
    <body style="font-family: Arial; padding: 40px; color: #333;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <img src="https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix" width="200">
            <div style="text-align:right; font-size:11px;"><b>PROFIX GESTÃO DE FACILITIES</b><br>CNPJ: 52.620.102/0001-03</div>
        </div>
        <h2 style="background:#002d5b; color:white; text-align:center; padding:12px; margin-top:30px;">PROPOSTA TÉCNICA COMERCIAL</h2>
        <p style="text-align:right; font-size:13px;">Rio de Janeiro, {data_hoje}</p>
        
        <div style="border:1px solid #ddd; padding:15px; margin-bottom:20px; font-size:13px; display:flex;">
            <div style="flex:1;"><b>CLIENTE:</b> {r_social}<br><b>CNPJ:</b> {cnpj_val}</div>
            <div style="flex:1; border-left: 1px solid #ddd; padding-left:15px;"><b>EMPREENDIMENTO:</b> {empreend}<br><b>A/C:</b> {cuidados}</div>
        </div>

        <b class="secao-titulo">1. METODOLOGIA E ESCOPO</b><div class="texto">{s1}</div>
        <b class="secao-titulo">2. MATERIAIS INCLUSOS</b><div class="texto">{s2}</div>
        <b class="secao-titulo">3. ATENDIMENTO E SUPORTE</b><div class="texto">{s3}</div>
        
        {fotos_html}

        <b class="secao-titulo">5. DETALHAMENTO DE VALORES</b>
        <div style="margin-top:10px;">{itens_html}</div>
        
        <div style="margin-top:30px; display:flex; justify-content:space-between; align-items:flex-start;">
            <div style="font-size:12px; color:#555;"><b>6. CONDIÇÕES COMERCIAIS</b><br>{s4}</div>
            <div style="background:#f1f4f9; padding:20px; border-left:8px solid #002d5b; text-align:right;">
                <small>VALOR TOTAL</small><br><b style="font-size:24px; color:#002d5b;">R$ {valor_total:,.2f}</b>
            </div>
        </div>
    </body>
    </html>"""

# =========================================================
# 3) LÓGICA DO APLICATIVO
# =========================================================
with st.sidebar:
    st.title("🛡️ Painel PROFIX")
    menu = st.radio("Navegação", ["Novo Orçamento", "Gerenciar Pedidos"])

# --- ABA: NOVO ORÇAMENTO ---
if menu == "Novo Orçamento":
    st.header("📑 Nova Proposta")

    # BUSCA CLIENTES QUE JÁ EXISTEM NO BANCO PARA FACILITAR
    try:
        dados_antigos = supabase.table("orcamentos").select("cliente_razao_social, cliente_cnpj, empreendimento, localizacao, aos_cuidados").execute().data
        # Remove duplicados
        clientes_unicos = {d['cliente_razao_social']: d for d in dados_antigos if d['cliente_razao_social']}
    except:
        clientes_unicos = {}

    with st.expander("1. Dados do Cliente", expanded=True):
        sel_c = st.selectbox("Usar dados de um cliente existente?", ["-- Digitar Novo --"] + list(clientes_unicos.keys()))
        
        # Lógica de preenchimento automático
        def_rz, def_cnpj, def_emp, def_loc, def_ac = "", "", "", "", ""
        if sel_c != "-- Digitar Novo --":
            c = clientes_unicos[sel_c]
            def_rz, def_cnpj, def_emp, def_loc, def_ac = c['cliente_razao_social'], c['cliente_cnpj'], c['empreendimento'], c['localizacao'], c['aos_cuidados']

        c1, c2 = st.columns(2)
        razao = c1.text_input("Razão Social", value=def_rz)
        cnpj = c2.text_input("CNPJ", value=def_cnpj)
        emp = c1.text_input("Empreendimento", value=def_emp)
        loc = c2.text_input("Localização", value=def_loc)
        ac = c1.text_input("Aos Cuidados", value=def_ac)

    with st.expander("2. Configuração do Escopo", expanded=True):
        t1 = st.text_area("1. Metodologia e Escopo", value="Manutenção de Elétrica, Hidráulica e Pequenos Reparos...", height=100)
        t2 = st.text_area("2. Materiais Inclusos", value="Todos os insumos básicos inclusos.", height=70)
        t3 = st.text_area("3. Atendimento", value="Visitas ilimitadas. SLA 24h.", height=70)
        t4 = st.text_area("4. Condições Comerciais", value="Faturamento 30 dias.", height=70)
        escopo_unificado = f"{t1}|||{t2}|||{t3}|||{t4}"

    with st.expander("3. Fotos e Itens"):
        up_f = st.file_uploader("Fotos", accept_multiple_files=True)
        if up_f and st.button("🪄 Analisar Fotos"):
            for f in up_f:
                st.session_state.fotos.append({"file": f, "nome": "Item Verificado", "unidades": "1"})
            st.rerun()
        
        for idx, f in enumerate(st.session_state.fotos):
            cc1, cc2 = st.columns([1, 4])
            cc1.image(f['file'], width=60)
            f['nome'] = cc2.text_input(f"Legenda {idx+1}", f['nome'], key=f"f_{idx}")

        st.divider()
        ci1, ci2, ci3 = st.columns([3, 1, 1])
        it_n = ci1.text_input("Serviço")
        it_q = ci2.number_input("Qtd", min_value=1)
        it_v = ci3.number_input("Valor Unit.", min_value=0.0)
        if st.button("➕ Adicionar"):
            st.session_state.itens.append({"serv": it_n, "qtd": it_q, "total": it_q * it_v})
            st.rerun()

    total = sum(i['total'] for i in st.session_state.itens)
    
    if st.button("💾 SALVAR E GERAR LINK", type="primary", use_container_width=True):
        payload = {
            "cliente_razao_social": razao, "cliente_cnpj": cnpj, "empreendimento": emp,
            "localizacao": loc, "aos_cuidados": ac, "valor_total": total,
            "metodologia_escopo": escopo_unificado, "status": "Pendente"
        }
        res = supabase.table("orcamentos").insert(payload).execute()
        st.success(f"Salvo! Link: https://profix-gestao.streamlit.app/?id={res.data[0]['id']}")

    st.divider()
    st.subheader("👁️ Pré-visualização")
    html = montar_layout_proposta(razao, cnpj, emp, loc, ac, escopo_unificado, st.session_state.itens, st.session_state.fotos, total)
    st.components.v1.html(html, height=800, scrolling=True)

# --- ABA: GERENCIAR PEDIDOS ---
elif menu == "Gerenciar Pedidos":
    st.header("📋 Histórico por Cliente")
    
    # Filtro dinâmico baseado no que já foi salvo
    clientes_salvos = supabase.table("orcamentos").select("cliente_razao_social").execute().data
    lista_f = sorted(list(set([c['cliente_razao_social'] for c in clientes_salvos if c['cliente_razao_social']])))
    
    filtro = st.selectbox("Filtrar por Cliente", ["Todos"] + lista_f)
    
    query = supabase.table("orcamentos").select("*").order("id", desc=True)
    if filtro != "Todos":
        query = query.eq("cliente_razao_social", filtro)
    
    for p in query.execute().data:
        st.info(f"**{p['cliente_razao_social']}** | {p['empreendimento']} | R$ {float(p['valor_total']):,.2f}")
