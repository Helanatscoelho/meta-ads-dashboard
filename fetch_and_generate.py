#!/usr/bin/env python3
"""
Meta Ads Weekly Dashboard Generator
Gera relatório semanal automaticamente toda segunda-feira
"""

import urllib.request
import urllib.parse
import json
import os
import sys
from datetime import datetime, timedelta

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

ACCESS_TOKEN = os.environ.get("META_ACCESS_TOKEN", "")
if not ACCESS_TOKEN:
    print("ERRO: META_ACCESS_TOKEN não configurado. Crie um arquivo .env ou defina a variável de ambiente.")
    sys.exit(1)

ACCOUNTS = [
    {"id": "act_101403706860167", "name": "Perfiletto"},
    {"id": "act_267770730525130", "name": "Helena Coelho"},
    {"id": "act_2410626089217011", "name": "Conta 2410"},
    {"id": "act_1182499605271369", "name": "MM Protege"},
    {"id": "act_655917871724513", "name": "Ergy Diesel"},
    {"id": "act_196598645524416", "name": "Marcelo Costa"},
    {"id": "act_297842908343350", "name": "Centro do Sorriso Arapongas"},
    {"id": "act_404664394554450", "name": "Saniteck"},
    {"id": "act_558494692916247", "name": "Lady Livretos"},
    {"id": "act_839314777805875", "name": "Centro do Sorriso Campo Mourão"},
    {"id": "act_1047813853024474", "name": "Cheflera"},
    {"id": "act_1559065974904383", "name": "Clínica Moliah"},
    {"id": "act_985077316316981", "name": "Arezzo"},
    {"id": "act_1463630264317907", "name": "Ana Capri"},
    {"id": "act_1648225505751115", "name": "Comunidade Trindade Santa"},
    {"id": "act_864538029208474", "name": "Monique"},
    {"id": "act_557811123855687", "name": "Loja Trindade Santa"},
    {"id": "act_2029226410831026", "name": "CA - Helena"},
    {"id": "act_1205207067848409", "name": "Centro do Sorriso Rolândia"},
    {"id": "act_1303967340832416", "name": "Odonto Bless Londrina"},
    {"id": "act_668541309479669", "name": "Castro e Figueira"},
    {"id": "act_1908379856581665", "name": "Carol Meirelles"},
    {"id": "act_1575227266844090", "name": "Vedoi"},
    {"id": "act_877477095207362", "name": "Star Veículos"},
]


def fetch_account_insights(account_id, date_start, date_end):
    fields = "spend,impressions,clicks,ctr,cpm,cpc,actions,cost_per_action_type,reach"
    params = {
        "fields": fields,
        "time_range": json.dumps({"since": date_start, "until": date_end}),
        "level": "account",
        "access_token": ACCESS_TOKEN,
    }
    url = f"https://graph.facebook.com/v19.0/{account_id}/insights?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        return {"error": str(e), "data": []}


def fetch_campaigns(account_id, date_start, date_end):
    fields = "name,status,objective,spend,impressions,clicks,ctr,cpc,actions,cost_per_action_type"
    params = {
        "fields": fields,
        "time_range": json.dumps({"since": date_start, "until": date_end}),
        "level": "campaign",
        "access_token": ACCESS_TOKEN,
    }
    url = f"https://graph.facebook.com/v19.0/{account_id}/insights?" + urllib.parse.urlencode(params)
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read().decode())
    except Exception:
        return {"data": []}


def get_action_value(actions, action_type):
    if not actions:
        return 0
    for a in actions:
        if a.get("action_type") == action_type:
            return float(a.get("value", 0))
    return 0


def get_cost_value(costs, action_type):
    if not costs:
        return 0
    for c in costs:
        if c.get("action_type") == action_type:
            return float(c.get("value", 0))
    return 0


def fmt_brl(value):
    if value == 0:
        return "R$ 0,00"
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def fmt_num(value):
    if value == 0:
        return "0"
    return f"{int(value):,}".replace(",", ".")


