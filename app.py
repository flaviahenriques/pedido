import streamlit as st
from datetime import datetime
import openai
from supabase import create_client
import base64

# #########################################################
# 1) CONFIGURAÇÕES E CONEXÃO
# #########################################################
st.set_page_config(page_title="PROFIX - Gestão Integrada", layout="wide")

# Credenciais (Devem estar no st.secrets do Streamlit Cloud)
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# Inicialização de estados de sessão
if "itens" not in st.session_state: st.session_state.itens = []
if "fotos" not in st.session_state: st.session_state.fotos = []
if "edit_id" not in st.session_state: st.session_state.edit_id = None

# =========================================================
# 2) DESIGN DA PROPOSTA (HTML/CSS)
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
                <div style="width:100%; height:200px; overflow:hidden; border:1px solid #ddd; border-radius:5px;">
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
            body {{ font-family: Arial, sans-serif; color: #333; }}
            .secao-titulo {{ color:#002d5b; font-size:15px; text-transform: uppercase; margin-top: 25px; display:block; border-bottom: 1px solid #eee; padding-bottom:5px; }}
            .texto {{ text-align: justify; font-size: 13px; white-space: pre-wrap; margin-top:8px; line-height:1.5; }}
        </style>
    </head>
    <body style="padding: 30px;">
        <div style="display:flex; justify-content:space-between; align-items:center;">
            <img src="https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix" width="200">
            <div style="text-align:right; font-size:10px;"><b>PROFIX GESTÃO DE FACILITIES</b><br>CNPJ: 52.620.102/0001-03</div>
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

        <b class="secao-titulo">5. DETALHAMENTO DE INVESTIMENTO</b>
        <div style="margin-top:10px;">{itens_html}</div>
        
        <div style="margin-top:30px; display:flex; justify-content:space-between; align-items:flex-start;">
            <div style="font-size:12px; color:#555; flex:1;"><b>6. CONDIÇÕES COMERCIAIS</b><br>{s4}</div>
            <div style="background:#f1f4f9; padding:20px; border-left:8px solid #002d5b; text-align:right; min-width:250px;">
                <small>VALOR TOTAL DA PROPOSTA</small><br><b style="font-size:26px; color:#002d5b;">R$ {valor_total:,.2f}</b>
            </div>
        </div>
    </body>
    </html>"""

# =========================================================
# 3) INTERFACE PRINCIPAL
# =========================================================
with st.sidebar:
    st.image("https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix", width=150)
    st.title("Sistema PROFIX")
    menu = st.radio("Navegação", ["Novo Orçamento", "Gerenciar Pedidos"])
    if st.button("🧹 Resetar Formulário"):
        st.session_state.itens = []; st.session_state.fotos = []; st.session_state.edit_id = None
        st.rerun()

# --- ABA: GERENCIAR PEDIDOS ---
if menu == "Gerenciar Pedidos":
    st.header("📋 Histórico de Orçamentos")
    
    # Carrega orçamentos do banco
    pedidos = supabase.table("orcamentos").select("*").order("id", desc=True).execute().data
    clientes_lista = sorted(list(set([p['cliente_razao_social'] for p in pedidos if p['cliente_razao_social']])))
    
    filtro_cli = st.selectbox("Filtrar por Cliente", ["Todos"] + clientes_lista)
    
    for p in pedidos:
        if filtro_cli != "Todos" and p['cliente_razao_social'] != filtro_cli: continue
        
        with st.expander(f"{p['cliente_razao_social']} - {p['empreendimento']} (R$ {float(p['valor_total']):,.2f})"):
            col_a, col_b = st.columns([3, 1])
            col_a.write(f"**Data:** {p['created_at'][:10]} | **Status:** {p['status']}")
            
            if col_b.button("📝 Editar", key=f"edit_{p['id']}"):
                st.session_state.edit_id = p['id']
                # Busca itens e fotos associados para carregar no formulário
                it_db = supabase.table("itens_orcamento").select("*").eq("orcamento_id", p['id']).execute().data
                ft_db = supabase.table("fotos_relatorio").select("*").eq("orcamento_id", p['id']).execute().data
                
                st.session_state.itens = [{"serv": i['servico'], "qtd": i['quantidade'], "total": i['valor_total']} for i in it_db]
                st.session_state.fotos = [{"url_foto": f['url_foto'], "nome": f['nome_item']} for f in ft_db]
                st.success("Dados carregados! Vá para 'Novo Orçamento'.")

# --- ABA: NOVO ORÇAMENTO ---
else:
    st.header("📑 " + ("Editando Proposta" if st.session_state.edit_id else "Nova Proposta"))
    
    # Memória de Clientes (Lógica inteligente sem tabela extra)
    dados_memo = supabase.table("orcamentos").select("cliente_razao_social, cliente_cnpj, empreendimento, localizacao, aos_cuidados").execute().data
    clientes_memo = {d['cliente_razao_social']: d for d in dados_memo if d['cliente_razao_social']}

    with st.expander("1. Dados do Cliente", expanded=True):
        sel_memo = st.selectbox("Buscar em clientes atendidos", ["-- Novo Cliente --"] + list(clientes_memo.keys()))
        
        d_rz, d_cnpj, d_emp, d_loc, d_ac, d_esc = "", "", "", "", "", "||||||"
        
        # Prioridade 1: Edição | Prioridade 2: Memória
        if st.session_state.edit_id:
            curr = supabase.table("orcamentos").select("*").eq("id", st.session_state.edit_id).execute().data[0]
            d_rz, d_cnpj, d_emp, d_loc, d_ac, d_esc = curr['cliente_razao_social'], curr['cliente_cnpj'], curr['empreendimento'], curr['localizacao'], curr['aos_cuidados'], curr['metodologia_escopo']
        elif sel_memo != "-- Novo Cliente --":
            m = clientes_memo[sel_memo]
            d_rz, d_cnpj, d_emp, d_loc, d_ac = m['cliente_razao_social'], m['cliente_cnpj'], m['empreendimento'], m['localizacao'], m['aos_cuidados']

        c1, c2 = st.columns(2)
        razao = c1.text_input("Razão Social", value=d_rz)
        cnpj = c2.text_input("CNPJ", value=d_cnpj)
        emp = c1.text_input("Empreendimento", value=d_emp)
        loc = c2.text_input("Localização", value=d_loc)
        ac = c1.text_input("Aos Cuidados", value=d_ac)

    with st.expander("2. Configuração do Escopo", expanded=True):
        p_esc = d_esc.split("|||") if 'd_esc' in locals() else ["","","",""]
        txt1 = st.text_area("1. Metodologia e Escopo Técnico", value=p_esc[0] if p_esc[0] else "Ex: Manutenção Elétrica e Hidráulica...", height=100)
        txt2 = st.text_area("2. Materiais Inclusos", value=p_esc[1] if len(p_esc)>1 else "Parafusos, buchas, silicone e veda-rosca.", height=70)
        txt3 = st.text_area("3. Modelo de Atendimento", value=p_esc[2] if len(p_esc)>2 else "Visitas ilimitadas. SLA 24h úteis.", height=70)
        txt4 = st.text_area("4. Condições Comerciais", value=p_esc[3] if len(p_esc)>3 else "Pagamento 30 dias após emissão da NF.", height=70)
        escopo_unificado = f"{txt1}|||{txt2}|||{txt3}|||{txt4}"

    with st.expander("3. Fotos e Valores", expanded=True):
        up_f = st.file_uploader("Subir Fotos", accept_multiple_files=True)
        if up_f and st.button("🪄 Processar Fotos (Nome do Arquivo)"):
            for f in up_f:
                # Lógica solicitada: Nome do arquivo vira a legenda (limpando extensão)
                nome_limpo = f.name.rsplit('.', 1)[0].replace('_', ' ').title()
                st.session_state.fotos.append({"file": f, "nome": nome_limpo})
            st.rerun()
        
        for idx, f in enumerate(st.session_state.fotos):
            cc1, cc2, cc3 = st.columns([1, 4, 0.5])
            cc1.image(f.get('url_foto') or f.get('file'), width=60)
            f['nome'] = cc2.text_input(f"Legenda da Foto {idx+1}", f['nome'], key=f"f_txt_{idx}")
            if cc3.button("🗑️", key=f"del_f_{idx}"):
                st.session_state.fotos.pop(idx); st.rerun()

        st.divider()
        ci1, ci2, ci3 = st.columns([3, 1, 1])
        it_n = ci1.text_input("Serviço / Taxa")
        it_q = ci2.number_input("Qtd", min_value=1, value=1)
        it_v = ci3.number_input("Valor Unitário", min_value=0.0)
        if st.button("➕ Adicionar Item ao Orçamento"):
            st.session_state.itens.append({"serv": it_n, "qtd": it_q, "total": it_q * it_v})
            st.rerun()
        
        for i_idx, it in enumerate(st.session_state.itens):
            c_it1, c_it2, c_it3 = st.columns([4, 1, 0.5])
            c_it1.write(f"**{it['serv']}** (x{it['qtd']})")
            c_it2.write(f"R$ {it['total']:,.2f}")
            if c_it3.button("❌", key=f"del_it_{i_idx}"):
                st.session_state.itens.pop(i_idx); st.rerun()

    total_geral = sum(i['total'] for i in st.session_state.itens)
    
    if st.button("💾 FINALIZAR E SALVAR PROPOSTA", type="primary", use_container_width=True):
        payload = {
            "cliente_razao_social": razao, "cliente_cnpj": cnpj, "empreendimento": emp,
            "localizacao": loc, "aos_cuidados": ac, "valor_total": total_geral,
            "metodologia_escopo": escopo_unificado, "status": "Pendente"
        }
        
        if st.session_state.edit_id:
            oid = st.session_state.edit_id
            supabase.table("orcamentos").update(payload).eq("id", oid).execute()
            supabase.table("itens_orcamento").delete().eq("orcamento_id", oid).execute()
            supabase.table("fotos_relatorio").delete().eq("orcamento_id", oid).execute()
        else:
            res_s = supabase.table("orcamentos").insert(payload).execute()
            oid = res_s.data[0]['id']

        # Salva itens
        for i in st.session_state.itens:
            supabase.table("itens_orcamento").insert({"orcamento_id": oid, "servico": i['serv'], "quantidade": i['qtd'], "valor_total": i['total']}).execute()
        
        #
