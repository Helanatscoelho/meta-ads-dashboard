import requests
import json
from datetime import datetime

TOKEN = "EAAddAZBQXZBVgBRSDYotmCrU8yLZAxe7Ysu3AJ5VEjkoOLj9cyuKazKI5pbpIozZCWz4V1WQwvCtKK4xj41tO9dSCiNir65YSyrD7Ft75ANA5KYhYpldeKtHVrUXVVU3PhcYky7QAkDZBPsBj4cDgQlMnZCMZCBLVPal8jAAo0VxSEvV7ACgEyhvTAhZCfXA0i7jQSqEKKSbZB1vKkLZCiqyBqzvkomFtlqhNrptMr"

ACCOUNTS = [
    {"id": "act_101403706860167", "name": "Conta 01 - Ads Perfiletto V4"},
    {"id": "act_267770730525130", "name": "Helena Coelho"},
    {"id": "act_2410626089217011", "name": "Conta 2410626089217011"},
    {"id": "act_1182499605271369", "name": "MM Protege"},
    {"id": "act_655917871724513", "name": "Ergy Diesel"},
    {"id": "act_196598645524416", "name": "Marcelo Costa"},
    {"id": "act_297842908343350", "name": "CA 01 - Arapongas Centro do Sorriso"},
    {"id": "act_404664394554450", "name": "Anúncios Saniteck"},
    {"id": "act_558494692916247", "name": "Lady Livretos"},
    {"id": "act_839314777805875", "name": "CENTRO DO SORRISO CAMPO MOURÃO"},
    {"id": "act_1047813853024474", "name": "CHEFLERA ADS"},
    {"id": "act_1559065974904383", "name": "CA01 | Clinica Moliah"},
    {"id": "act_1648225505751115", "name": "CA - COMUNIDADE TRINDADE SANTA"},
    {"id": "act_864538029208474", "name": "INSTA - MONIQUE"},
    {"id": "act_557811123855687", "name": "CA - LOJA TRINDADE SANTA"},
    {"id": "act_2029226410831026", "name": "CA - HELENA"},
    {"id": "act_1205207067848409", "name": "CA 01 - Rolândia Centro do Sorriso"},
    {"id": "act_1303967340832416", "name": "Odonto Bless Londrina"},
    {"id": "act_668541309479669", "name": "CA - Castro e Figueira"},
    {"id": "act_1908379856581665", "name": "CA - CAROL MEIRELLES 2"},
    {"id": "act_1575227266844090", "name": "Vedoi"},
    {"id": "act_877477095207362", "name": "Star Veiculos"},
]

FIELDS = "impressions,clicks,spend,reach,ctr,cpc,cpm,frequency,actions,cost_per_action_type"

def fetch_insights(account_id):
    url = f"https://graph.facebook.com/v19.0/{account_id}/insights"
    params = {
        "fields": FIELDS,
        "date_preset": "this_month",
        "level": "account",
        "access_token": TOKEN,
    }
    r = requests.get(url, params=params, timeout=30)
    data = r.json()
    if data.get("data"):
        return data["data"][0]
    return None

def get_action(actions, action_type):
    if not actions:
        return 0
    for a in actions:
        if a["action_type"] == action_type:
            return int(a["value"])
    return 0

def get_cost_per_action(cost_list, action_type):
    if not cost_list:
        return 0
    for a in cost_list:
        if a["action_type"] == action_type:
            return float(a["value"])
    return 0

def fmt_brl(val):
    return f"R$ {float(val):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def fmt_num(val):
    return f"{int(val):,}".replace(",", ".")

def fmt_pct(val):
    return f"{float(val):.2f}%"

def fmt_dec(val):
    return f"{float(val):.2f}"

print("Buscando dados de todas as contas...")
accounts_data = []
for acc in ACCOUNTS:
    print(f"  {acc['name']}...")
    insights = fetch_insights(acc["id"])
    accounts_data.append({"account": acc, "insights": insights})

