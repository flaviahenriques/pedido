import streamlit as st
from datetime import datetime
import openai
from supabase import create_client
import base64
from io import BytesIO

# #########################################################
# 1) CONFIGURAÇÕES E CONEXÃO
# #########################################################
st.set_page_config(page_title="PROFIX - Gestão de Orçamentos", layout="wide")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = openai.OpenAI(api_key=OPENAI_API_KEY)

if "itens" not in st.session_state: st.session_state.itens = []
if "fotos" not in st.session_state: st.session_state.fotos = []
if "edit_id" not in st.session_state: st.session_state.edit_id = None

def carregar_imagem_base64(foto_obj):
    # Se já tiver a URL (veio do banco), retorna ela direto para o PDF
    if foto_obj.get('url_foto') and foto_obj['url_foto'].startswith("http"):
        return foto_obj['url_foto']
    try:
        conteudo = foto_obj['file'].getvalue()
        base64_img = base64.b64encode(conteudo).decode()
        ext = foto_obj['file'].name.split('.')[-1]
        return f"data:image/{ext};base64,{base64_img}"
    except:
        return "https://via.placeholder.com/400x300?text=Erro+na+Imagem"

# =========================================================
# 2) DESIGN DA PROPOSTA
# =========================================================
def montar_layout_proposta(id_orc, r_social, cnpj_val, empreend, local, cuidados, escopo, lista_itens, lista_fotos, valor_total):
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    ano_atual = datetime.now().year
    
    partes = escopo.split("|||")
    while len(partes) < 4: partes.append("")
    s1, s2, s3, s4 = partes[0], partes[1], partes[2], partes[3]

    num_exibicao = f"{ano_atual}-{str(id_orc).zfill(3)}" if id_orc else "PROVISÓRIO"

    fotos_html = ""
    if lista_fotos:
        fotos_html += f'<b class="secao-titulo">4. RELATÓRIO FOTOGRÁFICO</b>'
        fotos_html += '<div style="display: flex; flex-wrap: wrap; gap: 2%; margin-top: 15px;">'
        for f in lista_fotos:
            img_src = carregar_imagem_base64(f)
            fotos_html += f"""
            <div style="width: 48%; margin-bottom:20px; page-break-inside: avoid;">
                <img src="{img_src}" style="width:100%; height:250px; object-fit: cover; border:1px solid #ddd; border-radius:5px;">
                <p style="text-align:center; font-size:11px; font-weight:bold; color:#002d5b; margin-top:5px;">{f.get('nome','Item')}</p>
            </div>"""
        fotos_html += '</div>'

    itens_html = "".join([f"<div style='display:flex; justify-content:space-between; border-bottom:1px solid #eee; padding:8px 0; font-size:14px;'><span><b>{i['serv'].upper()}</b> (x{i['qtd']})</span><b>R$ {float(i['total']):,.2f}</b></div>" for i in lista_itens])

    return f"""
    <html>
    <head>
        <style>
            @media all {{
                body {{ font-family: Arial, sans-serif; color: #333; margin: 0; padding: 20px; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
                .no-print {{ background-color: #002d5b; color: white; padding: 12px; border: none; border-radius: 5px; cursor: pointer; margin-bottom: 20px; font-weight: bold; }}
                .secao-titulo {{ color:#002d5b; font-size:14px; text-transform: uppercase; margin-top: 25px; display:block; border-bottom: 2px solid #002d5b; padding-bottom:3px; font-weight: bold; }}
                .texto {{ text-align: justify; font-size: 13px; white-space: pre-wrap; margin-top:8px; line-height:1.4; }}
            }}
            @page {{ size: A4; margin: 1cm; }}
            @media print {{ .no-print {{ display: none !important; }} body {{ padding: 0; margin: 0; }} }}
        </style>
    </head>
    <body>
        <button class="no-print" onclick="window.print()">🖨️ IMPRIMIR / SALVAR PDF</button>

        <table style="width:100%; border-collapse: collapse; margin-bottom: 5px;">
            <tr>
                <td style="width:35%; vertical-align: middle;">
                    <img src="https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix" width="200">
                </td>
                <td style="width:65%; text-align:right; vertical-align: middle; font-size:10px; line-height: 1.5;">
                    <b style="color:#002d5b; font-size:12px;">PROFIX GESTÃO DE FACILITIES</b><br>
                    CNPJ: 52.620.102/0001-03<br>
                    Av. Marechal Câmara, 160, Centro, Rio De Janeiro RJ, 20020-907<br>
                    Tel: 21 3609-1314 | atendimento@profixmanutencao.com<br>
                    www.profixmanutencao.com
                </td>
            </tr>
        </table>
        
        <div style="background:#002d5b !important; color:white !important; text-align:center; padding:10px; font-size:18px; font-weight:bold;">
            PROPOSTA TÉCNICA COMERCIAL
        </div>
        <div style="display:flex; justify-content:space-between; margin-top:5px; font-size:12px; font-weight:bold; color:#002d5b;">
            <span>ORÇAMENTO Nº: {num_exibicao}</span>
            <span>Rio de Janeiro, {data_hoje}</span>
        </div>
        
        <div style="border:1px solid #002d5b; padding:12px; margin-top:10px; margin-bottom:15px; font-size:13px; display:flex;">
            <div style="flex:1;"><b>CLIENTE:</b> {r_social}<br><b>CNPJ:</b> {cnpj_val}</div>
            <div style="flex:1; border-left: 1px solid #002d5b; padding-left:15px;"><b>EMPREENDIMENTO:</b> {empreend}<br><b>A/C:</b> {cuidados}</div>
        </div>

        <b class="secao-titulo">1. METODOLOGIA E ESCOPO TÉCNICO</b><div class="texto">{s1}</div>
        <b class="secao-titulo">2. MATERIAIS INCLUSOS</b><div class="texto">{s2}</div>
        <b class="secao-titulo">3. ATENDIMENTO E SUPORTE</b><div class="texto">{s3}</div>
        
        {fotos_html}

        <div style="page-break-inside: avoid;">
            <b class="secao-titulo">5. DETALHAMENTO DE INVESTIMENTO</b>
            <div style="margin-top:10px;">{itens_html}</div>
            
            <div style="margin-top:30px; display:flex; justify-content:space-between; align-items:flex-start;">
                <div style="font-size:11px; color:#555; flex:1; padding-right: 20px;">{s4}</div>
                <div style="background:#f1f4f9 !important; padding:20px; border-left:8px solid #002d5b; text-align:right; min-width:260px;">
                    <small style="color:#666;">VALOR TOTAL DO PROJETO</small><br>
                    <b style="font-size:26px; color:#002d5b;">R$ {valor_total:,.2f}</b>
                </div>
            </div>
        </div>
    </body>
    </html>"""