def fmt_pct(value):
    return f"{float(value):.2f}%"


def analyze_account(account, data, campaigns_data):
    insights = data.get("data", [{}])
    d = insights[0] if insights else {}

    spend = float(d.get("spend", 0))
    impressions = int(d.get("impressions", 0))
    clicks = int(d.get("clicks", 0))
    ctr = float(d.get("ctr", 0))
    cpm = float(d.get("cpm", 0))
    cpc = float(d.get("cpc", 0))
    reach = int(d.get("reach", 0))

    actions = d.get("actions", [])
    costs = d.get("cost_per_action_type", [])

    leads = max(
        get_action_value(actions, "lead"),
        get_action_value(actions, "offsite_conversion.fb_pixel_lead"),
        get_action_value(actions, "onsite_conversion.lead_grouped"),
    )
    messages = get_action_value(actions, "onsite_conversion.messaging_conversation_started_7d")
    total_leads = int(leads + messages)

    cost_per_lead = 0
    if total_leads > 0:
        cost_per_lead = spend / total_leads

    # Campaign analysis
    campaigns = campaigns_data.get("data", [])
    low_perf_campaigns = []
    suggested_campaigns = []

    for c in campaigns:
        c_spend = float(c.get("spend", 0))
        c_clicks = int(c.get("clicks", 0))
        c_impressions = int(c.get("impressions", 0))
        c_name = c.get("campaign_name") or c.get("name", "")
        c_ctr = float(c.get("ctr", 0))

        if c_spend > 50 and c_clicks == 0:
            low_perf_campaigns.append({"name": c_name, "spend": c_spend, "reason": "Gasto sem cliques"})
        elif c_impressions > 5000 and c_ctr < 0.5:
            low_perf_campaigns.append({"name": c_name, "spend": c_spend, "reason": f"CTR muito baixo ({c_ctr:.2f}%)"})

    return {
        "name": account["name"],
        "spend": spend,
        "impressions": impressions,
        "clicks": clicks,
        "ctr": ctr,
        "cpm": cpm,
        "cpc": cpc,
        "reach": reach,
        "leads": total_leads,
        "cost_per_lead": cost_per_lead,
        "messages": int(messages),
        "raw_leads": int(leads),
        "campaigns": campaigns,
        "low_perf_campaigns": low_perf_campaigns,
        "has_data": spend > 0 or impressions > 0,
    }


def generate_suggestions(acc):
    suggestions = []

    if acc["spend"] == 0:
        return ["⚠️ Conta sem investimento no período — verificar se campanhas estão ativas."]

    if acc["ctr"] > 0 and acc["ctr"] < 0.8:
        suggestions.append("📌 CTR abaixo de 0,8% — testar novos criativos (imagens/vídeos) para melhorar engajamento.")

    if acc["cpm"] > 30:
        suggestions.append("📌 CPM elevado (>R$30) — revisar segmentação de público para reduzir custo por mil impressões.")

    if acc["cpc"] > 5:
        suggestions.append("📌 CPC alto — otimizar landing page e CTA dos anúncios para aumentar taxa de conversão.")

    if acc["cost_per_lead"] > 80 and acc["leads"] > 0:
        suggestions.append(f"📌 Custo por lead elevado (R${acc['cost_per_lead']:.0f}) — revisar funil e qualidade do público-alvo.")

    if acc["leads"] == 0 and acc["spend"] > 100:
        suggestions.append("🚨 Nenhum lead gerado com investimento significativo — revisar objetivo das campanhas e formulários de captação.")

    if acc["ctr"] > 2:
        suggestions.append("✅ CTR excelente — escalar orçamento nesta conta/campanha para maximizar resultados.")

    if acc["cost_per_lead"] > 0 and acc["cost_per_lead"] < 30:
        suggestions.append("✅ Custo por lead eficiente — considerar aumentar o orçamento para escalar a captação.")

    if acc["messages"] > 0 and acc["raw_leads"] == 0:
        suggestions.append("💡 Conversões via mensagens detectadas — criar campanha específica de WhatsApp/Messenger para otimizar esse canal.")

    if acc["impressions"] > 100000 and acc["clicks"] < 500:
        suggestions.append("💡 Alto alcance mas poucos cliques — audiência ampla demais. Refinar segmentação por interesse e comportamento.")

    # Campaign suggestions
    for c in acc["low_perf_campaigns"]:
        suggestions.append(f"🔴 Pausar campanha '{c['name'][:50]}' — {c['reason']} (R${c['spend']:.0f} investidos).")

    if not suggestions:
        suggestions.append("✅ Conta com desempenho estável no período. Manter estratégia atual e monitorar semanalmente.")

    return suggestions


