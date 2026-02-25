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
    """ Converte URL do Storage em Base64 para garantir renderização no PDF """
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
    """ Realiza o upload real para o Bucket 'fotos_orcamentos' """
    try:
        if "url_foto" in foto_obj and str(foto_obj['url_foto']).startswith("http"):
            return foto_obj['url_foto']
            
        if 'file' in foto_obj:
            file_content = foto_obj['file'].getvalue()
            file_ext = foto_obj['file'].name.split('.')[-1]
            file_name = f"{uuid.uuid4()}.{file_ext}"
            bucket_name = "fotos_orcamentos"
            
            supabase.storage.from_(bucket_name).upload(file_name, file_content)
            res = supabase.storage.from_(bucket_name).get_public_url(file_name)
            return res
    except Exception as e:
        st.error(f"Erro no Upload: {e}")
        return None
    return None

# =========================================================
# 2) DESIGN DA PROPOSTA (LAYOUTS HTML COMPLETOS)
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
        fotos_html += '<b class="secao-titulo">4. RELATÓRIO FOTOGRÁFICO</b>'
        fotos_html += '<div style="display: flex; flex-wrap: wrap; gap: 2%; margin-top: 15px;">'
        for f in lista_fotos:
            img_src = ""
            if f.get('url_foto') and str(f['url_foto']).startswith("http"):
                img_src = transformar_url_em_base64(f['url_foto'])
            elif 'file' in f:
                try:
                    b64 = base64.b64encode(f['file'].getvalue()).decode()
                    img_src = f"data:image/png;base64,{b64}"
                except: img_src = ""
            
            if img_src:
                fotos_html += f"""
                <div style="width: 48%; margin-bottom:20px; page-break-inside: avoid;">
                    <img src="{img_src}" style="width:100%; height:250px; object-fit: cover; border:1px solid #ddd; border-radius:5px;">
                    <p style="text-align:center; font-size:11px; font-weight:bold; color:#002d5b; margin-top:5px;">{f.get('nome','Item')}</p>
                </div>"""
        fotos_html += '</div>'

    itens_html = "".join([f"<div style='display:flex; justify-content:space-between; border-bottom:1px solid #eee; padding:8px 0; font-size:14px;'><span><b>{i.get('serv','').upper()}</b> (x{i.get('qtd',1)})</span><b>R$ {float(i.get('total',0)):,.2f}</b></div>" for i in lista_itens])

    return f"""
    <html>
    <head>
    <style>
        * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; color: #333; margin: 0; padding: 0; }}
        @media print {{
            .no-print {{ display: none !important; }}
            @page {{ size: A4; margin: 1.5cm; }}
            .capa-container {{ margin: -1.5cm !important; height: 29.7cm; width: 21cm; page-break-after: always; }}
            .conteudo-pagina {{ page-break-before: always; }}
        }}
        .no-print {{ background: #002d5b; color: white; padding: 15px 30px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold; margin: 20px; }}
        .capa-container {{ display: flex; height: 100vh; background: white; border-left: 30px solid #002d5b; }}
        .capa-main {{ flex: 1; padding: 80px 60px; display: flex; flex-direction: column; }}
        .capa-titulo {{ font-size: 50px; color: #002d5b; font-weight: 900; line-height: 1; margin: 40px 0; }}
        .capa-info {{ margin-top: 50px; font-size: 16px; line-height: 2; }}
        .capa-label {{ color: #888; text-transform: uppercase; font-size: 12px; letter-spacing: 1px; display: block; }}
        .capa-valor {{ color: #333; font-size: 18px; margin-bottom: 20px; display: block; }}
        .secao-titulo {{ color:#002d5b; font-size:14px; text-transform: uppercase; margin-top: 25px; display:block; border-bottom: 2px solid #002d5b; padding-bottom:5px; font-weight: bold; }}
        .texto {{ text-align: justify; font-size: 13px; white-space: pre-wrap; margin: 10px 0; line-height: 1.6; color: #444; }}
    </style>
    </head>
    <body>
        <button class="no-print" onclick="window.print()">🖨️ GERAR PDF / IMPRIMIR PROPOSTA</button>
        <div class="capa-container">
            <div class="capa-main">
                <img src="https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix" width="220">
                <h1 class="capa-titulo">PROPOSTA<br>TÉCNICA<br><small style="font-size: 25px;">COMERCIAL</small></h1>
                <div class="capa-info">
                    <span class="capa-label">Cliente</span>
                    <span class="capa-valor"><b>{r_social}</b></span>
                    <span class="capa-label">Empreendimento</span>
                    <span class="capa-valor">{empreend}</span>
                    <span class="capa-label">Referência</span>
                    <span class="capa-valor">ORÇAMENTO #{num_exibicao}</span>
                </div>
                <div style="margin-top: auto; display: flex; justify-content: space-between; align-items: flex-end; border-top: 1px solid #eee; padding-top: 20px;">
                    <div><b style="color:#002d5b;">Rio de Janeiro</b><br>{data_hoje}</div>
                    <div style="text-align: right;"><b>PROFIX</b><br>Gestão de Facilities</div>
                </div>
            </div>
        </div>
        <div class="conteudo-pagina" style="padding: 20px;">
            <table style="width:100%; margin-bottom: 20px;">
                <tr>
                    <td><img src="https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix" width="180"></td>
                    <td style="text-align:right; font-size:10px; color: #666;">
                        <b style="color:#002d5b;">PROFIX GESTÃO DE FACILITIES</b><br>
                        CNPJ: 52.620.102/0001-03<br>
                        Tel: (21) 3609-1314<br>
                        Av. Marechal Câmara, 160, Sala 1107 - Centro, Rio de Janeiro - RJ
                    </td>
                </tr>
            </table>
            <div style="background:#002d5b !important; color:white !important; text-align:center; padding:10px; font-weight:bold;">PROPOSTA TÉCNICA COMERCIAL</div>
            <div style="border:1px solid #ddd; padding:15px; margin: 15px 0; font-size:13px; display:flex; background:#f9f9f9 !important;">
                <div style="flex:1;"><b>CLIENTE:</b> {r_social}<br><b>CNPJ:</b> {cnpj_val}<br><b>EMPREENDIMENTO:</b> {empreend}</div>
                <div style="flex:1; border-left: 1px solid #ddd; padding-left:15px;"><b>REF:</b> {num_exibicao}<br><b>A/C:</b> {cuidados}<br><b>LOCAL:</b> {local if local else "-"}</div>
            </div>
            <b class="secao-titulo">1. METODOLOGIA E ESCOPO TÉCNICO</b><div class="texto">{s1}</div>
            <b class="secao-titulo">2. MATERIAIS INCLUSOS</b><div class="texto">{s2}</div>
            <b class="secao-titulo">3. ATENDIMENTO E SUPORTE</b><div class="texto">{s3}</div>
            {fotos_html}
            <div style="page-break-inside: avoid; margin-top: 30px;">
                <b class="secao-titulo">5. INVESTIMENTO MENSAL / GLOBAL</b>
                <div style="margin: 15px 0;">{itens_html}</div>
                <div style="display: flex; justify-content: flex-end;">
                    <div style="background:#f1f4f9 !important; padding:25px; border-left:8px solid #002d5b !important; text-align:right; width: 300px;">
                        <small style="color:#666;">VALOR TOTAL</small><br>
                        <b style="font-size:28px; color:#002d5b;">R$ {valor_total:,.2f}</b>
                    </div>
                </div>
                <div style="font-size:11px; color:#777; margin-top: 15px; white-space: pre-wrap;">{s4}</div>
            </div>
        </div>
    </body>
    </html>
    """