# =========================================================
# 3) INTERFACE
# =========================================================
with st.sidebar:
    st.image("https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix", width=180)
    st.title("🛡️ Painel PROFIX")
    menu = st.radio("Menu:", ["Novo Orçamento", "Gerenciar Pedidos"])
    if st.button("➕ Limpar e Iniciar Novo"):
        st.session_state.itens = []; st.session_state.fotos = []; st.session_state.edit_id = None
        st.rerun()

if menu == "Gerenciar Pedidos":
    st.header("📋 Histórico")
    pedidos = supabase.table("orcamentos").select("*").order("id", desc=True).execute().data
    lista_cli = sorted(list(set([p['cliente_razao_social'] for p in pedidos if p['cliente_razao_social']])))
    filtro = st.selectbox("Filtrar Cliente", ["Todos"] + lista_cli)
    for p in pedidos:
        if filtro != "Todos" and p['cliente_razao_social'] != filtro: continue
        with st.expander(f"ID {p['id']} - {p['cliente_razao_social']} - {p['empreendimento']}"):
            if st.button("📝 Editar", key=f"ed_{p['id']}"):
                st.session_state.edit_id = p['id']
                it_db = supabase.table("itens_orcamento").select("*").eq("orcamento_id", p['id']).execute().data
                ft_db = supabase.table("fotos_relatorio").select("*").eq("orcamento_id", p['id']).execute().data
                
                # Atualiza Itens
                st.session_state.itens = [{"serv": i['servico'], "qtd": i['quantidade'], "total": i['valor_total']} for i in it_db]
                
                # CORREÇÃO: Força o carregamento das fotos do banco para o session_state
                st.session_state.fotos = []
                for f in ft_db:
                    st.session_state.fotos.append({
                        "url_foto": f['url_foto'], 
                        "nome": f['nome_item']
                    })
                st.rerun()

