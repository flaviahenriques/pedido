import streamlit as st
from datetime import datetime
import openai
from PIL import Image
from supabase import create_client
import base64

# #########################################################
# 1) CONFIGURAÇÕES DE CONEXÃO E PÁGINA
# #########################################################
st.set_page_config(page_title="PROFIX - Gerador de Orçamentos", layout="wide")

# Conexões seguras usando st.secrets
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# =========================================================
# 2) FUNÇÃO PARA MONTAR O HTML DO ORÇAMENTO (DESIGN A4)
# =========================================================
def montar_layout_proposta(orc_id, r_social, cnpj_val, empreend, local, cuidados, escopo, lista_itens, lista_fotos, valor_total):
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    # Formatação do Escopo para ficar organizado com títulos azuis
    # O separador "|||" é usado para dividir as 4 partes no banco de dados
    partes = escopo.split("|||")
    escopo_formatado = ""
    titulos = [
        "1. METODOLOGIA E ESCOPO TÉCNICO",
        "2. MATERIAIS INCLUSOS (SEM CUSTO ADICIONAL)",
        "3. MODELO DE ATENDIMENTO E SUPORTE",
        "4. CONDIÇÕES COMERCIAIS"
    ]
    
    for idx, titulo in enumerate(titulos):
        texto_secao = partes[idx] if idx < len(partes) else ""
        escopo_formatado += f"""
        <div style="margin-bottom: 20px;">
            <b style='color:#002d5b; font-size:16px; text-transform: uppercase;'>{titulo}</b>
            <div class="texto-escopo" style="margin-top:8px;">{texto_secao}</div>
        </div>"""

    itens_html = ""
    for idx, item in enumerate(lista_itens, start=1):
        nome_s = item.get('servico') or item.get('serv', 'Serviço')
        qtd_s = item.get('quantidade') or item.get('qtd', 1)
        v_total = item.get('valor_total') or item.get('total', 0.0)
        itens_html += f"""
        <div style="display:flex; justify-content:space-between; border-bottom:1px solid #eee; padding:8px 0; font-size:14px;">
            <span><b>{idx}. {nome_s.upper()}</b> (Qtd: {qtd_s})</span>
            <b>R$ {v_total:,.2f}</b>
        </div>"""

    fotos_html = ""
    if lista_fotos:
        fotos_html += "<br><b style='color:#002d5b; font-size:16px; text-transform: uppercase;'>5. RELATÓRIO FOTOGRÁFICO</b><br><br>"
        fotos_html += '<div style="display: flex; flex-wrap: wrap; gap: 4%;">'
        for f_idx, foto in enumerate(lista_fotos):
            url = foto.get('url_foto') or foto.get('file')
            legenda = foto.get('nome_item') or foto.get('nome', 'Item')
            qtd_un = foto.get('unidades') or foto.get('qtd', '1')
            if hasattr(url, "read"): continue
            fotos_html += f"""
            <div style="width: 48%; margin-bottom:20px; page-break-inside: avoid; display: flex; flex-direction: column;">
                <div style="width: 100%; height: 220px; overflow: hidden; border-radius:8px; border: 1px solid #ddd;">
                    <img src="{url}" style="width:100%; height:100%; object-fit: cover;">
                </div>
                <p style="text-align:center; font-size:11px; color:#002d5b; font-weight:bold; margin-top:5px;">
                    Foto {f_idx+1}: {legenda} (Qtd: {qtd_un})
                </p>
            </div>"""
        fotos_html += '</div>'

    return f"""
<html>
<head>
<style>
    body {{ background: #f0f2f6; margin: 0; padding: 40px 0; font-family: Arial, sans-serif; }}
    .folha-documento {{
        background-color: white; width: 210mm; min-height: 297mm;
        margin: auto; padding: 50px; box-shadow: 0 0 30px rgba(0,0,0,0.25);
        color: black; position: relative;
    }}
    .titulo-barra {{ background-color: #002d5b; color: white; text-align: center; padding: 12px; font-weight: bold; margin: 20px 0; }}
    .texto-escopo {{ text-align: justify; font-size: 13px; white-space: pre-wrap; word-wrap: break-word; line-height:1.4; }}
    @media print {{ body {{ background: none; padding: 0; }} .folha-documento {{ box-shadow: none; margin: 0; width: 100%; min-height: auto; }} }}
</style>
</head>
<body>
<div class="folha-documento">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <img src="https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix" width="220">
        <div style="text-align:right; font-size:11px; line-height:1.5;">
            <b>PROFIX GESTÃO DE FACILITIES</b><br>CNPJ: 52.620.102/0001-03<br>Centro, Rio de Janeiro - RJ
        </div>
    </div>
    <div class="titulo-barra">PROPOSTA TÉCNICA COMERCIAL</div>
    <div style="text-align:right; font-size:13px; margin-bottom:20px;">Rio de Janeiro, {data_hoje}</div>
    
    <div style="display:flex; border:1px solid #dcdcdc; margin-bottom:30px; font-size:13px;">
        <div style="width:6px; background:#002d5b;"></div>
        <div style="flex:1; padding:15px;">
            <b>RAZÃO SOCIAL:</b><br>{r_social or '—'}<br><br>
            <b>CNPJ:</b><br>{cnpj_val or '—'}<br><br>
            <b>EMPREENDIMENTO:</b><br>{empreend or '—'}
        </div>
        <div style="flex:1; padding:15px; border-left:1px solid #dcdcdc;">
            <b>ENDEREÇO:</b><br>{local or '—'}<br><br>
            <b>A/C:</b><br>{cuidados or '—'}
        </div>
    </div>

    {escopo_formatado}

    <b style='color:#002d5b; font-size:16px; text-transform: uppercase;'>DETALHAMENTO DE VALORES</b>
    {itens_html}

    <div style="display:flex; margin-top:40px; gap:40px; align-items:flex-start;">
        <div style="width:300px; background:#f1f4f9; padding:25px; border-left:8px solid #002d5b; text-align:right; margin-left:auto;">
            <small style="color:#666;">TOTAL DO INVESTIMENTO</small><br><br>
            <span style="font-size:28px; font-weight:bold; color:#002d5b;">R$ {valor_total:,.2f}</span>
        </div>
    </div>
    {fotos_html}
</div>
</body>
</html>
"""

