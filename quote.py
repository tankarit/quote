import re
import streamlit as st
from datetime import datetime, timedelta
from copy import deepcopy

# =========================
# Config da página
# =========================
st.set_page_config(
    page_title="TANKAR IT QUOTE TOOL",
    page_icon="💼",
    layout="centered"
)

APP_NAME = "TANKAR IT QUOTE TOOL"

# =========================
# CSS (tema claro/escuro + padding superior maior p/ não “comer” o título)
# =========================
def inject_theme(dark: bool):
    blue = "#0B3C5D"
    green = "#0B8457"
    bg_light = "#ffffff"
    bg_dark = "#0f1420"
    text_light = "#0B3C5D"
    text_dark = "#e8eef3"
    card_light = "#f9fbfd"
    card_dark = "#151c2b"
    border_light = "#e8eef3"
    border_dark = "#22304a"

    if dark:
        app_bg = bg_dark; text = text_dark; card = card_dark; border = border_dark; hr = "#243251"
    else:
        app_bg = bg_light; text = text_light; card = card_light; border = border_light; hr = "#e6eef5"

    st.markdown(f"""
    <style>
    .stApp {{ background: {app_bg}; }}
    /* Aumenta o padding superior para o título não ficar colado no topo */
    .block-container {{ padding-top: 2.2rem; }}

    .header-band {{
      background: linear-gradient(90deg, {blue}, {green});
      border-radius: 16px; padding: 16px 18px; color: white; margin-bottom: 14px;
      box-shadow: 0 4px 18px rgba(0,0,0,0.15);
    }}
    h1, h2, h3, h4, h5, h6, label, .stMarkdown p {{ color: {text}; }}
    hr {{ border: 0; height: 1px; background: {hr}; margin: 0.8rem 0 1rem; }}
    .card {{
      border: 1px solid {border}; border-radius: 12px; padding: 12px 14px; background: {card};
    }}
    .badge {{
      display: inline-block; padding: 2px 8px; border-radius: 999px;
      background: {blue}; color: #fff; font-size: 12px; font-weight: 600;
    }}
    .stButton>button {{
      background: {green}; color: white; border: 0; border-radius: 10px;
      padding: 0.6rem 1.0rem; font-weight: 600;
      box-shadow: 0 4px 12px rgba(11,132,87,0.25); transition: all .15s ease;
    }}
    .stButton>button:hover {{ filter: brightness(1.05); transform: translateY(-1px); }}
    </style>
    """, unsafe_allow_html=True)

# Sidebar: apenas tema e totais financeiros (sem logo, sem PDF)
with st.sidebar:
    st.markdown("### Aparência")
    tema = st.radio("Tema", options=["Claro", "Escuro"], index=1, horizontal=True)
    inject_theme(dark=(tema == "Escuro"))

    st.markdown("---")
    st.markdown("### Opções financeiras (opcional)")
    # estados serão inicializados em init_state()

# =========================
# Constantes de preço
# =========================
HORA_CONSULTORIA = 200.0
HORA_DESIGN = 200.0

# Implementação/Melhoria Wireless
IMPL_ANALISE_FIXA = 2280.0
IMPL_HORA_ADICIONAL = 220.0

# Wireless Survey
WS_ANALISE_FIXA = 3000.0
WS_ADD_POR_ANDAR = 1000.0
WS_ACIMA_10_ANDARES = 20000.0
WS_METRAGENS = {
    "50–200 m² (+R$ 2.000)": 2000.0,
    "200–300 m² (+R$ 3.500)": 3500.0,
    "300–500 m² (+R$ 5.000)": 5000.0,
    "Acima de 600 m² (+R$ 10.000)": 10000.0,
}

# Design (Wireless/Cabeada/Híbrida)
DESIGN_ANALISE_FIXA = 2500.0

# Gestão Industrial (por faixa de funcionários)
GI_FAIXAS = [
    (1, 100, 4899.0),
    (101, 200, 6899.0),
    (201, 10**9, 8899.0),  # acima de 200
]

CURSOS_OPCOES = [
    "Curso de gerenciamento de rede interna",
    "Curso de gestão de redes Wireless e identificação de problemas",
    "Consulte engenharia",
]