def montar_layout_simplificado_com_capa(id_orc, r_social, cnpj_val, empreend, lista_itens, lista_fotos, valor_total):
    data_hoje = datetime.now().strftime("%d/%m/%Y")
    ano_atual = datetime.now().year
    num_exibicao = f"{ano_atual}-{str(id_orc).zfill(3)}" if id_orc else "PROVISÓRIO"

    itens_html = "".join([
        f"<tr>"
        f"<td style='padding:12px; border-bottom:1px solid #eee;'><b>{i.get('serv','').upper()}</b></td>"
        f"<td style='padding:12px; border-bottom:1px solid #eee; text-align:center;'>{i.get('qtd',1)}</td>"
        f"<td style='padding:12px; border-bottom:1px solid #eee; text-align:right;'><b>R$ {float(i.get('total',0)):,.2f}</b></td>"
        f"</tr>" 
        for i in lista_itens
    ])

    fotos_html = ""
    if lista_fotos:
        fotos_html = '<div style="margin-top:40px;"><b style="color:#002d5b; border-bottom:2px solid #002d5b; display:block; padding-bottom:5px;">REGISTRO FOTOGRÁFICO</b>'
        fotos_html += '<div style="display:flex; flex-wrap:wrap; gap:15px; margin-top:15px;">'
        for f in lista_fotos:
            img_src = transformar_url_em_base64(f['url_foto']) if f.get('url_foto') else ""
            if img_src:
                fotos_html += f"""
                <div style="width:31%; border:1px solid #ddd; border-radius:4px; padding:5px; page-break-inside: avoid;">
                    <img src="{img_src}" style="width:100%; height:140px; object-fit:cover; border-radius:2px;">
                    <p style="font-size:10px; text-align:center; margin:5px 0; font-weight:bold; color:#002d5b;">{f.get('nome','')}</p>
                </div>"""
        fotos_html += '</div></div>'

    return f"""
    <html>
    <head>
    <style>
        * {{ -webkit-print-color-adjust: exact !important; print-color-adjust: exact !important; }}
        body {{ font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; color: #333; }}
        @media print {{
            .no-print {{ display: none !important; }}
            @page {{ size: A4; margin: 1.5cm; }}
            .capa-container {{ margin: -1.5cm !important; height: 29.7cm; width: 21cm; page-break-after: always; }}
            .conteudo-pagina {{ page-break-before: always; padding: 20px; }}
        }}
        .no-print {{ background: #002d5b; color: white; padding: 15px; border: none; border-radius: 5px; cursor: pointer; margin: 20px; font-weight: bold; }}
        .capa-container {{ display: flex; height: 100vh; background: white; border-left: 30px solid #002d5b; }}
        .capa-main {{ flex: 1; padding: 80px 60px; display: flex; flex-direction: column; }}
        .capa-titulo {{ font-size: 50px; color: #002d5b; font-weight: 900; line-height: 1; margin: 40px 0; }}
        .capa-info {{ margin-top: 50px; font-size: 16px; line-height: 2; }}
        .capa-label {{ color: #888; text-transform: uppercase; font-size: 12px; display: block; }}
        .capa-valor {{ color: #333; font-size: 18px; margin-bottom: 20px; display: block; }}
    </style>
    </head>
    <body>
        <button class="no-print" onclick="window.print()">🖨️ IMPRIMIR ORÇAMENTO SIMPLES</button>
        <div class="capa-container">
            <div class="capa-main">
                <img src="https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix" width="220">
                <h1 class="capa-titulo">ORÇAMENTO<br>DE SERVIÇOS</h1>
                <div class="capa-info">
                    <span class="capa-label">Cliente</span>
                    <span class="capa-valor"><b>{r_social}</b></span>
                    <span class="capa-label">Empreendimento</span>
                    <span class="capa-valor">{empreend}</span>
                    <span class="capa-label">Referência</span>
                    <span class="capa-valor">#{num_exibicao}</span>
                </div>
                <div style="margin-top: auto; display: flex; justify-content: space-between; border-top: 1px solid #eee; padding-top: 20px;">
                    <div><b>Rio de Janeiro</b><br>{data_hoje}</div>
                    <div style="text-align: right;"><b>PROFIX</b></div>
                </div>
            </div>
        </div>
        <div class="conteudo-pagina">
            <table style="width:100%; margin-bottom: 20px;">
                <tr>
                    <td><img src="https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix" width="150"></td>
                    <td style="text-align:right; font-size:10px; color: #666;">
                        <b style="color:#002d5b;">PROFIX GESTÃO DE FACILITIES</b><br>
                        CNPJ: 52.620.102/0001-03<br>
                        Tel: (21) 3609-1314<br>
                        Av. Marechal Câmara, 160, Sala 1107 - Centro, Rio de Janeiro - RJ
                    </td>
                </tr>
            </table>
            <div style="background:#002d5b !important; color:white !important; text-align:center; padding:10px; font-weight:bold;">DEMONSTRATIVO DE CUSTOS</div>
            <table style="width:100%; border-collapse:collapse; margin-top:20px;">
                <thead>
                    <tr style="background:#002d5b !important; color:white !important;">
                        <th style="padding:12px; text-align:left;">DESCRIÇÃO DOS SERVIÇOS / ITENS</th>
                        <th style="padding:12px;">QTD</th>
                        <th style="padding:12px; text-align:right;">TOTAL</th>
                    </tr>
                </thead>
                <tbody>{itens_html}</tbody>
            </table>
            <div style="margin-top:30px; display:flex; justify-content:flex-end;">
                <div style="background:#f1f4f9 !important; padding:20px; border-left:8px solid #002d5b !important; text-align:right; min-width:250px;">
                    <span style="color:#666; font-size:12px;">VALOR TOTAL DO INVESTIMENTO</span><br>
                    <b style="font-size:26px; color:#002d5b;">R$ {valor_total:,.2f}</b>
                </div>
            </div>
            {fotos_html}
            <div style="margin-top:50px; font-size:11px; color:#999; border-top:1px solid #eee; padding-top:10px;">
                <b>NOTAS GERAIS:</b><br>
                1. Validade desta proposta: 10 dias úteis.<br>
                2. Impostos inclusos conforme legislação vigente.<br>
                3. O início dos serviços está condicionado à aprovação formal deste documento.
            </div>
        </div>
    </body>
    </html>
    """