def generate_new_campaign_ideas(acc):
    ideas = []

    if acc["messages"] > 20:
        ideas.append("📲 Campanha de Mensagens Avançada — criar fluxo automatizado no WhatsApp para nurturing de leads.")

    if acc["spend"] > 500 and acc["leads"] > 10:
        ideas.append("🎯 Campanha de Retargeting — criar público personalizado de visitantes/engajadores para remarketing.")

    if acc["impressions"] > 50000:
        ideas.append("👥 Lookalike Audience — criar público semelhante baseado nos melhores leads convertidos.")

    if acc["ctr"] > 1.5:
        ideas.append("🚀 Campanha de Conversão Otimizada — duplicar conjunto de anúncios com melhor CTR e aumentar orçamento.")

    if acc["spend"] > 0 and len(ideas) == 0:
        ideas.append("🧪 Teste A/B de Criativos — criar 3 variações de anúncio para identificar melhor performance.")

    return ideas


def generate_html(accounts_data, date_start, date_end):
    date_start_fmt = datetime.strptime(date_start, "%Y-%m-%d").strftime("%d/%m/%Y")
    date_end_fmt = datetime.strptime(date_end, "%Y-%m-%d").strftime("%d/%m/%Y")
    generated_at = datetime.now().strftime("%d/%m/%Y às %H:%M")

    total_spend = sum(a["spend"] for a in accounts_data)
    total_impressions = sum(a["impressions"] for a in accounts_data)
    total_clicks = sum(a["clicks"] for a in accounts_data)
    total_leads = sum(a["leads"] for a in accounts_data)
    active_accounts = sum(1 for a in accounts_data if a["has_data"])
    avg_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
    avg_cpl = (total_spend / total_leads) if total_leads > 0 else 0

    cards_html = ""
    for acc in accounts_data:
        suggestions = generate_suggestions(acc)
        new_campaigns = generate_new_campaign_ideas(acc)
        low_perf = acc["low_perf_campaigns"]

        if not acc["has_data"]:
            status_badge = '<span class="badge badge-inactive">Sem dados</span>'
            status_class = "card-inactive"
        elif acc["ctr"] > 1.5 and acc["cost_per_lead"] < 50 and acc["leads"] > 0:
            status_badge = '<span class="badge badge-good">Performance Boa</span>'
            status_class = "card-good"
        elif acc["ctr"] < 0.5 or acc["cost_per_lead"] > 80:
            status_badge = '<span class="badge badge-bad">Atenção</span>'
            status_class = "card-bad"
        else:
            status_badge = '<span class="badge badge-ok">Normal</span>'
            status_class = "card-ok"

        suggestions_html = "".join(f"<li>{s}</li>" for s in suggestions)
        new_camp_html = "".join(f"<li>{c}</li>" for c in new_campaigns)
        low_perf_html = ""
        if low_perf:
            items = "".join(f"<li>🔴 <strong>{c['name'][:60]}</strong> — {c['reason']}</li>" for c in low_perf)
            low_perf_html = f"""
            <div class="section-block warning-block">
                <h4>🔴 Campanhas para Pausar/Revisar</h4>
                <ul>{items}</ul>
            </div>"""

        cards_html += f"""
        <div class="client-card {status_class}">
            <div class="card-header">
                <div class="client-info">
                    <div class="client-avatar">{acc['name'][0].upper()}</div>
                    <div>
                        <h3>{acc['name']}</h3>
                        <span class="period-label">📅 {date_start_fmt} → {date_end_fmt}</span>
                    </div>
                </div>
                {status_badge}
            </div>

            <div class="metrics-grid">
                <div class="metric-block meta-color">
                    <div class="metric-section-title">💰 META ADS</div>
                    <div class="metric-row">
                        <span class="metric-label">Investimento</span>
                        <span class="metric-value highlight">{fmt_brl(acc['spend'])}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Impressões</span>
                        <span class="metric-value">{fmt_num(acc['impressions'])}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Cliques</span>
                        <span class="metric-value">{fmt_num(acc['clicks'])}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Conversas Iniciadas</span>
                        <span class="metric-value">{fmt_num(acc['messages'])}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">CTR</span>
                        <span class="metric-value {'ctr-good' if acc['ctr'] > 1.5 else 'ctr-bad' if acc['ctr'] < 0.5 and acc['ctr'] > 0 else ''}">{fmt_pct(acc['ctr'])}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Custo por Mil (CPM)</span>
                        <span class="metric-value">{fmt_brl(acc['cpm'])}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Custo por Clique</span>
                        <span class="metric-value">{fmt_brl(acc['cpc'])}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Todos os Leads</span>
                        <span class="metric-value highlight">{fmt_num(acc['leads'])}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Custo por Lead</span>
                        <span class="metric-value {'cpl-good' if 0 < acc['cost_per_lead'] < 50 else 'cpl-bad' if acc['cost_per_lead'] > 80 else ''}">{fmt_brl(acc['cost_per_lead'])}</span>
                    </div>
                    <div class="metric-row">
                        <span class="metric-label">Alcance</span>
                        <span class="metric-value">{fmt_num(acc['reach'])}</span>
                    </div>
                </div>
            </div>

            <div class="analysis-section">
                {low_perf_html}
                <div class="section-block suggestions-block">
                    <h4>💡 Sugestões de Melhoria</h4>
                    <ul>{suggestions_html}</ul>
                </div>
                <div class="section-block campaigns-block">
                    <h4>🚀 Novas Campanhas a Criar</h4>
                    <ul>{new_camp_html}</ul>
                </div>
            </div>
        </div>
        """

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard Meta Ads — {date_start_fmt} a {date_end_fmt}</title>
    <style>
        :root {{
            --meta-blue: #1877F2;
            --meta-dark: #0a0a0a;
            --meta-card: #141414;
            --meta-border: #2a2a2a;
            --meta-text: #e8e8e8;
            --meta-muted: #888;
            --green: #00d67a;
            --red: #ff4444;
            --orange: #ff9500;
            --yellow: #ffd700;
            --purple: #9b59b6;
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #0d0d0d;
            color: var(--meta-text);
            min-height: 100vh;
        }}

        .top-banner {{
            background: linear-gradient(135deg, #1877F2 0%, #0050c8 50%, #003a9e 100%);
            padding: 30px 40px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        .top-banner::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.05) 0%, transparent 60%);
            animation: pulse 4s ease-in-out infinite;
        }}
        @keyframes pulse {{ 0%,100%{{transform:scale(1)}} 50%{{transform:scale(1.05)}} }}

        .banner-logo {{
            font-size: 14px;
            font-weight: 600;
            letter-spacing: 3px;
            text-transform: uppercase;
            color: rgba(255,255,255,0.7);
            margin-bottom: 8px;
        }}
        .banner-title {{
            font-size: 32px;
            font-weight: 800;
            color: #fff;
            margin-bottom: 6px;
        }}
        .banner-period {{
            font-size: 16px;
            color: rgba(255,255,255,0.85);
        }}
        .banner-generated {{
            font-size: 12px;
            color: rgba(255,255,255,0.5);
            margin-top: 8px;
        }}

        .summary-bar {{
            display: flex;
            justify-content: center;
            gap: 0;
            background: #111;
            border-bottom: 1px solid var(--meta-border);
            flex-wrap: wrap;
        }}
        .summary-item {{
            padding: 20px 30px;
            text-align: center;
            border-right: 1px solid var(--meta-border);
            min-width: 140px;
        }}
        .summary-item:last-child {{ border-right: none; }}
        .summary-num {{
            font-size: 24px;
            font-weight: 800;
            color: var(--meta-blue);
        }}
        .summary-label {{
            font-size: 11px;
            color: var(--meta-muted);
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-top: 4px;
        }}

        .controls {{
            padding: 20px 40px;
            display: flex;
            gap: 12px;
            align-items: center;
            flex-wrap: wrap;
            background: #111;
            border-bottom: 1px solid var(--meta-border);
        }}
        .filter-btn {{
            padding: 8px 18px;
            border-radius: 20px;
            border: 1px solid var(--meta-border);
            background: transparent;
            color: var(--meta-text);
            cursor: pointer;
            font-size: 13px;
            transition: all 0.2s;
        }}
        .filter-btn:hover, .filter-btn.active {{
            background: var(--meta-blue);
            border-color: var(--meta-blue);
        }}
        .search-box {{
            padding: 8px 16px;
            border-radius: 20px;
            border: 1px solid var(--meta-border);
            background: #1a1a1a;
            color: var(--meta-text);
            font-size: 13px;
            width: 220px;
            outline: none;
        }}
        .search-box:focus {{ border-color: var(--meta-blue); }}

        .dashboard-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(560px, 1fr));
            gap: 20px;
            padding: 30px 40px;
            max-width: 1600px;
            margin: 0 auto;
        }}

        .client-card {{
            background: var(--meta-card);
            border-radius: 16px;
            overflow: hidden;
            border: 1px solid var(--meta-border);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        .client-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 40px rgba(24,119,242,0.15);
        }}
        .card-good {{ border-left: 4px solid var(--green); }}
        .card-bad {{ border-left: 4px solid var(--red); }}
        .card-ok {{ border-left: 4px solid var(--meta-blue); }}
        .card-inactive {{ border-left: 4px solid #444; opacity: 0.6; }}

        .card-header {{
            padding: 18px 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            border-bottom: 1px solid var(--meta-border);
            background: linear-gradient(to right, #1a1a1a, #141414);
        }}
        .client-info {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}
        .client-avatar {{
            width: 44px;
            height: 44px;
            border-radius: 12px;
            background: var(--meta-blue);
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 18px;
            font-weight: 800;
            flex-shrink: 0;
        }}
        .client-info h3 {{
            font-size: 16px;
            font-weight: 700;
            color: #fff;
        }}
        .period-label {{
            font-size: 11px;
            color: var(--meta-muted);
            margin-top: 2px;
            display: block;
        }}

        .badge {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }}
        .badge-good {{ background: rgba(0,214,122,0.15); color: var(--green); border: 1px solid rgba(0,214,122,0.3); }}
        .badge-bad {{ background: rgba(255,68,68,0.15); color: var(--red); border: 1px solid rgba(255,68,68,0.3); }}
        .badge-ok {{ background: rgba(24,119,242,0.15); color: var(--meta-blue); border: 1px solid rgba(24,119,242,0.3); }}
        .badge-inactive {{ background: rgba(100,100,100,0.15); color: #666; border: 1px solid #333; }}

        .metrics-grid {{
            padding: 16px 20px;
        }}
        .metric-block {{
            border-radius: 10px;
            overflow: hidden;
        }}
        .metric-section-title {{
            font-size: 11px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1.5px;
            padding: 10px 14px;
            background: rgba(24,119,242,0.1);
            color: var(--meta-blue);
            border-bottom: 1px solid rgba(24,119,242,0.2);
        }}
        .meta-color .metric-section-title {{
            background: rgba(24,119,242,0.08);
            color: #5b9cf6;
        }}
        .metric-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 9px 14px;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            transition: background 0.15s;
        }}
        .metric-row:hover {{ background: rgba(255,255,255,0.03); }}
        .metric-row:last-child {{ border-bottom: none; }}
        .metric-label {{
            font-size: 13px;
            color: var(--meta-muted);
        }}
        .metric-value {{
            font-size: 14px;
            font-weight: 600;
            color: var(--meta-text);
        }}
        .metric-value.highlight {{ color: var(--yellow); font-size: 15px; }}
        .ctr-good {{ color: var(--green) !important; }}
        .ctr-bad {{ color: var(--red) !important; }}
        .cpl-good {{ color: var(--green) !important; }}
        .cpl-bad {{ color: var(--red) !important; }}

        .analysis-section {{
            padding: 0 20px 18px;
        }}
        .section-block {{
            border-radius: 10px;
            margin-top: 12px;
            overflow: hidden;
        }}
        .section-block h4 {{
            font-size: 12px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 1px;
            padding: 10px 14px;
        }}
        .section-block ul {{
            list-style: none;
            padding: 0;
        }}
        .section-block li {{
            padding: 8px 14px;
            font-size: 13px;
            line-height: 1.5;
            border-bottom: 1px solid rgba(255,255,255,0.04);
            color: #ccc;
        }}
        .section-block li:last-child {{ border-bottom: none; padding-bottom: 10px; }}

        .suggestions-block {{
            background: rgba(24,119,242,0.05);
            border: 1px solid rgba(24,119,242,0.15);
        }}
        .suggestions-block h4 {{ color: #5b9cf6; background: rgba(24,119,242,0.08); }}

        .campaigns-block {{
            background: rgba(155,89,182,0.05);
            border: 1px solid rgba(155,89,182,0.15);
        }}
        .campaigns-block h4 {{ color: #b388ff; background: rgba(155,89,182,0.08); }}

        .warning-block {{
            background: rgba(255,68,68,0.05);
            border: 1px solid rgba(255,68,68,0.15);
        }}
        .warning-block h4 {{ color: var(--red); background: rgba(255,68,68,0.08); }}

        .footer {{
            text-align: center;
            padding: 30px;
            color: var(--meta-muted);
            font-size: 12px;
            border-top: 1px solid var(--meta-border);
            margin-top: 20px;
        }}

        .hidden {{ display: none !important; }}

        @media (max-width: 768px) {{
            .dashboard-grid {{ grid-template-columns: 1fr; padding: 15px; }}
            .summary-bar {{ justify-content: flex-start; overflow-x: auto; }}
            .controls {{ padding: 15px; }}
            .banner-title {{ font-size: 22px; }}
        }}
    </style>
</head>
<body>

<div class="top-banner">
    <div class="banner-logo">Ao Cubo Marketing · Relatório Semanal</div>
    <div class="banner-title">📊 Dashboard Meta Ads</div>
    <div class="banner-period">Período: {date_start_fmt} — {date_end_fmt}</div>
    <div class="banner-generated">Gerado em {generated_at}</div>
</div>

<div class="summary-bar">
    <div class="summary-item">
        <div class="summary-num">{active_accounts}</div>
        <div class="summary-label">Contas Ativas</div>
    </div>
    <div class="summary-item">
        <div class="summary-num">{fmt_brl(total_spend)}</div>
        <div class="summary-label">Investimento Total</div>
    </div>
    <div class="summary-item">
        <div class="summary-num">{fmt_num(total_impressions)}</div>
        <div class="summary-label">Impressões</div>
    </div>
    <div class="summary-item">
        <div class="summary-num">{fmt_num(total_clicks)}</div>
        <div class="summary-label">Cliques</div>
    </div>
    <div class="summary-item">
        <div class="summary-num">{fmt_num(total_leads)}</div>
        <div class="summary-label">Leads Totais</div>
    </div>
    <div class="summary-item">
        <div class="summary-num">{fmt_pct(avg_ctr)}</div>
        <div class="summary-label">CTR Médio</div>
    </div>
    <div class="summary-item">
        <div class="summary-num">{fmt_brl(avg_cpl)}</div>
        <div class="summary-label">CPL Médio</div>
    </div>
</div>

<div class="controls">
    <input class="search-box" type="text" placeholder="🔍 Buscar cliente..." oninput="filterCards(this.value)" />
    <button class="filter-btn active" onclick="filterStatus('all', this)">Todos</button>
    <button class="filter-btn" onclick="filterStatus('good', this)">✅ Boa performance</button>
    <button class="filter-btn" onclick="filterStatus('bad', this)">⚠️ Atenção</button>
    <button class="filter-btn" onclick="filterStatus('inactive', this)">📴 Sem dados</button>
</div>

<div class="dashboard-grid" id="grid">
{cards_html}
</div>

<div class="footer">
    Dashboard gerado automaticamente · Ao Cubo Marketing · {generated_at}<br>
    Dados via Meta Ads API v19.0 · Período: {date_start_fmt} a {date_end_fmt}
</div>

<script>
function filterCards(query) {{
    const q = query.toLowerCase();
    document.querySelectorAll('.client-card').forEach(card => {{
        const name = card.querySelector('h3').textContent.toLowerCase();
        card.classList.toggle('hidden', !name.includes(q));
    }});
}}

function filterStatus(status, btn) {{
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.client-card').forEach(card => {{
        if (status === 'all') {{
            card.classList.remove('hidden');
        }} else {{
            card.classList.toggle('hidden', !card.classList.contains('card-' + status));
        }}
    }});
}}
</script>
</body>
</html>"""
    return html


def main(date_start=None, date_end=None):
    if not date_start:
        today = datetime.now()
        last_monday = today - timedelta(days=today.weekday() + 7)
        last_sunday = last_monday + timedelta(days=6)
        date_start = last_monday.strftime("%Y-%m-%d")
        date_end = last_sunday.strftime("%Y-%m-%d")

    print(f"\n{'='*60}")
    print(f"  META ADS DASHBOARD — {date_start} a {date_end}")
    print(f"{'='*60}")
    print(f"  Buscando dados de {len(ACCOUNTS)} contas...\n")

    accounts_data = []
    for i, account in enumerate(ACCOUNTS):
        print(f"  [{i+1:02d}/{len(ACCOUNTS)}] {account['name'][:40]:<40}", end=" ", flush=True)
        insights = fetch_account_insights(account["id"], date_start, date_end)
        campaigns = fetch_campaigns(account["id"], date_start, date_end)
        data = analyze_account(account, insights, campaigns)
        accounts_data.append(data)
        status = f"R$ {data['spend']:.0f} | {data['leads']} leads" if data["has_data"] else "sem dados"
        print(f"→ {status}")

    accounts_data.sort(key=lambda x: x["spend"], reverse=True)

    html = generate_html(accounts_data, date_start, date_end)

    output_dir = os.path.dirname(os.path.abspath(__file__))
    filename = f"dashboard_{date_start}_{date_end}.html"
    filepath = os.path.join(output_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    latest_path = os.path.join(output_dir, "dashboard_latest.html")
    with open(latest_path, "w", encoding="utf-8") as f:
        f.write(html)

    total = sum(a["spend"] for a in accounts_data)
    leads = sum(a["leads"] for a in accounts_data)
    print(f"\n{'='*60}")
    print(f"  ✅ Dashboard gerado: {filename}")
    print(f"  💰 Total investido: R$ {total:,.2f}")
    print(f"  🎯 Total de leads: {leads}")
    print(f"  📁 Arquivo: {filepath}")
    print(f"{'='*60}\n")

    return filepath


if __name__ == "__main__":
    if len(sys.argv) == 3:
        main(sys.argv[1], sys.argv[2])
    else:
        main("2026-04-20", "2026-04-27")