# =========================
# Estado & Helpers
# =========================
def init_state():
    st.session_state.setdefault("itens", [])
    st.session_state.setdefault("observacoes_finais", "")
    # Financeiro
    st.session_state.setdefault("finance_despesas", 0.0)
    st.session_state.setdefault("finance_impostos", 0.0)  # %
    st.session_state.setdefault("finance_margem", 0.0)    # %
    # Cabeçalho do orçamento
    st.session_state.setdefault("cliente_nome", "")
    st.session_state.setdefault("cliente_contato", "")
    st.session_state.setdefault("validade_dias", 7)
    st.session_state.setdefault("consultor_nome", "")

init_state()

def format_brl(valor: float) -> str:
    # Usa apenas dígitos, vírgula e ponto simples para evitar caracteres estranhos
    s = f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def agora_br():
    return datetime.now().strftime("%d/%m/%Y %H:%M")

def data_validade_str(dias: int) -> str:
    dt = datetime.now() + timedelta(days=max(1, int(dias)))
    return dt.strftime("%d/%m/%Y")

def add_item(item: dict):
    st.session_state.itens.append(item)

def delete_item(idx: int):
    if 0 <= idx < len(st.session_state.itens):
        st.session_state.itens.pop(idx)

def duplicate_item(idx: int):
    if 0 <= idx < len(st.session_state.itens):
        st.session_state.itens.append(deepcopy(st.session_state.itens[idx]))

def total_itens():
    return sum(i["subtotal"] for i in st.session_state.itens)

def total_com_financeiros():
    subtotal = total_itens()
    despesas = float(st.session_state.finance_despesas) or 0.0
    impostos_pct = float(st.session_state.finance_impostos) or 0.0
    margem_pct = float(st.session_state.finance_margem) or 0.0

    base_impostos = subtotal + despesas
    impostos = base_impostos * (impostos_pct / 100.0)
    base_margem = subtotal + despesas + impostos
    margem = base_margem * (margem_pct / 100.0)
    total = subtotal + despesas + impostos + margem
    return {
        "subtotal": subtotal,
        "despesas": despesas,
        "impostos_pct": impostos_pct,
        "impostos_valor": impostos,
        "margem_pct": margem_pct,
        "margem_valor": margem,
        "total": total,
    }

def gerar_txt_final():
    linhas = [
        f"{APP_NAME}",
        f"Data/Hora: {agora_br()}",
        "-"*70,
        f"Cliente: {st.session_state.cliente_nome or '(não informado)'}",
        f"Contato: {st.session_state.cliente_contato or '(não informado)'}",
        f"Consultor Tankar: {st.session_state.consultor_nome or '(não informado)'}",
        f"Validade: {st.session_state.validade_dias} dias (até {data_validade_str(st.session_state.validade_dias)})",
        "-"*70
    ]
    for idx, it in enumerate(st.session_state.itens, 1):
        linhas += [
            f"Item {idx}: {it['servico']}",
            f"Descrição/Resumo: {it.get('descricao','-')}",
            f"Detalhes: {it.get('detalhes','-')}",
            f"Subtotal: {format_brl(it['subtotal'])}",
            "-"*70
        ]
    fin = total_com_financeiros()
    linhas += [
        "Informações gerais do orçamento:",
        st.session_state.observacoes_finais.strip() or "(sem observações)",
        "-"*70,
        f"SUBTOTAL ITENS: {format_brl(fin['subtotal'])}",
        f"DESPESAS: {format_brl(fin['despesas'])}",
        f"IMPOSTOS ({fin['impostos_pct']}%): {format_brl(fin['impostos_valor'])}",
        f"MARGEM ({fin['margem_pct']}%): {format_brl(fin['margem_valor'])}",
        f"TOTAL GERAL: {format_brl(fin['total'])}",
        "",
        "Observações:",
        "- Itens com 'sob consulta' poderão sofrer alteração após análise técnica.",
        "- Custos de transporte, quando aplicáveis, foram somados em 'Despesas' ou serão calculados separadamente.",
        "- Validade conforme indicada acima."
    ]
    return "\n".join(linhas)