# Totals
total_spend = sum(float(d["insights"]["spend"]) for d in accounts_data if d["insights"] and d["insights"].get("spend"))
total_impressions = sum(int(d["insights"]["impressions"]) for d in accounts_data if d["insights"] and d["insights"].get("impressions"))
total_clicks = sum(int(d["insights"]["clicks"]) for d in accounts_data if d["insights"] and d["insights"].get("clicks"))
total_reach = sum(int(d["insights"]["reach"]) for d in accounts_data if d["insights"] and d["insights"].get("reach"))

total_leads = 0
total_messages = 0
for d in accounts_data:
    if d["insights"]:
        actions = d["insights"].get("actions", [])
        total_leads += get_action(actions, "lead") + get_action(actions, "onsite_conversion.lead")
        total_messages += get_action(actions, "onsite_conversion.messaging_conversation_started_7d")

active_accounts = sum(1 for d in accounts_data if d["insights"])
total_ctr = (total_clicks / total_impressions * 100) if total_impressions > 0 else 0
total_cpl = (total_spend / total_leads) if total_leads > 0 else 0
avg_cpm = (total_spend / total_impressions * 1000) if total_impressions > 0 else 0
avg_cpc = (total_spend / total_clicks) if total_clicks > 0 else 0

today = datetime.now()
date_range = f"01/05/2026 → {today.strftime('%d/%m/%Y')}"
generated_at = today.strftime("%d/%m/%Y às %H:%M")

def performance_badge(insights):
    if not insights:
        return '<span class="badge badge-nodata">Sem dados</span>'
    ctr = float(insights.get("ctr", 0))
    spend = float(insights.get("spend", 0))
    if spend == 0:
        return '<span class="badge badge-nodata">Sem dados</span>'
    if ctr >= 1.5:
        return '<span class="badge badge-good">✓ Bom desempenho</span>'
    elif ctr >= 0.5:
        return '<span class="badge badge-warning">⚠ Atenção</span>'
    else:
        return '<span class="badge badge-bad">✗ Baixo desempenho</span>'

def build_account_card(d):
    acc = d["account"]
    ins = d["insights"]
    initial = acc["name"][0].upper()

    if not ins or float(ins.get("spend", 0)) == 0:
        return f'''
        <div class="account-card no-data">
            <div class="account-header">
                <div class="account-avatar">{initial}</div>
                <div class="account-info">
                    <h3>{acc["name"]}</h3>
                    <small>{date_range}</small>
                </div>
                <span class="badge badge-nodata">Sem dados</span>
            </div>
            <div class="no-data-msg">Nenhum dado de investimento neste período.</div>
        </div>'''

    actions = ins.get("actions", [])
    cost_list = ins.get("cost_per_action_type", [])
    spend = float(ins.get("spend", 0))
    impressions = int(ins.get("impressions", 0))
    clicks = int(ins.get("clicks", 0))
    reach = int(ins.get("reach", 0))
    ctr = float(ins.get("ctr", 0))
    cpc = float(ins.get("cpc", 0))
    cpm = float(ins.get("cpm", 0))
    freq = float(ins.get("frequency", 0))

    leads = get_action(actions, "lead") + get_action(actions, "onsite_conversion.lead") + get_action(actions, "onsite_conversion.lead_grouped")
    link_clicks = get_action(actions, "link_click")
    video_views = get_action(actions, "video_view")
    msg_started = get_action(actions, "onsite_conversion.messaging_conversation_started_7d")
    msg_connections = get_action(actions, "onsite_conversion.total_messaging_connection")

    conversations = msg_started + msg_connections
    cpl = (spend / leads) if leads > 0 else 0
    cpm_msg = (spend / conversations) if conversations > 0 else 0

    badge = performance_badge(ins)

    leads_row = f'''
        <div class="metric-row">
            <span class="metric-label">🎯 Leads</span>
            <span class="metric-value">{fmt_num(leads)}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">💬 Conversas iniciadas</span>
            <span class="metric-value">{fmt_num(conversations)}</span>
        </div>
        <div class="metric-row">
            <span class="metric-label">💸 CPL</span>
            <span class="metric-value">{fmt_brl(cpl) if leads > 0 else "—"}</span>
        </div>''' if leads > 0 or conversations > 0 else f'''
        <div class="metric-row">
            <span class="metric-label">💬 Conversas iniciadas</span>
            <span class="metric-value">{fmt_num(conversations)}</span>
        </div>'''

    video_row = f'''
        <div class="metric-row">
            <span class="metric-label">▶ Views de vídeo</span>
            <span class="metric-value">{fmt_num(video_views)}</span>
        </div>''' if video_views > 0 else ""

    return f'''
    <div class="account-card">
        <div class="account-header">
            <div class="account-avatar">{initial}</div>
            <div class="account-info">
                <h3>{acc["name"]}</h3>
                <small>{date_range}</small>
            </div>
            {badge}
        </div>
        <div class="metrics-grid">
            <div class="metric-row highlight">
                <span class="metric-label">💰 Investimento</span>
                <span class="metric-value">{fmt_brl(spend)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">👁 Impressões</span>
                <span class="metric-value">{fmt_num(impressions)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">🌐 Alcance</span>
                <span class="metric-value">{fmt_num(reach)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">🔁 Frequência</span>
                <span class="metric-value">{fmt_dec(freq)}x</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">🖱 Cliques</span>
                <span class="metric-value">{fmt_num(clicks)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">🔗 Link Clicks</span>
                <span class="metric-value">{fmt_num(link_clicks)}</span>
            </div>
            {leads_row}
            {video_row}
            <div class="metric-row">
                <span class="metric-label">📊 CTR</span>
                <span class="metric-value {'ctr-good' if ctr >= 1.5 else 'ctr-warn' if ctr >= 0.5 else 'ctr-bad'}">{fmt_pct(ctr)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">💡 CPM</span>
                <span class="metric-value">{fmt_brl(cpm)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">🚀 CPC</span>
                <span class="metric-value">{fmt_brl(cpc)}</span>
            </div>
        </div>
    </div>'''

