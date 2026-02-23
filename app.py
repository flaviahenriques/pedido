import streamlit as st
from datetime import datetime
import openai
from supabase import create_client
import base64
import requests
from io import BytesIO
import uuid

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

@st.cache_data(show_spinner=False)
def transformar_url_em_base64(url):
    """ Baixa a foto da URL e converte em Base64 para o PDF """
    if not url or not str(url).startswith("http"):
        return url
    try:
        headers = {'User-Agent': 'Mozilla/5.0'}
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code == 200:
            content_type = res.headers.get('content-type', 'image/png')
            b64 = base64.b64encode(res.content).decode()
            return f"data:{content_type};base64,{b64}"
    except:
        return url
    return url

def upload_imagem_supabase(foto_obj):
    """ Faz o upload real da imagem para o Storage e retorna a URL pública """
    try:
        # Se já for uma URL do Supabase, não faz upload de novo
        if "url_foto" in foto_obj and str(foto_obj['url_foto']).startswith("http"):
            return foto_obj['url_foto']
            
        if 'file' in foto_obj:
            file_content = foto_obj['file'].getvalue()
            file_ext = foto_obj['file'].name.split('.')[-1]
            file_name = f"{uuid.uuid4()}.{file_ext}"
            
            # Caminho no Bucket 'fotos_orcamentos'
            bucket_name = "fotos_orcamentos"
            
            # Upload para o Storage
            supabase.storage.from_(bucket_name).upload(file_name, file_content)
            
            # Gerar URL Pública
            res = supabase.storage.from_(bucket_name).get_public_url(file_name)
            return res
    except Exception as e:
        st.error(f"Erro no Upload: {e}")
        return None
    return None

# =========================================================
# 2) DESIGN DA PROPOSTA
# =========================================================
def montar_layout_proposta(id_orc, r_social, cnpj_val, empreend, local, cuidados, escopo, lista_itens, lista_fotos, valor_total):
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    partes = escopo.split("|||")
    while len(partes) < 4: partes.append("")
    s1, s2, s3, s4 = partes[0], partes[1], partes[2], partes[3]
    num_exibicao = str(id_orc).zfill(4) if id_orc else "0000"

    fotos_html = ""
    if lista_fotos:
        fotos_html += '<b class="secao-titulo">4. RELATÓRIO FOTOGRÁFICO</b>'
        fotos_html += '<div style="display: flex; flex-wrap: wrap; gap: 2%; margin-top: 15px;">'
        for f in lista_fotos:
            # Para o PDF, precisamos de Base64. Se for URL, converte. Se for novo upload, pega o file.
            img_src = ""
            if f.get('url_foto') and str(f['url_foto']).startswith("data:image"):
                img_src = f['url_foto']
            elif f.get('url_foto') and str(f['url_foto']).startswith("http"):
                img_src = transformar_url_em_base64(f['url_foto'])
            elif 'file' in f:
                b64 = base64.b64encode(f['file'].getvalue()).decode()
                img_src = f"data:image/png;base64,{b64}"

            fotos_html += f"""
            <div style="width: 48%; margin-bottom:20px; page-break-inside: avoid;">
                <img src="{img_src}" 
                     onerror="this.src='https://via.placeholder.com/400x300?text=Imagem+Nao+Disponivel';"
                     style="width:100%; height:250px; object-fit: cover; border:1px solid #ddd; border-radius:5px;">
                <p style="text-align:center; font-size:11px; font-weight:bold; color:#002d5b; margin-top:5px;">{f.get('nome','Item')}</p>
            </div>"""
        fotos_html += '</div>'

    itens_html = "".join([f"<div style='display:flex; justify-content:space-between; border-bottom:1px solid #eee; padding:8px 0; font-size:14px;'><span><b>{i['serv'].upper()}</b> (x{i['qtd']})</span><b>R$ {float(i['total']):,.2f}</b></div>" for i in lista_itens])

    return f"""
    <html>
    <head>
        <style>
            @media all {{
                body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; margin: 0; padding: 0; -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
                .no-print {{ background-color: #002d5b; color: white; padding: 12px 24px; border: none; border-radius: 4px; cursor: pointer; margin: 20px; font-weight: bold; }}
                .secao-titulo {{ color:#002d5b; font-size:14px; text-transform: uppercase; margin-top: 30px; display:block; border-bottom: 2px solid #002d5b; padding-bottom:5px; font-weight: bold; }}
                .texto {{ text-align: justify; font-size: 13px; white-space: pre-wrap; margin-top:10px; line-height:1.5; color: #444; }}
                .conteudo-pagina {{ padding: 40px 50px; page-break-before: always; }}
                .capa-container {{ height: 29.7cm; width: 21cm; display: flex; page-break-after: always; background-color: white; }}
                .capa-sidebar {{ width: 60px; background-color: #002d5b; height: 100%; }}
                .capa-main {{ flex: 1; padding: 80px 60px; display: flex; flex-direction: column; justify-content: space-between; }}
                .capa-header {{ border-bottom: 4px solid #002d5b; padding-bottom: 20px; }}
                .capa-titulo {{ font-size: 48px; color: #002d5b; font-weight: 800; margin: 0; }}
                .capa-subtitulo {{ font-size: 18px; color: #666; text-transform: uppercase; letter-spacing: 4px; margin-top: 10px; }}
                .capa-info {{ margin-top: 80px; }}
                .capa-label {{ color: #002d5b; font-size: 12px; font-weight: bold; text-transform: uppercase; margin-bottom: 5px; display: block; }}
                .capa-valor {{ font-size: 20px; color: #333; margin-bottom: 25px; display: block; }}
                .capa-footer {{ font-size: 14px; color: #888; border-top: 1px solid #eee; padding-top: 20px; }}
            }}
            @page {{ size: A4; margin: 0; }}
            @media print {{ .no-print {{ display: none !important; }} }}
        </style>
    </head>
    <body>
        <button class="no-print" onclick="window.print()">🖨️ GERAR PDF PROFISSIONAL</button>
        <div class="capa-container">
            <div class="capa-sidebar"></div>
            <div class="capa-main">
                <div class="capa-header">
                    <img src="https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix" width="220">
                    <div style="margin-top: 60px;">
                        <h1 class="capa-titulo">PROPOSTA<br>TÉCNICA</h1>
                        <div class="capa-subtitulo">Manutenção e Facilities</div>
                    </div>
                </div>
                <div class="capa-info">
                    <span class="capa-label">Preparado para:</span>
                    <span class="capa-valor"><b>{r_social}</b></span>
                    <span class="capa-label">Empreendimento:</span>
                    <span class="capa-valor">{empreend}</span>
                    <span class="capa-label">Referência:</span>
                    <span class="capa-valor">ORÇAMENTO #{num_exibicao}</span>
                </div>
                <div class="capa-footer">
                    <div style="display: flex; justify-content: space-between;">
                        <span>Rio de Janeiro, {data_hoje}</span>
                        <span><b>PROFIX</b> | Gestão de Facilities</span>
                    </div>
                </div>
            </div>
        </div>
        <div class="conteudo-pagina">
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
            <div style="background:#002d5b !important; color:white !important; text-align:center; padding:10px; font-size:18px; font-weight:bold;">PROPOSTA TÉCNICA COMERCIAL</div>
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
        </div>
    </body>
    </html>"""