# =========================
# Cabeçalho visual
# =========================
st.markdown(
    '<div class="header-band"><h2 style="margin:0;">TANKAR IT QUOTE TOOL</h2>'
    '<div class="badge">Orçamentos Multisserviço</div></div>',
    unsafe_allow_html=True
)
st.caption("Preencha os dados do orçamento, inclua os itens (um por vez) e exporte para TXT.")

# =========================
# 0) Dados do Orçamento
# =========================
st.markdown("### 0) Dados do Orçamento")
c1, c2 = st.columns([1,1])
with c1:
    st.session_state.cliente_nome = st.text_input("Nome do cliente*", value=st.session_state.cliente_nome)
    st.session_state.validade_dias = st.number_input(
        "Validade do orçamento (dias)*", min_value=1, step=1, value=int(st.session_state.validade_dias)
    )
with c2:
    st.session_state.cliente_contato = st.text_input("Contato (email/telefone)", value=st.session_state.cliente_contato)
    st.session_state.consultor_nome = st.text_input("Consultor Tankar*", value=st.session_state.consultor_nome)

st.markdown("<hr>", unsafe_allow_html=True)

# =========================
# 1) Escolha de Serviço
# =========================
SERVICOS = [
    "— Selecione —",
    "Consultoria em Infraestrutura / Redes / Melhorias e Suporte",
    "Implementação ou Melhoria de Rede Wireless",
    "Wireless Survey",
    "Design de Rede (Wireless/Cabeada/Híbrida)",
    "Gestão Industrial",
    "Cursos e Treinamentos",
    "Venda de Equipamentos",
]
st.markdown("### 1) Escolha o serviço")
servico = st.selectbox("Serviço:", options=SERVICOS, index=0)
st.markdown("<hr>", unsafe_allow_html=True)

# =========================
# 2) Formulários por Serviço
# =========================
if servico == "Consultoria em Infraestrutura / Redes / Melhorias e Suporte":
    st.subheader("Consultoria (R$ 200/h)")
    resumo = st.text_area("Resuma a solicitação do cliente (até 500 caracteres)", max_chars=500, height=120)
    horas = st.number_input("Horas necessárias", min_value=1, step=1, value=4, help="Valor/hora fixo em R$ 200")
    pretende_equip = st.radio("O cliente pretende adquirir equipamentos?", ["Não", "Sim"], horizontal=True) == "Sim"
    equip_sel = []
    if pretende_equip:
        equip_sel = st.multiselect(
            "Selecione os equipamentos de interesse (uma ou mais opções)",
            options=[
                "Access Points",
                "Computadores / Laptops Lenovo",
                "Servidores",
                "Câmeras de segurança",
            ]
        )
    subtotal = float(horas) * HORA_CONSULTORIA

    st.markdown("#### Resumo (parcial)")
    st.markdown(f"- Horas: **{horas} h** × {format_brl(HORA_CONSULTORIA)} = **{format_brl(subtotal)}**")
    st.markdown(f"- Interesse em equipamentos: **{'Sim' if pretende_equip else 'Não'}**")
    if pretende_equip and equip_sel:
        st.markdown(f"- Equipamentos: {', '.join(equip_sel)}")

    if st.button("➕ Incluir item"):
        if not resumo.strip():
            st.warning("Informe o **resumo** antes de incluir.")
        else:
            detalhes = f"Horas: {horas} × {format_brl(HORA_CONSULTORIA)}"
            if pretende_equip:
                eq = ", ".join(equip_sel) if equip_sel else "(não especificado)"
                detalhes += f" | Interesse em equipamentos: {eq}"
            add_item({
                "servico": servico,
                "descricao": resumo.strip(),
                "detalhes": detalhes,
                "subtotal": subtotal
            })
            st.success("Item adicionado ao orçamento!")