# =========================================================
# 3) INTERFACE PRINCIPAL
# =================================########################

with st.sidebar:
    st.image("https://kelygcjgdbkryfqpqoqe.supabase.co/storage/v1/object/public/fotos_orcamentos/logo_profix", width=180)
    st.title("🛡️ Painel PROFIX")
    
# Criação das abas para organização limpa
tab_nova, tab_lista = st.tabs(["📝 Novo/Editar Orçamento", "📋 Gerenciar Pedidos"])

# --- ABA: GERENCIAR PEDIDOS ---
with tab_lista:
    st.header("Histórico de Orçamentos")
    pedidos = supabase.table("orcamentos").select("*").order("id", desc=True).execute().data
    lista_cli = sorted(list(set([p['cliente_razao_social'] for p in pedidos if p['cliente_razao_social']])))
    filtro = st.selectbox("Filtrar Cliente", ["Todos"] + lista_cli, key="filtro_cli")
    
    for p in pedidos:
        if filtro != "Todos" and p['cliente_razao_social'] != filtro: continue
        with st.expander(f"ID {p['id']} - {p['cliente_razao_social']}"):
            if st.button("📝 Carregar para Edição", key=f"ed_btn_{p['id']}"):
                st.session_state.edit_id = p['id']
                it_db = supabase.table("itens_orcamento").select("*").eq("orcamento_id", p['id']).execute().data
                ft_db = supabase.table("fotos_relatorio").select("*").eq("orcamento_id", p['id']).execute().data
                st.session_state.itens = [{"serv": i['servico'], "qtd": i['quantidade'], "total": i['valor_total']} for i in it_db]
                st.session_state.fotos = [{"url_foto": f['url_foto'], "nome": f['nome_item']} for f in ft_db]
                st.success("Dados carregados! Volte para a aba 'Novo/Editar'.")
                st.rerun()