else:
    st.header("📑 " + ("Editando Proposta" if st.session_state.edit_id else "Nova Proposta"))
    
    dados_memo = supabase.table("orcamentos").select("cliente_razao_social, cliente_cnpj, empreendimento, localizacao, aos_cuidados").execute().data
    clientes_memo = {d['cliente_razao_social']: d for d in dados_memo if d['cliente_razao_social']}

    with st.expander("1. Dados do Cliente", expanded=True):
        sel_c = st.selectbox("Cliente Existente?", ["-- Novo --"] + list(clientes_memo.keys()))
        rz, cnp, emp, loc, ac, esc_db = "", "", "", "", "", "||||||"
        if st.session_state.edit_id:
            curr = supabase.table("orcamentos").select("*").eq("id", st.session_state.edit_id).execute().data[0]
            rz, cnp, emp, loc, ac, esc_db = curr['cliente_razao_social'], curr['cliente_cnpj'], curr['empreendimento'], curr['localizacao'], curr['aos_cuidados'], curr['metodologia_escopo']
        elif sel_c != "-- Novo --":
            c = clientes_memo[sel_c]; rz, cnp, emp, loc, ac = c['cliente_razao_social'], c['cliente_cnpj'], c['empreendimento'], c['localizacao'], c['aos_cuidados']

        c1, c2 = st.columns(2)
        razao = c1.text_input("Razão Social", value=rz)
        cnpj_val = c2.text_input("CNPJ", value=cnp)
        emp_val = c1.text_input("Empreendimento", value=emp)
        loc_val = c2.text_input("Localização", value=loc)
        ac_val = c1.text_input("Aos Cuidados", value=ac)

    with st.expander("2. Escopo Técnico", expanded=True):
        p_esc = esc_db.split("|||")
        
        if not st.session_state.edit_id and (len(p_esc) < 2 or p_esc[0] == ""):
            p_esc = [
                """A PROFIX atuará com foco na preservação do padrão estético e na manutenção da integridade das instalações, assegurando que os apartamentos decorados e estandes de vendas mantenham-se em estado de 'novo' e prontos para visitação...""",
                """A PROFIX assume o fornecimento integral de todos os materiais de consumo...""",
                """Perfil da Equipe: Os serviços são executados por profissionais capacitados...""",
                """<b>CONDIÇÕES COMERCIAIS</b><br>Vigência do Contrato: 12 (doze) meses..."""
            ]

        while len(p_esc) < 4: p_esc.append("")
        t1 = st.text_area("1. Metodologia", value=p_esc[0], height=400)
        t2 = st.text_area("2. Materiais", value=p_esc[1], height=300)
        t3 = st.text_area("3. Atendimento", value=p_esc[2], height=250)
        t4 = st.text_area("Condições Comerciais", value=p_esc[3], height=250)
        escopo_final = f"{t1}|||{t2}|||{t3}|||{t4}"

    with st.expander("3. Fotos e Valores", expanded=True):
        up_f = st.file_uploader("Subir Fotos", accept_multiple_files=True)
        if up_f and st.button("🪄 Processar Fotos"):
            for f in up_f:
                nome_limpo = f.name.rsplit('.', 1)[0].replace('_', ' ').title()
                st.session_state.fotos.append({"file": f, "nome": nome_limpo})
            st.rerun()
        
        for idx, f in enumerate(st.session_state.fotos):
            cc1, cc2, cc3 = st.columns([1, 4, 0.5])
            
            # CORREÇÃO: Determina a imagem a ser exibida na interface (URL do banco ou arquivo bruto do upload)
            img_preview = f.get('url_foto') if f.get('url_foto') else f.get('file')
            if img_preview:
                cc1.image(img_preview, width=80)
            
            f['nome'] = cc2.text_input(f"Legenda {idx+1}", f['nome'], key=f"f_txt_{idx}")
            if cc3.button("🗑️", key=f"del_f_{idx}"): st.session_state.fotos.pop(idx); st.rerun()

        st.divider()
        ci1, ci2, ci3 = st.columns([3, 1, 1])
        it_n = ci1.text_input("Serviço")
        it_q = ci2.number_input("Qtd", min_value=1, value=1)
        it_v = ci3.number_input("Preço Unitário", min_value=0.0)
        if st.button("➕ Adicionar Item"):
            st.session_state.itens.append({"serv": it_n, "qtd": it_q, "total": it_q * it_v}); st.rerun()
        
        for i_idx, it in enumerate(st.session_state.itens):
            c_it1, c_it2, c_it3 = st.columns([4, 1, 0.5])
            c_it1.write(f"**{it['serv']}** (x{it['qtd']})")
            c_it2.write(f"R$ {it['total']:,.2f}")
            if c_it3.button("❌", key=f"del_it_{i_idx}"): st.session_state.itens.pop(i_idx); st.rerun()

    total_proposta = sum(i['total'] for i in st.session_state.itens)
    
    if st.button("💾 SALVAR PROPOSTA", type="primary", use_container_width=True):
        payload = {"cliente_razao_social": razao, "cliente_cnpj": cnpj_val, "empreendimento": emp_val, "localizacao": loc_val, "aos_cuidados": ac_val, "valor_total": total_proposta, "metodologia_escopo": escopo_final, "status": "Enviado"}
        if st.session_state.edit_id:
            oid = st.session_state.edit_id
            supabase.table("orcamentos").update(payload).eq("id", oid).execute()
            supabase.table("itens_orcamento").delete().eq("orcamento_id", oid).execute()
            supabase.table("fotos_relatorio").delete().eq("orcamento_id", oid).execute()
        else:
            res = supabase.table("orcamentos").insert(payload).execute(); oid = res.data[0]['id']
            st.session_state.edit_id = oid

        for i in st.session_state.itens: supabase.table("itens_orcamento").insert({"orcamento_id": oid, "servico": i['serv'], "quantidade": i['qtd'], "valor_total": i['total']}).execute()
        for f in st.session_state.fotos: 
            url_f = f.get('url_foto', 'https://via.placeholder.com/400x300?text=Foto+Salva')
            supabase.table("fotos_relatorio").insert({"orcamento_id": oid, "nome_item": f['nome'], "url_foto": url_f}).execute()
        st.success(f"✅ Proposta Salva! Número: {datetime.now().year}-{str(oid).zfill(3)}")

    st.divider()
    st.subheader("👁️ Pré-visualização")
    html_gerado = montar_layout_proposta(st.session_state.edit_id, razao, cnpj_val, emp_val, loc_val, ac_val, escopo_final, st.session_state.itens, st.session_state.fotos, total_proposta)
    st.components.v1.html(html_gerado, height=1200, scrolling=True)