elif servico == "Implementação ou Melhoria de Rede Wireless":
    st.subheader("Implementação/Melhoria de Rede Wireless")
    st.markdown(
        f'<div class="card">Análise inicial obrigatória: <b>{format_brl(IMPL_ANALISE_FIXA)}</b>. '
        f'Horas adicionais a <b>{format_brl(IMPL_HORA_ADICIONAL)}</b>. '
        f'<br/><i>Custos de transporte serão calculados separadamente.</i></div>',
        unsafe_allow_html=True
    )
    horas_adic = st.number_input("Horas adicionais", min_value=0, step=1, value=0)
    resumo = st.text_area("Descreva a necessidade do cliente (até 500 caracteres)", max_chars=500, height=120)
    subtotal = IMPL_ANALISE_FIXA + horas_adic * IMPL_HORA_ADICIONAL

    st.markdown("#### Resumo (parcial)")
    st.markdown(f"- Análise inicial: **{format_brl(IMPL_ANALISE_FIXA)}**")
    st.markdown(f"- Horas adicionais: **{horas_adic} h × {format_brl(IMPL_HORA_ADICIONAL)}**")
    st.markdown(f"- Subtotal: **{format_brl(subtotal)}**")
    st.caption("Custos de transporte serão calculados separadamente.")

    if st.button("➕ Incluir item"):
        if not resumo.strip():
            st.warning("Informe a **descrição/resumo** antes de incluir.")
        else:
            detalhes = (
                f"Análise inicial {format_brl(IMPL_ANALISE_FIXA)} | "
                f"Horas adic.: {horas_adic} × {format_brl(IMPL_HORA_ADICIONAL)} | "
                "Transporte separado"
            )
            add_item({
                "servico": servico,
                "descricao": resumo.strip(),
                "detalhes": detalhes,
                "subtotal": subtotal
            })
            st.success("Item adicionado ao orçamento!")

elif servico == "Wireless Survey":
    st.subheader("Wireless Survey")
    st.markdown(
        f'<div class="card">Base: <b>{format_brl(WS_ANALISE_FIXA)}</b>. '
        f'Para prédios, some <b>{format_brl(WS_ADD_POR_ANDAR)}/andar</b> (1–10 andares) '
        f'ou <b>{format_brl(WS_ACIMA_10_ANDARES)}</b> para mais de 10 andares. '
        f'Metragem por andar também soma por andar.</div>',
        unsafe_allow_html=True
    )
    col_a, col_b = st.columns(2)
    with col_a:
        andar_op = st.selectbox("Andares", options=[str(n) for n in range(1, 11)] + ["Acima de 10"])
    with col_b:
        metragem_op = st.selectbox("Metragem por andar (faixa)", options=list(WS_METRAGENS.keys()))

    if andar_op == "Acima de 10":
        qtd_andares = st.number_input("Quantidade de andares (≥ 11)", min_value=11, step=1, value=11)
        custo_andares = WS_ACIMA_10_ANDARES
    else:
        qtd_andares = int(andar_op)
        custo_andares = qtd_andares * WS_ADD_POR_ANDAR

    custo_metragem_por_andar = WS_METRAGENS[metragem_op]
    custo_metragem_total = qtd_andares * custo_metragem_por_andar

    resumo = st.text_area("Observações / escopo do survey (até 500 caracteres)", max_chars=500, height=120)
    subtotal = WS_ANALISE_FIXA + custo_andares + custo_metragem_total

    st.markdown("#### Resumo (parcial)")
    st.markdown(f"- Análise inicial: **{format_brl(WS_ANALISE_FIXA)}**")
    if andar_op == "Acima de 10":
        st.markdown(f"- Andares: **{qtd_andares}** → **{format_brl(WS_ACIMA_10_ANDARES)}**")
    else:
        st.markdown(f"- Andares: **{qtd_andares} × {format_brl(WS_ADD_POR_ANDAR)} = {format_brl(custo_andares)}**")
    st.markdown(
        f"- Metragem por andar: **{metragem_op}** → "
        f"**{qtd_andares} × {format_brl(custo_metragem_por_andar)} = {format_brl(custo_metragem_total)}**"
    )
    st.markdown(f"- Subtotal: **{format_brl(subtotal)}**")

    if st.button("➕ Incluir item"):
        if qtd_andares <= 0:
            st.warning("Informe um número válido de andares.")
        else:
            detalhes = [
                f"Análise inicial {format_brl(WS_ANALISE_FIXA)}",
                (f"Andares: {qtd_andares} (faixa >10) = {format_brl(WS_ACIMA_10_ANDARES)}"
                 if andar_op == "Acima de 10" else
                 f"Andares: {qtd_andares} × {format_brl(WS_ADD_POR_ANDAR)} = {format_brl(custo_andares)}"),
                f"Metragem: {metragem_op} × {qtd_andares} = {format_brl(custo_metragem_total)}",
            ]
            add_item({
                "servico": servico,
                "descricao": (resumo or "").strip(),
                "detalhes": " | ".join(detalhes),
                "subtotal": subtotal
            })
            st.success("Item adicionado ao orçamento!")

