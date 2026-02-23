import streamlit as st
from datetime import datetime
import openai
from PIL import Image
from supabase import create_client
import base64
import io

# #########################################################
# 1) CONFIGURAÇÕES DE PÁGINA E CONEXÕES
# #########################################################
st.set_page_config(page_title="PROFIX - Gerador de Orçamentos", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

# =========================================================
# FUNÇÃO AUXILIAR PARA FOTOS EM BASE64 (PARA PRÉ-VISUALIZAÇÃO)
# =========================================================
def get_image_base64(file_obj):
    if isinstance(file_obj, str): # Se já for uma URL
        return file_obj
    try:
        file_obj.seek(0)
        b64 = base64.b64encode(file_obj.read()).decode()
        return f"data:image/jpeg;base64,{b64}"
    except:
        return ""

# =========================================================
# 2) FUNÇÃO PARA MONTAR O HTML DO ORÇAMENTO (DESIGN A4)
# =========================================================
def montar_layout_proposta(orc_id, r_social, cnpj_val, empreend, local, cuidados, escopo, lista_itens, lista_fotos, valor_total):
    data_hoje = datetime.now().strftime("%d/%m/%Y")

    itens_html = ""
    for idx, item in enumerate(lista_itens, start=1):
        nome_s = item.get('servico') or item.get('serv', 'Serviço')
        qtd_s = item.get('quantidade') or item.get('qtd', 1)
        v_total = item.get('valor_total') or item.get('total', 0.0)
        itens_html += f"""
        <div style="display:flex; justify-content:space-between; border-bottom:1px solid #eee; padding:8px 0; font-size:14px;">
            <span style="flex: 2;"><b>{idx}. {nome_s.upper()}</b></span>
            <span style="flex: 1; text-align: center;">Qtd: {qtd_s}</span>
            <span style="flex: 1; text-align: right;"><b>R$ {v_total:,.2f}</b></span>
        </div>"""

    fotos_html = ""
    if lista_fotos:
        fotos_html += "<br><br><b style='color:#002d5b; font-size:16px;'>3. RELATÓRIO FOTOGRÁFICO</b><br><br>"
        fotos_html += '<div style="display: flex; flex-wrap: wrap; gap: 20px; justify-content: space-between;">'
        for f_idx, foto in enumerate(lista_fotos):
            # Lógica para pegar a imagem (URL ou arquivo local)
            src = foto.get('url_foto') or foto.get('file')
            if not isinstance(src, str): # Se for um objeto de upload
                src = get_image_base64(src)
            
            legenda = foto.get('nome_item') or foto.get('nome', 'Item')
            qtd_un = foto.get('unidades') or foto.get('qtd', '1')
            
            fotos_html += f"""
            <div style="width: 45%; margin-bottom:20px; page-break-inside: avoid;">
                <div style="width: 100%; height: 200px; overflow: hidden; border-radius:8px; border: 1px solid #ddd;">
                    <img src="{src}" style="width:100%; height:100%; object-fit: cover;">
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
    body {{ background: transparent; margin: 0; padding: 0; font-family: Arial, sans-serif; }}
    .folha-documento {{
        background-color: white; max-width: 800px; margin: 0 auto; padding: 40px; color: black; box-sizing: border-box;
    }}
    .titulo-barra {{ background-color: #002d5b; color: white; text-align: center; padding: 12px; font-weight: bold; margin: 20px 0; }}
    .texto-escopo {{ margin: 10px 0 25px 0; text-align: justify; font-size: 13px; white-space: pre-wrap; word-wrap: break-word; }}
    @media print {{
        body {{ background: white !important; }}
        .folha-documento {{ max-width: 100%; width: 100%; padding: 0; margin: 0; box-shadow: none; }}
        .titulo-barra {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
        @page {{ size: A4; margin: 15mm; }}
    }}
</style>
</head>
<body>
<div class="folha-documento">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <img src="https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix" width="180">
        <div style="text-align:right; font-size:10px; line-height:1.4;">
            <b>PROFIX GESTÃO DE FACILITIES</b><br>
            CNPJ: 52.620.102/0001-03<br>
            Av. Marechal Câmara, 160, Sala 1107<br>
            Centro, Rio de Janeiro - RJ
        </div>
    </div>
    <div class="titulo-barra">PROPOSTA TÉCNICA COMERCIAL</div>
    <div style="text-align:right; font-size:12px; margin-bottom:15px;">Rio de Janeiro, {data_hoje}</div>
    <div style="display:flex; border:1px solid #dcdcdc; margin-bottom:25px; font-size:12px;">
        <div style="width:6px; background:#002d5b;"></div>
        <div style="flex:1; padding:12px;">
            <b>RAZÃO SOCIAL:</b><br>{r_social or '—'}<br><br>
            <b>CNPJ:</b><br>{cnpj_val or '—'}<br><br>
            <b>EMPREENDIMENTO:</b><br>{empreend or '—'}
        </div>
        <div style="flex:1; padding:12px; border-left:1px solid #dcdcdc;">
            <b>ENDEREÇO:</b><br>{local or '—'}<br><br>
            <b>A/C:</b><br>{cuidados or '—'}
        </div>
    </div>
    <b style='color:#002d5b; font-size:15px;'>1. METODOLOGIA E ESCOPO TÉCNICO</b>
    <div class="texto-escopo">{escopo or '—'}</div>
    <b style='color:#002d5b; font-size:15px;'>2. DETALHAMENTO DE SERVIÇOS</b>
    {itens_html}
    <div style="display:flex; margin-top:30px; gap:20px; align-items:flex-start;">
        <div style="flex:1; font-size:11px;">
            <b>CONDIÇÕES GERAIS:</b><br>
            • Validade da Proposta: 10 dias úteis.<br>
            • Pagamento conforme contrato.
        </div>
        <div style="width:250px; background:#f1f4f9; padding:20px; border-left:6px solid #002d5b; text-align:right;">
            <small style="color:#666;">TOTAL DO INVESTIMENTO</small><br>
            <span style="font-size:24px; font-weight:bold; color:#002d5b;">R$ {valor_total:,.2f}</span>
        </div>
    </div>
    {fotos_html}
</div>
</body>
</html>
"""

# #########################################################
# 3) LÓGICA DE NAVEGAÇÃO E ESTADOS
# #########################################################
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
        st.components.v1.html(f"{html_view}<script>window.print();</script>", height=2000, scrolling=True)
        st.stop()
    except: st.error("Orçamento não encontrado.")

with st.sidebar:
    st.title("🛡️ Painel PROFIX")
    opcoes = ["Criar Novo", "Gerenciar Pedidos"]
    st.session_state.pagina = st.radio("Navegação", opcoes, index=opcoes.index(st.session_state.pagina))
    if st.button("🧹 Novo (Limpar)"):
        st.session_state.itens, st.session_state.fotos, st.session_state.edit_id = [], [], None
        st.rerun()

# #########################################################
# 4) PÁGINA: GERENCIAR PEDIDOS
# #########################################################
if st.session_state.pagina == "Gerenciar Pedidos":
    st.subheader("📋 Histórico")
    pedidos = supabase.table("orcamentos").select("*").order("id", desc=True).execute().data
    for p in pedidos:
        col1, col2, col3, col4 = st.columns([3, 1, 1, 1])
        col1.write(f"**{p['cliente_razao_social']}**")
        col2.write(f"R$ {float(p['valor_total']):,.2f}")
        col3.write(p['status'])
        if col4.button("📝 Editar", key=f"ed_{p['id']}"):
            st.session_state.edit_id = p['id']
            st.session_state.itens = [{"serv": i['servico'], "qtd": i['quantidade'], "total": i['valor_total']} for i in supabase.table("itens_orcamento").select("*").eq("orcamento_id", p['id']).execute().data]
            st.session_state.fotos = [{"id": f['id'], "file": f['url_foto'], "nome": f['nome_item'], "url_foto": f['url_foto'], "unidades": f['unidades']} for f in supabase.table("fotos_relatorio").select("*").eq("orcamento_id", p['id']).execute().data]
            st.session_state.pagina = "Criar Novo"
            st.rerun()
        st.divider()

# #########################################################
# 5) PÁGINA: CRIAR / EDITAR ORÇAMENTO
# #########################################################
else:
    modo_ed = st.session_state.edit_id is not None
    st.title("🛡️ " + ("Editar Orçamento" if modo_ed else "Novo Orçamento"))
    
    dados_ed = {}
    if modo_ed:
        dados_ed = supabase.table("orcamentos").select("*").eq("id", st.session_state.edit_id).execute().data[0]

    with st.expander("1. Dados do Cliente", expanded=True):
        c1, c2 = st.columns(2)
        razao = c1.text_input("Razão Social", value=dados_ed.get('cliente_razao_social', ""))
        cnpj = c2.text_input("CNPJ", value=dados_ed.get('cliente_cnpj', ""))
        emp = c1.text_input("Empreendimento", value=dados_ed.get('empreendimento', ""))
        loc = c2.text_input("Localização", value=dados_ed.get('localizacao', ""))
        ac = c1.text_input("Aos Cuidados", value=dados_ed.get('aos_cuidados', ""))

    with st.expander("2. Escopo e Fotos"):
        escopo = st.text_area("Metodologia Técnica", value=dados_ed.get('metodologia_escopo', ""), height=150)
        up_f = st.file_uploader("Adicionar Fotos", accept_multiple_files=True)
        if up_f and st.button("🪄 IA Analisar Fotos"):
            for f in up_f:
                b64 = base64.b64encode(f.read()).decode('utf-8')
                f.seek(0)
                try:
                    res = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": "user", "content": [{"type": "text", "text": "O que é este item de manutenção? (3 palavras)"}, {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}]}],
                        max_tokens=20
                    )
                    ia_n = res.choices[0].message.content
                except: ia_n = "Item verificado"
                st.session_state.fotos.append({"id": f"{f.name}_{datetime.now().microsecond}", "file": f, "nome": ia_n, "unidades": "1"})
            st.rerun()

        for idx, f in enumerate(st.session_state.fotos):
            cc1, cc2, cc3, cc4 = st.columns([1, 3, 1, 0.5])
            cc1.image(f['file'], width=100)
            f['nome'] = cc2.text_input(f"Descrição {idx}", f['nome'], key=f"f_n_{idx}")
            f['unidades'] = cc3.text_input(f"Qtd {idx}", f.get('unidades', '1'), key=f"f_q_{idx}")
            if cc4.button("🗑️", key=f"f_d_{idx}"):
                st.session_state.fotos.pop(idx); st.rerun()

    with st.expander("3. Itens e Valores"):
        ci1, ci2, ci3 = st.columns([3, 1, 1])
        it_n = ci1.text_input("Serviço")
        it_q = ci2.number_input("Qtd", min_value=1, value=1)
        it_v = ci3.number_input("Unitário R$", min_value=0.0)
        if st.button("➕ Adicionar Item"):
            st.session_state.itens.append({"serv": it_n, "qtd": it_q, "total": it_q * it_v})
            st.rerun()
        for i_idx, it in enumerate(st.session_state.itens):
            c_it1, c_it2, c_it3 = st.columns([4, 1, 0.5])
            c_it1.write(f"✅ {it['serv']} (x{it['qtd']})")
            c_it2.write(f"R$ {it['total']:,.2f}")
            if c_it3.button("❌", key=f"it_d_{i_idx}"):
                st.session_state.itens.pop(i_idx); st.rerun()

    total = sum(i['total'] for i in st.session_state.itens)
    st.markdown(f"### Total: R$ {total:,.2f}")

    if st.button("💾 SALVAR ORÇAMENTO", type="primary", use_container_width=True):
        payload = {
            "cliente_razao_social": razao, "cliente_cnpj": cnpj, "empreendimento": emp,
            "localizacao": loc, "aos_cuidados": ac, "valor_total": total,
            "metodologia_escopo": escopo, "status": "Pendente"
        }
        try:
            if modo_ed:
                oid = st.session_state.edit_id
                supabase.table("orcamentos").update(payload).eq("id", oid).execute()
                supabase.table("itens_orcamento").delete().eq("orcamento_id", oid).execute()
                supabase.table("fotos_relatorio").delete().eq("orcamento_id", oid).execute()
            else:
                oid = supabase.table("orcamentos").insert(payload).execute().data[0]['id']

            for i in st.session_state.itens:
                supabase.table("itens_orcamento").insert({"orcamento_id": oid, "servico": i['serv'], "quantidade": i['qtd'], "valor_total": i['total']}).execute()
            for f_idx, f in enumerate(st.session_state.fotos):
                if isinstance(f['file'], str) and f['file'].startswith('http'):
                    url = f['file']
                else:
                    agora = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
                    f_path = f"{oid}/{agora}_{f_idx}.jpg"
                    supabase.storage.from_("fotos_orcamentos").upload(path=f_path, file=f['file'].getvalue(), file_options={"content-type": "image/jpeg", "upsert": "true"})
                    url = supabase.storage.from_("fotos_orcamentos").get_public_url(f_path)
                supabase.table("fotos_relatorio").insert({"orcamento_id": oid, "nome_item": f['nome'], "url_foto": url, "unidades": f['unidades']}).execute()
            
            st.success("✅ Orçamento salvo!")
        except Exception as e:
            st.error(f"Erro ao salvar: {e}")

    # =========================================================
    # ÁREA DE PRÉ-VISUALIZAÇÃO (CORRIGIDA PARA MOSTRAR FOTOS SEMPRE)
    # =========================================================
    st.divider()
    st.subheader("👁️ Pré-visualização")
    html_final = montar_layout_proposta(None, razao, cnpj, emp, loc, ac, escopo, st.session_state.itens, st.session_state.fotos, total)
    
    st.components.v1.html(f"""
        <style>
            @media print {{
                .no-print {{ display: none !important; }}
                .preview-container {{ border: none !important; background: white !important; padding: 0 !important; }}
            }}
        </style>
        <div class="no-print" style="margin-bottom: 20px;">
            <button onclick="window.print()" style="
                width: 100%; background: #002d5b; color: white; padding: 18px; 
                border: none; border-radius: 8px; cursor: pointer; font-weight: bold; 
                font-size: 18px; box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            ">🖨️ GERAR PDF / IMPRIMIR</button>
        </div>
        <div class="preview-container" style="border: 1px solid #ddd; background: #f9f9f9; padding: 10px;">
            {html_final}
        </div>
    """, height=1200, scrolling=True)