# =========================================================
# 3) LÓGICA DE NAVEGAÇÃO E ESTADOS
# =========================================================
if "itens" not in st.session_state: st.session_state.itens = []
if "fotos" not in st.session_state: st.session_state.fotos = []
if "pagina" not in st.session_state: st.session_state.pagina = "Criar Novo"
if "edit_id" not in st.session_state: st.session_state.edit_id = None

params = st.query_params
if "id" in params:
    doc_id = params["id"]
    try:
        d = supabase.table("orcamentos").select("*").eq("id", doc_id).execute().data[0]
        it_db = supabase.table("itens_orcamento").select("*").eq("orcamento_id", doc_id).execute().data
        ft_db = supabase.table("fotos_relatorio").select("*").eq("orcamento_id", doc_id).execute().data
        html_view = montar_layout_proposta(doc_id, d['cliente_razao_social'], d['cliente_cnpj'], d['empreendimento'], d['localizacao'], d['aos_cuidados'], d['metodologia_escopo'], it_db, ft_db, float(d['valor_total']))
        st.components.v1.html(html_view, height=1200, scrolling=True)
        st.stop()
    except: st.error("Erro ao carregar orçamento.")

with st.sidebar:
    st.title("🛡️ Painel PROFIX")
    opcoes = ["Criar Novo", "Gerenciar Pedidos"]
    st.session_state.pagina = st.radio("Navegação", opcoes, index=opcoes.index(st.session_state.pagina))