elif servico == "Design de Rede (Wireless/Cabeada/Híbrida)":
    st.subheader("Design de Rede")
    tipo = st.radio("Tipo de rede", options=["Wireless", "Cabeada", "Híbrida"], horizontal=True)
    horas = st.number_input("Horas de projeto", min_value=1, step=1, value=8, help=f"R$ {HORA_DESIGN:.0f}/hora")
    descricao = st.text_area("Descrição / Solicitação do cliente (até 500 caracteres)", max_chars=500, height=120)
    subtotal = DESIGN_ANALISE_FIXA + horas * HORA_DESIGN

    st.markdown("#### Resumo (parcial)")
    st.markdown(f"- Análise inicial c/ relatório: **{format_brl(DESIGN_ANALISE_FIXA)}**")
    st.markdown(f"- Horas: **{horas} × {format_brl(HORA_DESIGN)} = {format_brl(horas * HORA_DESIGN)}**")
    st.markdown(f"- Subtotal: **{format_brl(subtotal)}**")

    if st.button("➕ Incluir item"):
        if not descricao.strip():
            st.warning("Descreva a solicitação do cliente antes de incluir.")
        else:
            detalhes = (
                f"Tipo: {tipo} | Análise inicial {format_brl(DESIGN_ANALISE_FIXA)} | "
                f"Horas: {horas} × {format_brl(HORA_DESIGN)}"
            )
            add_item({
                "servico": f"{servico} — {tipo}",
                "descricao": descricao.strip(),
                "detalhes": detalhes,
                "subtotal": subtotal
            })
            st.success("Item adicionado ao orçamento!")

elif servico == "Gestão Industrial":
    st.subheader("Consultoria em Gestão Industrial")
    servicos_gi = st.multiselect(
        "Selecione os serviços (pode escolher mais de um)",
        options=[
            "Gestão de estoques e PCP",
            "Otimização de processos",
            "Redução de custos",
            "Supply Chain e Vendas",
            "Criação de dashboard e indicadores",
            "Treinamentos (IE & ESG)",
        ]
    )
    num_func = st.number_input("Número de funcionários", min_value=1, step=1, value=50)
    resumo = st.text_area("Resumo da solicitação (até 500 caracteres)", max_chars=500, height=120)

    preco_base = None
    for ini, fim, preco in GI_FAIXAS:
        if ini <= num_func <= fim:
            preco_base = preco
            break
    if preco_base is None:
        preco_base = GI_FAIXAS[-1][2]

    st.markdown("#### Resumo (parcial)")
    st.markdown(f"- Serviços selecionados: {', '.join(servicos_gi) if servicos_gi else '(nenhum)'}")
    st.markdown(f"- Funcionários: **{num_func}** → **{format_brl(preco_base)}**")

    if st.button("➕ Incluir item"):
        if not resumo.strip():
            st.warning("Resuma a solicitação antes de incluir.")
        else:
            detalhes = f"Serviços: {', '.join(servicos_gi) if servicos_gi else '(não especificado)'} | Funcionários: {num_func}"
            add_item({
                "servico": servico,
                "descricao": resumo.strip(),
                "detalhes": detalhes,
                "subtotal": preco_base
            })
            st.success("Item adicionado ao orçamento!")

elif servico == "Cursos e Treinamentos":
    st.subheader("Cursos e Treinamentos")
    curso = st.selectbox("Selecione o curso", options=CURSOS_OPCOES, index=0)
    obs = st.text_area("Observações/escopo (opcional, até 500 caracteres)", max_chars=500, height=100)
    st.caption("⚠️ Valores não definidos — itens ficam **sob consulta**.")
    subtotal = 0.0
    if st.button("➕ Incluir item"):
        add_item({
            "servico": servico,
            "descricao": (obs or "").strip(),
            "detalhes": f"Curso: {curso} | Preço: sob consulta",
            "subtotal": subtotal
        })
        st.success("Item adicionado (sob consulta).")