# =========================================================
# 3) INTERFACE
# =================================########################
with st.sidebar:
    st.image("https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix", width=180)
    st.title("🛡️ Painel PROFIX")
    menu = st.radio("Menu:", ["Novo Orçamento", "Gerenciar Pedidos"])
    if st.button("➕ Limpar e Iniciar Novo"):
        st.session_state.itens = []; st.session_state.fotos = []; st.session_state.edit_id = None
        st.rerun()

if menu == "Gerenciar Pedidos":
    st.header("📋 Gerenciar Pedidos")
    pedidos = supabase.table("orcamentos").select("*").order("id", desc=True).execute().data
    
    for p in pedidos:
        with st.expander(f"ID {str(p['id']).zfill(4)} - {p['cliente_razao_social']}"):
            if st.button("📝 Editar", key=f"ed_{p['id']}"):
                st.session_state.edit_id = p['id']
                # Puxa dados do banco
                it_db = supabase.table("itens_orcamento").select("*").eq("orcamento_id", p['id']).execute().data
                ft_db = supabase.table("fotos_relatorio").select("*").eq("orcamento_id", p['id']).execute().data
                
                st.session_state.itens = [{"serv": i['servico'], "qtd": i['quantidade'], "total": i['valor_total']} for i in it_db]
                # Carrega as URLs reais do banco para o state
                st.session_state.fotos = [{"url_foto": f['url_foto'], "nome": f['nome_item']} for f in ft_db]
                st.rerun()