cards_html = "\n".join(build_account_card(d) for d in accounts_data)

html = f'''<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Meta Ads — Ao Cubo Marketing</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background: #f5f6fa; color: #1a1a2e; }}

  .header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%); color: white; padding: 32px 40px; }}
  .header h1 {{ font-size: 28px; font-weight: 700; letter-spacing: -0.5px; }}
  .header p {{ color: rgba(255,255,255,0.6); font-size: 13px; margin-top: 6px; }}
  .header .agency {{ font-size: 13px; color: #4fc3f7; font-weight: 600; margin-bottom: 6px; text-transform: uppercase; letter-spacing: 1px; }}

  .summary {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; padding: 28px 40px; background: white; border-bottom: 1px solid #e8ecf0; }}
  .kpi {{ text-align: center; padding: 16px; background: #f8f9fc; border-radius: 12px; }}
  .kpi .value {{ font-size: 26px; font-weight: 800; color: #1a1a2e; }}
  .kpi .label {{ font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-top: 4px; }}

  .legend {{ display: flex; gap: 20px; padding: 16px 40px; background: white; border-bottom: 1px solid #e8ecf0; flex-wrap: wrap; align-items: center; }}
  .legend-title {{ font-size: 12px; font-weight: 600; color: #555; }}
  .badge {{ font-size: 11px; font-weight: 600; padding: 4px 10px; border-radius: 20px; }}
  .badge-good {{ background: #e8f5e9; color: #2e7d32; }}
  .badge-warning {{ background: #fff8e1; color: #f57f17; }}
  .badge-bad {{ background: #ffebee; color: #c62828; }}
  .badge-nodata {{ background: #f5f5f5; color: #9e9e9e; }}

  .container {{ padding: 28px 40px; display: grid; grid-template-columns: repeat(auto-fill, minmax(380px, 1fr)); gap: 20px; }}

  .account-card {{ background: white; border-radius: 16px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.06); border: 1px solid #e8ecf0; transition: box-shadow 0.2s; }}
  .account-card:hover {{ box-shadow: 0 6px 24px rgba(0,0,0,0.1); }}
  .account-card.no-data {{ opacity: 0.65; }}

  .account-header {{ display: flex; align-items: center; gap: 14px; padding: 18px 20px; border-bottom: 1px solid #f0f2f5; }}
  .account-avatar {{ width: 44px; height: 44px; border-radius: 12px; background: linear-gradient(135deg, #1a1a2e, #4fc3f7); color: white; display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 700; flex-shrink: 0; }}
  .account-info {{ flex: 1; min-width: 0; }}
  .account-info h3 {{ font-size: 14px; font-weight: 700; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }}
  .account-info small {{ font-size: 11px; color: #aaa; }}

  .metrics-grid {{ padding: 14px 20px 18px; }}
  .metric-row {{ display: flex; justify-content: space-between; align-items: center; padding: 7px 0; border-bottom: 1px solid #f5f6fa; }}
  .metric-row:last-child {{ border-bottom: none; }}
  .metric-row.highlight {{ background: #f8f9fc; margin: 0 -4px; padding: 8px 4px; border-radius: 8px; border-bottom: none; margin-bottom: 4px; }}
  .metric-label {{ font-size: 13px; color: #666; }}
  .metric-value {{ font-size: 13px; font-weight: 700; color: #1a1a2e; }}
  .ctr-good {{ color: #2e7d32; }}
  .ctr-warn {{ color: #f57f17; }}
  .ctr-bad {{ color: #c62828; }}

  .no-data-msg {{ padding: 20px; text-align: center; color: #bbb; font-size: 13px; }}

  footer {{ text-align: center; padding: 20px; color: #bbb; font-size: 12px; background: white; border-top: 1px solid #e8ecf0; margin-top: 10px; }}

  @media(max-width: 600px) {{
    .header, .summary, .legend, .container {{ padding-left: 16px; padding-right: 16px; }}
    .container {{ grid-template-columns: 1fr; }}
  }}
</style>
</head>
<body>

<div class="header">
  <div class="agency">Ao Cubo Marketing</div>
  <h1>Dashboard Meta Ads</h1>
  <p>Período: {date_range} &nbsp;·&nbsp; Gerado em {generated_at}</p>
</div>

<div class="summary">
  <div class="kpi"><div class="value">{active_accounts}</div><div class="label">Contas ativas</div></div>
  <div class="kpi"><div class="value">{fmt_brl(total_spend)}</div><div class="label">Investimento total</div></div>
  <div class="kpi"><div class="value">{fmt_num(total_impressions)}</div><div class="label">Impressões</div></div>
  <div class="kpi"><div class="value">{fmt_num(total_reach)}</div><div class="label">Alcance total</div></div>
  <div class="kpi"><div class="value">{fmt_num(total_clicks)}</div><div class="label">Cliques</div></div>
  <div class="kpi"><div class="value">{fmt_num(total_leads + total_messages)}</div><div class="label">Leads / Conversas</div></div>
  <div class="kpi"><div class="value">{fmt_pct(total_ctr)}</div><div class="label">CTR médio</div></div>
  <div class="kpi"><div class="value">{fmt_brl(avg_cpm)}</div><div class="label">CPM médio</div></div>
</div>

<div class="legend">
  <span class="legend-title">Desempenho CTR:</span>
  <span class="badge badge-good">✓ Bom (CTR ≥ 1.5%)</span>
  <span class="badge badge-warning">⚠ Atenção (0.5% – 1.5%)</span>
  <span class="badge badge-bad">✗ Baixo (CTR &lt; 0.5%)</span>
  <span class="badge badge-nodata">Sem dados</span>
</div>

<div class="container">
{cards_html}
</div>

<footer>Ao Cubo Marketing · Dashboard Meta Ads · {generated_at}</footer>

</body>
</html>'''

output_path = "dashboard_meta_ads.html"
with open(output_path, "w", encoding="utf-8") as f:
    f.write(html)

print(f"\n✓ Dashboard gerado: {output_path}")
print(f"  Contas ativas: {active_accounts}/{len(ACCOUNTS)}")
print(f"  Investimento total: {fmt_brl(total_spend)}")
print(f"  Impressões: {fmt_num(total_impressions)}")
print(f"  CTR médio: {fmt_pct(total_ctr)}")