elif servico == "Venda de Equipamentos":
    st.subheader("Venda de Equipamentos")
    st.info("Venda de equipamento — Anexar orçamento parceiro Lenovo.")
    if st.button("➕ Incluir item"):
        add_item({
            "servico": servico,
            "descricao": "Venda de equipamento — anexar orçamento parceiro Lenovo.",
            "detalhes": "Item sem valor neste documento (apenas referência).",
            "subtotal": 0.0
        })
        st.success("Item adicionado ao orçamento!")

# =========================
# 3) Itens adicionados
# =========================
st.markdown("### 2) Itens do orçamento")
if not st.session_state.itens:
    st.info("Nenhum item adicionado ainda. Selecione um serviço acima e clique em **Incluir item**.")
else:
    for i, it in enumerate(st.session_state.itens):
        with st.expander(f"Item {i+1}: {it['servico']} — {format_brl(it['subtotal'])}", expanded=False):
            st.markdown(f"**Descrição/Resumo:** {it.get('descricao','-') or '-'}")
            st.markdown(f"**Detalhes:** {it.get('detalhes','-')}")
            st.markdown(f"**Subtotal:** {format_brl(it['subtotal'])}")
            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"📄 Duplicar item {i+1}", key=f"dup_{i}"):
                    duplicate_item(i)
                    st.rerun()
            with c2:
                if st.button(f"🗑️ Excluir item {i+1}", key=f"del_{i}"):
                    delete_item(i)
                    st.rerun()

    colA, colB = st.columns([1,1])
    with colA:
        st.markdown(f"#### SUBTOTAL ITENS: {format_brl(total_itens())}")
    with colB:
        if st.button("🧹 Limpar todos os itens"):
            st.session_state.itens = []
            st.rerun()

# =========================
# 4) Observações + Finanças + Exportar TXT
# =========================
st.markdown("### 3) Informações gerais (até 1000 caracteres)")
st.session_state.observacoes_finais = st.text_area(
    "Inclua informações e condições gerais da solicitação:",
    value=st.session_state.observacoes_finais,
    max_chars=1000,
    height=140
)

# Financeiro na lateral
with st.sidebar:
    st.session_state.finance_despesas = st.number_input(
        "Despesas (R$) — viagens, hospedagem etc.",
        min_value=0.0, step=100.0, value=float(st.session_state.finance_despesas)
    )
    st.session_state.finance_impostos = st.number_input(
        "Impostos (%) — aplicados sobre Subtotal + Despesas",
        min_value=0.0, step=0.5, value=float(st.session_state.finance_impostos)
    )
    st.session_state.finance_margem = st.number_input(
        "Margem/Markup (%) — aplicada após impostos",
        min_value=0.0, step=0.5, value=float(st.session_state.finance_margem)
    )

# Resumo financeiro no corpo — com TOTAL GERAL simples (ASCII)
st.markdown("### 4) Resumo financeiro")
fin = total_com_financeiros()
st.markdown(f"- Subtotal itens: **{format_brl(fin['subtotal'])}**")
st.markdown(f"- Despesas: **{format_brl(fin['despesas'])}**")
st.markdown(f"- Impostos ({fin['impostos_pct']}%): **{format_brl(fin['impostos_valor'])}**")
st.markdown(f"- Margem/Markup ({fin['margem_pct']}%): **{format_brl(fin['margem_valor'])}**")
st.subheader(f"TOTAL GERAL: {format_brl(fin['total'])}")

# Exportação TXT
st.markdown("### 5) Exportar orçamento (TXT)")
tem_itens = len(st.session_state.itens) > 0
dados_ok = bool(st.session_state.cliente_nome.strip()) and bool(st.session_state.consultor_nome.strip())
if not tem_itens:
    st.info("Adicione pelo menos **um item** para habilitar a exportação.")
elif not dados_ok:
    st.info("Preencha **Nome do cliente** e **Consultor Tankar** para habilitar a exportação.")
else:
    txt_content = gerar_txt_final()
    st.download_button(
        label="📄 Baixar .TXT",
        file_name=f"orcamento_TANKAR_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
        mime="text/plain",
        data=txt_content.encode("utf-8")
    )