else:
    st.header("📑 " + ("Editando Proposta" if st.session_state.edit_id else "Nova Proposta"))
    
    # Busca clientes para auto-complete
    dados_memo = supabase.table("orcamentos").select("cliente_razao_social, cliente_cnpj, empreendimento, localizacao, aos_cuidados").execute().data
    clientes_memo = {d['cliente_razao_social']: d for d in dados_memo if d['cliente_razao_social']}

    with st.expander("1. Dados do Cliente", expanded=True):
        sel_c = st.selectbox("Cliente Existente?", ["-- Novo --"] + list(clientes_memo.keys()))
        rz, cnp, emp, loc, ac, esc_db = "", "", "", "", "", "||| ||| ||| "
        
        if st.session_state.edit_id:
            curr = supabase.table("orcamentos").select("*").eq("id", st.session_state.edit_id).execute().data[0]
            rz, cnp, emp, loc, ac, esc_db = curr['cliente_razao_social'], curr['cliente_cnpj'], curr['empreendimento'], curr['localizacao'], curr['aos_cuidados'], curr['metodologia_escopo']
        elif sel_c != "-- Novo --":
            c = clientes_memo[sel_c]
            rz, cnp, emp, loc, ac = c['cliente_razao_social'], c['cliente_cnpj'], c['empreendimento'], c['localizacao'], c['aos_cuidados']

        c1, c2 = st.columns(2)
        razao = c1.text_input("Razão Social", value=rz)
        cnpj_val = c2.text_input("CNPJ", value=cnp)
        emp_val = c1.text_input("Empreendimento", value=emp)
        loc_val = c2.text_input("Localização", value=loc)
        ac_val = c1.text_input("Aos Cuidados", value=ac)

    with st.expander("2. Escopo Técnico", expanded=True):
        p_esc = esc_db.split("|||")
        while len(p_esc) < 4: p_esc.append("")
        t1 = st.text_area("1. Metodologia", value=p_esc[0], height=300)
        t2 = st.text_area("2. Materiais", value=p_esc[1], height=200)
        t3 = st.text_area("3. Atendimento", value=p_esc[2], height=150)
        t4 = st.text_area("Condições Comerciais", value=p_esc[3], height=150)
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
            # Preview da imagem (URL ou File)
            preview = f.get('url_foto') if f.get('url_foto') else f.get('file')
            if preview: cc1.image(preview, width=120)
            f['nome'] = cc2.text_input(f"Legenda {idx}", f['nome'], key=f"f_txt_{idx}")
            if cc3.button("🗑️", key=f"del_f_{idx}"): st.session_state.fotos.pop(idx); st.rerun()

        st.divider()
        ci1, ci2, ci3 = st.columns([3, 1, 1])
        it_n, it_q, it_v = ci1.text_input("Serviço"), ci2.number_input("Qtd", 1), ci3.number_input("Preço Unitário", 0.0)
        if st.button("➕ Adicionar Item"):
            st.session_state.itens.append({"serv": it_n, "qtd": it_q, "total": it_q * it_v}); st.rerun()
        
        for i_idx, it in enumerate(st.session_state.itens):
            c_it1, c_it2, c_it3 = st.columns([4, 1, 0.5])
            c_it1.write(f"**{it['serv']}** (x{it['qtd']})")
            c_it2.write(f"R$ {it['total']:,.2f}")
            if c_it3.button("❌", key=f"del_it_{i_idx}"): st.session_state.itens.pop(i_idx); st.rerun()

    total_proposta = sum(i['total'] for i in st.session_state.itens)
    
    if st.button("💾 SALVAR PROPOSTA", type="primary", use_container_width=True):
        with st.spinner("Salvando e fazendo upload das imagens..."):
            payload = {"cliente_razao_social": razao, "cliente_cnpj": cnpj_val, "empreendimento": emp_val, "localizacao": loc_val, "aos_cuidados": ac_val, "valor_total": total_proposta, "metodologia_escopo": escopo_final}
            
            if st.session_state.edit_id:
                oid = st.session_state.edit_id
                supabase.table("orcamentos").update(payload).eq("id", oid).execute()
                supabase.table("itens_orcamento").delete().eq("orcamento_id", oid).execute()
                supabase.table("fotos_relatorio").delete().eq("orcamento_id", oid).execute()
            else:
                res = supabase.table("orcamentos").insert(payload).execute()
                oid = res.data[0]['id']
                st.session_state.edit_id = oid

            for i in st.session_state.itens: 
                supabase.table("itens_orcamento").insert({"orcamento_id": oid, "servico": i['serv'], "quantidade": i['qtd'], "valor_total": i['total']}).execute()
            
            for f in st.session_state.fotos: 
                # AQUI ESTÁ A MÁGICA: Ele faz o upload real pro Storage antes de salvar a URL no banco
                url_final = upload_imagem_supabase(f)
                if url_final:
                    supabase.table("fotos_relatorio").insert({"orcamento_id": oid, "nome_item": f['nome'], "url_foto": url_final}).execute()
            
            st.success(f"✅ Proposta Salva! ID: {oid}")
            st.rerun()

    st.divider()
    html_gerado = montar_layout_proposta(st.session_state.edit_id, razao, cnpj_val, emp_val, loc_val, ac_val, escopo_final, st.session_state.itens, st.session_state.fotos, total_proposta)
    st.components.v1.html(html_gerado, height=1200, scrolling=True)