# --- ABA: NOVO ORÇAMENTO ---
with tab_nova:
    st.header("📑 " + ("Editando Proposta" if st.session_state.edit_id else "Nova Proposta"))
    
    # Busca clientes para preenchimento automático
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

    with st.expander("2. Escopo Técnico (PROFIX)", expanded=True):
        p_esc = esc_db.split("|||")
        # Se for novo ou escopo estiver vazio, carrega o texto padrão completo
        if not st.session_state.edit_id and (len(p_esc) < 2 or p_esc[0].strip() == ""):
            p_esc = [
                """A PROFIX atuará com foco na preservação do padrão estético e na manutenção da integridade das instalações, assegurando que os apartamentos decorados e estandes de vendas mantenham-se em estado de 'novo' e prontos para visitação. Nossa metodologia prioriza a conservação detalhada para que o ambiente reflita fielmente a qualidade do projeto original, compreendendo:

Gestão de Iluminação e Atmosfera (Elétrica): Manutenção contínua de todo o sistema de iluminação decorativa e funcional. Realizamos a substituição imediata de lâmpadas e fitas LED, respeitando rigorosamente a temperatura de cor (quente/fria) e a intensidade original do projeto de interiores, garantindo que o ambiente mantenha a atmosfera planejada pelos arquitetos. Cuidamos da funcionalidade e limpeza de tomadas e interruptores.

Sistemas Hidráulicos e Escoamento: Monitoramento preventivo de todos os pontos de água, incluindo torneiras, misturadores, cubas e sistemas sanitários, eliminando gotejamentos ou irregularidades funcionais. Nossa atuação foca na estanqueidade total, prevenindo umidades que danifiquem o mobiliário. Inclui a limpeza técnica periódica de calhas e tubos de queda, garantindo o escoamento pluvial e protegendo o patrimônio contra infiltrações.

Revitalização de Acabamentos e Revestimentos (Limites Mensais): Intervenções de restauro para correção visual imediata de avarias decorrentes do fluxo de visitação:
• Pintura de Revitalização: Retoques em paredes e tetos (até 4m²);
• Sistemas de Forro: Reparos em gesso acartonado (até 1m²) e placas moduladas (até 2m²);
• Revestimentos e Calafetação: Revisão de rejuntamentos e cerâmicas (até 1m²), além da renovação de silicones;
• Massa e Nivelamento: Recomposição de emboço ou massa (até 5m²);
• Impermeabilização Pontual: Tratamento de áreas localizadas (até 2m²).

Zelo com Marcenaria e Ferragens: Ajuste e preservação de itens de marcenaria e serralheria. Inclui lubrificação e regulagem de dobradiças e corrediças, aperto de puxadores e pequenos reparos de colagem.

Zelo com Inox e Metais: Limpeza técnica e conservação estética de portas de elevadores e marcos metálicos, garantindo a remoção de marcas e a preservação do brilho original dos acabamentos.

Este escopo não contempla: manutenção mecânica/eletrônica de ar-condicionado (apenas filtros e drenos), reposição de vidros/espelhos, manutenção mecânica de elevadores, reformas estruturais, limpeza de fachadas ou reparos em mobiliário solto/decoração.

Objetivo: Manter a infraestrutura operacional e estética em nível de excelência, permitindo que o foco total do visitante esteja na qualidade e nos detalhes do imóvel.""",
                """A PROFIX assume o fornecimento integral de todos os materiais de consumo e peças de reposição necessários para a execução dos serviços descritos nesta proposta. Nossa logística de suprimentos segue critérios rigorosos para garantir a integridade do projeto e a valorização do imóvel:

Critério de Substituição e Fidelidade: Na manutenção de qualquer componente, seguiremos rigorosamente o padrão da peça já instalada no local. A prioridade será total para a mesma marca e referência do projeto original.

Descontinuidade de Mercado: Somente em casos comprovados de descontinuidade, optaremos por uma marca similar de primeira linha (premium).

Padrão de Pintura e Cores: A contratante deverá fornecer as referências e códigos das cores desejadas. Utilizaremos exclusivamente tintas de linha premium.

Critério de Retoque e Pintura Geral: A proposta contempla o retoque pontual. Caso a superfície original não aceite o retoque e demande a pintura integral, a PROFIX enviará previamente uma proposta de valor complementar.

Principais insumos cobertos: Componentes de iluminação LED (lâmpadas, fitas, reatores), dispositivos elétricos (tomadas, interruptores), vedações (silicones, rejuntes), hidráulica (reparos de válvulas, engates) e materiais de acabamento (tinta, massas, lixas, seladores).

Logística: A gestão de compra e entrega dos insumos é de inteira responsabilidade da PROFIX, garantindo agilidade imediata nos reparos.""",
                """Perfil da Equipe: Os serviços são executados por profissionais capacitados para atuar em ambientes de alto padrão. Priorizamos a organização e a limpeza absoluta do local após cada intervenção, preservando a integridade do mobiliário decorativo e a estética do projeto.

Gestão por Relatórios Digitais: Após cada manutenção, será enviado um Relatório Fotográfico detalhado (antes e depois). Este documento garante o controle da construtora sobre a preservação do seu patrimônio e serve como histórico técnico das instalações.

Respeito ao Fluxo de Vendas: As visitas e intervenções serão coordenadas com a administração do estande para não interferir nos horários de maior fluxo de clientes, mantendo o ambiente sempre pronto para recepção.

Compromisso de Agilidade: A PROFIX estabelece o prazo máximo de 48 horas para o atendimento e resolução de chamados após a abertura da solicitação.""",
                """<b>CONDIÇÕES COMERCIAIS</b><br>Vigência do Contrato: 12 (doze) meses, garantindo a manutenção contínua e a preservação do padrão estético do patrimônio durante o ciclo de exposição.

Abrangência: O valor proposto contempla todos os custos diretos e indiretos, incluindo mão de obra especializada, materiais de rotina, encargos trabalhistas, previdenciários, tributos (ISS, PIS, COFINS), seguros e EPIs.

Condição de Pagamento: O faturamento será realizado mensalmente, com vencimento para 30 dias após a emissão da respectiva Nota Fiscal de prestação de serviços.

Serviços Extraordinários: Demandas que excedam os limites de metragem estipulados no item 1, ou intervenções estruturais de grande porte, serão objeto de orçamento complementar para aprovação prévia.

Validade da Proposta: 30 dias."""
            ]

        while len(p_esc) < 4: p_esc.append("")
        t1 = st.text_area("1. Metodologia", value=p_esc[0], height=350)
        t2 = st.text_area("2. Materiais", value=p_esc[1], height=250)
        t3 = st.text_area("3. Atendimento", value=p_esc[2], height=200)
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
            prev = f.get('url_foto') if f.get('url_foto') else f.get('file')
            if prev: cc1.image(prev, width=100)
            f['nome'] = cc2.text_input(f"Legenda {idx}", f['nome'], key=f"f_txt_{idx}")
            if cc3.button("🗑️", key=f"del_f_{idx}"): 
                st.session_state.fotos.pop(idx)
                st.rerun()

        st.divider()
        ci1, ci2, ci3 = st.columns([3, 1, 1])
        it_n, it_q, it_v = ci1.text_input("Serviço"), ci2.number_input("Qtd", 1), ci3.number_input("R$ Unit", 0.0)
        if st.button("➕ Adicionar Item"): 
            st.session_state.itens.append({"serv": it_n, "qtd": it_q, "total": it_q * it_v})
            st.rerun()
            
        for i_idx, it in enumerate(st.session_state.itens):
            c_it1, c_it2, c_it3 = st.columns([4, 1, 0.5])
            c_it1.write(f"**{it['serv']}** (x{it['qtd']})")
            c_it2.write(f"R$ {it['total']:,.2f}")
            if c_it3.button("❌", key=f"del_it_{i_idx}"): 
                st.session_state.itens.pop(i_idx)
                st.rerun()

    total_proposta = sum(i['total'] for i in st.session_state.itens)
    
    if st.button("💾 SALVAR PROPOSTA NO SISTEMA", type="primary", use_container_width=True):
        with st.spinner("Salvando..."):
            payload = {
                "cliente_razao_social": razao, "cliente_cnpj": cnpj_val, 
                "empreendimento": emp_val, "localizacao": loc_val, 
                "aos_cuidados": ac_val, "valor_total": total_proposta, 
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
                st.session_state.edit_id = oid

            for i in st.session_state.itens: 
                supabase.table("itens_orcamento").insert({"orcamento_id": oid, "servico": i['serv'], "quantidade": i['qtd'], "valor_total": i['total']}).execute()
            for f in st.session_state.fotos: 
                url_final = upload_imagem_supabase(f)
                if url_final:
                    supabase.table("fotos_relatorio").insert({"orcamento_id": oid, "nome_item": f['nome'], "url_foto": url_final}).execute()
            st.success("✅ Orçamento salvo com sucesso!")

    st.divider()
    formato = st.radio("Escolha o formato de exibição:", ["Proposta Técnica Completa", "Orçamento Simples (Direto)"], horizontal=True)

    if formato == "Orçamento Simples (Direto)":
        html_final = montar_layout_simplificado_com_capa(st.session_state.edit_id, razao, cnpj_val, emp_val, st.session_state.itens, st.session_state.fotos, total_proposta)
    else:
        html_final = montar_layout_proposta(st.session_state.edit_id, razao, cnpj_val, emp_val, loc_val, ac_val, escopo_final, st.session_state.itens, st.session_state.fotos, total_proposta)

    st.components.v1.html(html_final, height=1200, scrolling=True)