if st.session_state.pagina == "Gerenciar Pedidos":
    st.subheader("📋 Histórico")
    pedidos = supabase.table("orcamentos").select("*").order("id", desc=True).execute().data
    for p in pedidos:
        col1, col2, col3 = st.columns([3, 1, 1])
        col1.write(f"**{p['cliente_razao_social']}**")
        col2.write(f"R$ {float(p['valor_total']):,.2f}")
        if col3.button("📝 Editar", key=f"ed_{p['id']}"):
            st.session_state.edit_id = p['id']
            st.session_state.pagina = "Criar Novo"
            st.rerun()

else:
    st.title("🛡️ Novo Orçamento")
    
    with st.expander("1. Dados do Cliente", expanded=True):
        c1, c2 = st.columns(2)
        razao = c1.text_input("Razão Social")
        cnpj = c2.text_input("CNPJ")
        emp = c1.text_input("Empreendimento")
        loc = c2.text_input("Localização")
        ac = c1.text_input("Aos Cuidados")

    with st.expander("2. Escopo Técnico e Condições", expanded=True):
        st.markdown("### Preencha as seções da proposta")
        # Textos padrão conforme sua solicitação
        txt1 = st.text_area("1. Metodologia e Escopo Técnico", value="Elétrica Leve: Substituição de lâmpadas, tomadas...\nHidráulica Leve: Ajustes em torneiras, sifões...\nPortas: Fechaduras e molas...", height=120)
        txt2 = st.text_area("2. Materiais Inclusos", value="Parafusos, buchas, fita isolante, silicone, lâmpadas padrão, tomadas, fechaduras padrão...", height=100)
        txt3 = st.text_area("3. Modelo de Atendimento", value="Visitas ilimitadas em horário comercial. Resposta em até 24h úteis.", height=80)
        txt4 = st.text_area("4. Condições Comerciais", value="Faturamento: 30 dias após NF.\nValidade: 30 dias.", height=80)
        
        # Unimos com um separador especial que não será digitado pelo usuário
        escopo_unificado = f"{txt1}|||{txt2}|||{txt3}|||{txt4}"

    with st.expander("3. Itens e Fotos"):
        up_f = st.file_uploader("Anexar Fotos", accept_multiple_files=True)
        if up_f and st.button("🪄 Analisar Fotos"):
            for f in up_f:
                st.session_state.fotos.append({"file": f, "nome": "Item Verificado", "unidades": "1"})
            st.rerun()
        
        ci1, ci2, ci3 = st.columns([3, 1, 1])
        it_n = ci1.text_input("Serviço/Taxa")
        it_q = ci2.number_input("Qtd", min_value=1)
        it_v = ci3.number_input("Valor", min_value=0.0)
        if st.button("➕ Adicionar Item"):
            st.session_state.itens.append({"serv": it_n, "qtd": it_q, "total": it_q * it_v})
            st.rerun()

    total = sum(i['total'] for i in st.session_state.itens)
    
    if st.button("💾 SALVAR E GERAR LINK", type="primary", use_container_width=True):
        payload = {
            "cliente_razao_social": razao, "cliente_cnpj": cnpj, "empreendimento": emp,
            "localizacao": loc, "aos_cuidados": ac, "valor_total": total,
            "metodologia_escopo": escopo_unificado, "status": "Pendente"
        }
        try:
            res = supabase.table("orcamentos").insert(payload).execute()
            oid = res.data[0]['id']
            
            for i in st.session_state.itens:
                supabase.table("itens_orcamento").insert({"orcamento_id": oid, "servico": i['serv'], "quantidade": i['qtd'], "valor_total": i['total']}).execute()
            
            url_profix = "https://profix-gestao.streamlit.app"
            st.success(f"✅ Orçamento Criado!")
            st.code(f"{url_profix}/?id={oid}")
        except Exception as e:
            st.error(f"Erro: {e}")

    st.divider()
    st.subheader("👁️ Pré-visualização")
    prev = montar_layout_proposta(None, razao, cnpj, emp, loc, ac, escopo_unificado, st.session_state.itens, st.session_state.fotos, total)
    st.components.v1.html(prev, height=800, scrolling=True)
