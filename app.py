import streamlit as st
from datetime import datetime
import openai
from supabase import create_client
import base64

# #########################################################
# 1) CONFIGURAÇÕES E CONEXÃO
# #########################################################
st.set_page_config(page_title="PROFIX - Gestão de Orçamentos", layout="wide")

# Credenciais (Devem estar no st.secrets do Streamlit Cloud)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Inicialização de estados de sessão para evitar perda de dados
if "itens" not in st.session_state: st.session_state.itens = []
if "fotos" not in st.session_state: st.session_state.fotos = []
if "edit_id" not in st.session_state: st.session_state.edit_id = None

# =========================================================
# 2) DESIGN DA PROPOSTA (HTML COM BOTÃO DE IMPRESSÃO)
# =========================================================
def montar_layout_proposta(r_social, cnpj_val, empreend, local, cuidados, escopo, lista_itens, lista_fotos, valor_total):
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    
    # Divide os 4 campos de escopo usando o separador |||
    partes = escopo.split("|||")
    s1, s2, s3, s4 = (partes + ["", "", "", ""])[:4]

    # Galeria de Fotos (Item 4 - ANTES do Investimento)
    fotos_html = ""
    if lista_fotos:
        fotos_html += "<b style='color:#002d5b; font-size:16px; text-transform: uppercase;'>4. RELATÓRIO FOTOGRÁFICO</b><br><br>"
        fotos_html += '<div style="display: flex; flex-wrap: wrap; gap: 4%;">'
        for f in lista_fotos:
            url = f.get('url_foto') or f.get('file')
            # Placeholder para fotos que ainda não foram enviadas ao storage
            if hasattr(url, "read"): url = "https://via.placeholder.com/400x300?text=Foto+Carregada"
            
            fotos_html += f"""
            <div style="width: 48%; margin-bottom:20px; page-break-inside: avoid;">
                <div style="width:100%; height:220px; overflow:hidden; border:1px solid #ddd; border-radius:5px;">
                    <img src="{url}" style="width:100%; height:100%; object-fit: cover;">
                </div>
                <p style="text-align:center; font-size:11px; font-weight:bold; color:#002d5b; margin-top:5px;">{f.get('nome','Item')}</p>
            </div>"""
        fotos_html += '</div>'

    # Tabela de Valores (Item 5)
    itens_html = ""
    for idx, i in enumerate(lista_itens, start=1):
        itens_html += f"""
        <div style="display:flex; justify-content:space-between; border-bottom:1px solid #eee; padding:8px 0; font-size:14px;">
            <span>{idx}. <b>{i['serv'].upper()}</b> (Qtd: {i['qtd']})</span>
            <b>R$ {float(i['total']):,.2f}</b>
        </div>"""

    return f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; color: #333; padding: 20px; }}
            .secao-titulo {{ color:#002d5b; font-size:15px; text-transform: uppercase; margin-top: 25px; display:block; border-bottom: 1px solid #eee; padding-bottom:5px; }}
            .texto {{ text-align: justify; font-size: 13px; white-space: pre-wrap; margin-top:8px; line-height:1.5; }}
            .btn-imprimir {{ 
                background-color: #002d5b; color: white; padding: 12px 24px; 
                border: none; border-radius: 5px; cursor: pointer; font-weight: bold;
                font-size: 16px; margin-bottom: 30px; display: flex; align-items: center; gap: 10px;
            }}
            .btn-imprimir:hover {{ background-color: #004080; }}
            @media print {{ 
                .btn-imprimir {{ display: none !important; }} 
                body {{ padding: 0; }}
                @page {{ margin: 1cm; }}
            }}
        </style>
    </head>
    <body>
        <button class="btn-imprimir" onclick="window.print()">
            <span>🖨️</span> IMPRIMIR OU SALVAR PDF
        </button>

        <div style="display:flex; justify-content:space-between; align-items:center;">
            <img src="https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix" width="220">
            <div style="text-align:right; font-size:10px;"><b>PROFIX GESTÃO DE FACILITIES</b><br>CNPJ: 52.620.102/0001-03<br>Rio de Janeiro - RJ</div>
        </div>
        
        <h2 style="background:#002d5b; color:white; text-align:center; padding:12px; margin-top:30px; text-transform: uppercase; letter-spacing: 1px;">Proposta Técnica Comercial</h2>
        <p style="text-align:right; font-size:13px;">Data de emissão: {data_hoje}</p>
        
        <div style="border:1px solid #ddd; padding:15px; margin-bottom:20px; font-size:13px; display:flex; background: #fcfcfc;">
            <div style="flex:1;"><b>CLIENTE:</b> {r_social}<br><b>CNPJ:</b> {cnpj_val}</div>
            <div style="flex:1; border-left: 1px solid #ddd; padding-left:15px;"><b>EMPREENDIMENTO:</b> {empreend}<br><b>A/C:</b> {cuidados}</div>
        </div>

        <b class="secao-titulo">1. Metodologia e Escopo Técnico</b><div class="texto">{s1}</div>
        <b class="secao-titulo">2. Materiais e Insumos Inclusos</b><div class="texto">{s2}</div>
        <b class="secao-titulo">3. Modelo de Atendimento e Suporte</b><div class="texto">{s3}</div>
        
        <div style="margin-top: 30px;">{fotos_html}</div>

        <div style="page-break-before: auto;">
            <b class="secao-titulo">5. Detalhamento do Investimento</b>
            <div style="margin-top:10px;">{itens_html}</div>
            
            <div style="margin-top:40px; display:flex; justify-content:space-between; align-items:flex-start;">
                <div style="font-size:12px; color:#555; flex:1;"><b>6. Condições Comerciais</b><br>{s4}</div>
                <div style="background:#f1f4f9; padding:25px; border-left:8px solid #002d5b; text-align:right; min-width:280px;">
                    <small style="text-transform: uppercase; color: #666;">Valor Total do Projeto</small><br>
                    <b style="font-size:28px; color:#002d5b;">R$ {valor_total:,.2f}</b>
                </div>
            </div>
        </div>
    </body>
    </html>"""

# =========================================================
# 3) INTERFACE STREAMLIT
# =========================================================
with st.sidebar:
    st.image("https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix", width=180)
    st.title("🛡️ Painel Administrativo")
    menu = st.radio("Selecione uma opção:", ["Novo Orçamento", "Gerenciar Pedidos"])
    if st.button("➕ Iniciar Novo"):
        st.session_state.itens = []; st.session_state.fotos = []; st.session_state.edit_id = None
        st.rerun()

# --- ABA: GERENCIAR PEDIDOS ---
if menu == "Gerenciar Pedidos":
    st.header("📋 Histórico de Orçamentos")
    pedidos = supabase.table("orcamentos").select("*").order("id", desc=True).execute().data
    lista_cli = sorted(list(set([p['cliente_razao_social'] for p in pedidos if p['cliente_razao_social']])))
    
    filtro = st.selectbox("Filtrar por Cliente", ["Todos"] + lista_cli)
    
    for p in pedidos:
        if filtro != "Todos" and p['cliente_razao_social'] != filtro: continue
        with st.expander(f"{p['cliente_razao_social']} - {p['empreendimento']} (R$ {float(p['valor_total']):,.2f})"):
            c1, c2 = st.columns([3, 1])
            c1.write(f"**ID:** {p['id']} | **Status:** {p['status']}")
            if c2.button("📝 Editar Proposta", key=f"btn_ed_{p['id']}"):
                st.session_state.edit_id = p['id']
                it_db = supabase.table("itens_orcamento").select("*").eq("orcamento_id", p['id']).execute().data
                ft_db = supabase.table("fotos_relatorio").select("*").eq("orcamento_id", p['id']).execute().data
                st.session_state.itens = [{"serv": i['servico'], "qtd": i['quantidade'], "total": i['valor_total']} for i in it_db]
                st.session_state.fotos = [{"url_foto": f['url_foto'], "nome": f['nome_item']} for f in ft_db]
                st.success("Dados carregados! Volte para 'Novo Orçamento'.")

# --- ABA: NOVO ORÇAMENTO ---
else:
    st.header("📑 " + ("Editando Proposta" if st.session_state.edit_id else "Nova Proposta Comercial"))
    
    # Memória de Clientes
    dados_memo = supabase.table("orcamentos").select("cliente_razao_social, cliente_cnpj, empreendimento, localizacao, aos_cuidados").execute().data
    clientes_memo = {d['cliente_razao_social']: d for d in dados_memo if d['cliente_razao_social']}

    with st.expander("1. Dados do Cliente", expanded=True):
        sel_c = st.selectbox("Preencher com dados de cliente existente?", ["-- Digitar Novo --"] + list(clientes_memo.keys()))
        
        rz, cnpj, emp, loc, ac, esc = "", "", "", "", "", "||||||"
        
        if st.session_state.edit_id:
            curr = supabase.table("orcamentos").select("*").eq("id", st.session_state.edit_id).execute().data[0]
            rz, cnpj, emp, loc, ac, esc = curr['cliente_razao_social'], curr['cliente_cnpj'], curr['empreendimento'], curr['localizacao'], curr['aos_cuidados'], curr['metodologia_escopo']
        elif sel_c != "-- Digitar Novo --":
            c = clientes_memo[sel_c]
            rz, cnpj, emp, loc, ac = c['cliente_razao_social'], c['cliente_cnpj'], c['empreendimento'], c['localizacao'], c['aos_cuidados']

        c1, c2 = st.columns(2)
        razao = c1.text_input("Razão Social", value=rz)
        cnpj_val = c2.text_input("CNPJ", value=cnpj)
        emp_val = c1.text_input("Empreendimento", value=emp)
        loc_val = c2.text_input("Localização", value=loc)
        ac_val = c1.text_input("Aos Cuidados", value=ac)

    with st.expander("2. Escopo da Proposta", expanded=True):
        p_esc = esc.split("|||") if 'esc' in locals() else ["","","",""]
        t1 = st.text_area("1. Metodologia e Escopo", value=p_esc[0] if p_esc[0] else "Manutenção Predial...", height=100)
        t2 = st.text_area("2. Materiais Inclusos", value=p_esc[1] if len(p_esc)>1 else "Insumos básicos de civil e elétrica.", height=70)
        t3 = st.text_area("3. Atendimento", value=p_esc[2] if len(p_esc)>2 else "SLA de 24 horas úteis.", height=70)
        t4 = st.text_area("4. Condições Comerciais", value=p_esc[3] if len(p_esc)>3 else "Pagamento em 30 dias.", height=70)
        escopo_final = f"{t1}|||{t2}|||{t3}|||{t4}"

    with st.expander("3. Relatório Fotográfico e Valores", expanded=True):
        up_f = st.file_uploader("Subir fotos do levantamento", accept_multiple_files=True)
        if up_f and st.button("🪄 Processar Nomes de Arquivo"):
            for f in up_f:
                # O nome do arquivo vira legenda automaticamente
                nome_limpo = f.name.rsplit('.', 1)[0].replace('_', ' ').title()
                st.session_state.fotos.append({"file": f, "nome": nome_limpo})
            st.rerun()
        
        for idx, f in enumerate(st.session_state.fotos):
            cc1, cc2, cc3 = st.columns([1, 4, 0.5])
            cc1.image(f.get('url_foto') or f.get('file'), width=60)
            f['nome'] = cc2.text_input(f"Legenda Foto {idx+1}", f['nome'], key=f"f_txt_{idx}")
            if cc3.button("🗑️", key=f"del_f_{idx}"):
                st.session_state.fotos.pop(idx); st.rerun()

        st.divider()
        ci1, ci2, ci3 = st.columns([3, 1, 1])
        it_n = ci1.text_input("Nome do Serviço")
        it_q = ci2.number_input("Qtd", min_value=1, value=1)
        it_v = ci3.number_input("Preço Unitário", min_value=0.0)
        if st.button("➕ Adicionar Serviço"):
            st.session_state.itens.append({"serv": it_n, "qtd": it_q, "total": it_q * it_v})
            st.rerun()
        
        for i_idx, it in enumerate(st.session_state.itens):
            c_it1, c_it2, c_it3 = st.columns([4, 1, 0.5])
            c_it1.write(f"**{it['serv']}** (x{it['qtd']})")
            c_it2.write(f"R$ {it['total']:,.2f}")
            if c_it3.button("❌", key=f"del_it_{i_idx}"):
                st.session_state.itens.pop(i_idx); st.rerun()

    total_proposta = sum(i['total'] for i in st.session_state.itens)
    
    if st.button("💾 SALVAR PROPOSTA", type="primary", use_container_width=True):
        payload = {
            "cliente_razao_social": razao, "cliente_cnpj": cnpj_val, "empreendimento": emp_val,
            "localizacao": loc_val, "aos_cuidados": ac_val, "valor_total": total_proposta,
            "metodologia_escopo": escopo_final, "status": "Enviado"
        }
        
        if st.session_state.edit_id:
            oid = st.session_state.edit_id
            supabase.table("orcamentos").update(payload).eq("id", oid).execute()
            supabase.table("itens_orcamento").delete().eq("orcamento_id", oid).execute()
            supabase.table("fotos_relatorio").delete().eq("orcamento_id", oid).execute()
        else:
            res = supabase.table("orcamentos").insert(payload).execute()
            oid = res.data[0]['id']

        for i in st.session_state.itens:
            supabase.table("itens_orcamento").insert({"orcamento_id": oid, "servico": i['serv'], "quantidade": i['qtd'], "valor_total": i['total']}).execute()
        
        for f in st.session_state.fotos:
            url_f = f.get('url_foto', 'https://placeholder.com')
            supabase.table("fotos_relatorio").insert({"orcamento_id": oid, "nome_item": f['nome'], "url_foto": url_f}).execute()
        
        st.success(f"✅ Proposta {oid} salva com sucesso!")

    st.divider()
    st.subheader("👁️ Pré-visualização e Impressão")
    # Gerar HTML final
    html_gerado = montar_layout_proposta(razao, cnpj_val, emp_val, loc_val, ac_val, escopo_final, st.session_state.itens, st.session_state.fotos, total_proposta)
    # Exibir o HTML em um frame grande
    st.components.v1.html(html_gerado, height=1200, scrolling=True)
