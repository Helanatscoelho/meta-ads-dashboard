const https = require('https');
const fs = require('fs');

const TOKEN = "EAAddAZBQXZBVgBRSDYotmCrU8yLZAxe7Ysu3AJ5VEjkoOLj9cyuKazKI5pbpIozZCWz4V1WQwvCtKK4xj41tO9dSCiNir65YSyrD7Ft75ANA5KYhYpldeKtHVrUXVVU3PhcYky7QAkDZBPsBj4cDgQlMnZCMZCBLVPal8jAAo0VxSEvV7ACgEyhvTAhZCfXA0i7jQSqEKKSbZB1vKkLZCiqyBqzvkomFtlqhNrptMr";

const ACCOUNTS = [
  {id:"act_101403706860167", name:"Conta 01 - Ads Perfiletto V4"},
  {id:"act_267770730525130", name:"Helena Coelho"},
  {id:"act_2410626089217011", name:"Conta 2410626089217011"},
  {id:"act_1182499605271369", name:"MM Protege"},
  {id:"act_655917871724513", name:"Ergy Diesel"},
  {id:"act_196598645524416", name:"Marcelo Costa"},
  {id:"act_297842908343350", name:"CA 01 - Arapongas Centro do Sorriso"},
  {id:"act_404664394554450", name:"Anúncios Saniteck"},
  {id:"act_558494692916247", name:"Lady Livretos"},
  {id:"act_839314777805875", name:"Centro do Sorriso Campo Mourão"},
  {id:"act_1047813853024474", name:"CHEFLERA ADS"},
  {id:"act_1559065974904383", name:"CA01 | Clinica Moliah"},
  {id:"act_1648225505751115", name:"CA - Comunidade Trindade Santa"},
  {id:"act_864538029208474", name:"INSTA - MONIQUE"},
  {id:"act_557811123855687", name:"CA - Loja Trindade Santa"},
  {id:"act_2029226410831026", name:"CA - Helena"},
  {id:"act_1205207067848409", name:"CA 01 - Rolândia Centro do Sorriso"},
  {id:"act_1303967340832416", name:"Odonto Bless Londrina"},
  {id:"act_668541309479669", name:"CA - Castro e Figueira"},
  {id:"act_1908379856581665", name:"CA - Carol Meirelles 2"},
  {id:"act_1575227266844090", name:"Vedoi"},
  {id:"act_877477095207362", name:"Star Veiculos"},
];

const FIELDS = "impressions,clicks,spend,reach,ctr,cpc,cpm,frequency,actions,cost_per_action_type";

function fetchJson(url) {
  return new Promise((resolve, reject) => {
    https.get(url, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve(JSON.parse(data)); } catch(e) { reject(e); }
      });
    }).on('error', reject);
  });
}

function fetchInsights(accountId) {
  const params = new URLSearchParams({
    fields: FIELDS,
    date_preset: 'this_month',
    level: 'account',
    access_token: TOKEN
  });
  const url = `https://graph.facebook.com/v19.0/${accountId}/insights?${params}`;
  return fetchJson(url).then(d => (d.data && d.data.length > 0) ? d.data[0] : null);
}

function getAction(actions, type) {
  if (!actions) return 0;
  const a = actions.find(x => x.action_type === type);
  return a ? parseInt(a.value) : 0;
}

function fmtBRL(val) {
  return 'R$ ' + parseFloat(val).toLocaleString('pt-BR', {minimumFractionDigits:2, maximumFractionDigits:2});
}
function fmtNum(val) {
  return parseInt(val).toLocaleString('pt-BR');
}
function fmtPct(val) {
  return parseFloat(val).toFixed(2) + '%';
}
function fmtDec(val) {
  return parseFloat(val).toFixed(2);
}

function performanceBadge(ins) {
  if (!ins || parseFloat(ins.spend || 0) === 0) return '<span class="badge badge-nodata">Sem dados</span>';
  const ctr = parseFloat(ins.ctr || 0);
  if (ctr >= 1.5) return '<span class="badge badge-good">✓ Bom desempenho</span>';
  if (ctr >= 0.5) return '<span class="badge badge-warning">⚠ Atenção</span>';
  return '<span class="badge badge-bad">✗ Baixo desempenho</span>';
}

function buildCard(d) {
  const acc = d.account;
  const ins = d.insights;
  const initial = [...acc.name][0].toUpperCase();

  if (!ins || parseFloat(ins.spend || 0) === 0) {
    return `
    <div class="account-card no-data">
      <div class="account-header">
        <div class="account-avatar">${initial}</div>
        <div class="account-info"><h3>${acc.name}</h3><small>${DATE_RANGE}</small></div>
        <span class="badge badge-nodata">Sem dados</span>
      </div>
      <div class="no-data-msg">Nenhum dado de investimento neste período.</div>
    </div>`;
  }

  const actions = ins.actions || [];
  const spend = parseFloat(ins.spend || 0);
  const impressions = parseInt(ins.impressions || 0);
  const clicks = parseInt(ins.clicks || 0);
  const reach = parseInt(ins.reach || 0);
  const ctr = parseFloat(ins.ctr || 0);
  const cpc = parseFloat(ins.cpc || 0);
  const cpm = parseFloat(ins.cpm || 0);
  const freq = parseFloat(ins.frequency || 0);

  const leads = getAction(actions,'lead') + getAction(actions,'onsite_conversion.lead') + getAction(actions,'onsite_conversion.lead_grouped');
  const linkClicks = getAction(actions,'link_click');
  const videoViews = getAction(actions,'video_view');
  const msgStarted = getAction(actions,'onsite_conversion.messaging_conversation_started_7d');
  const msgConn = getAction(actions,'onsite_conversion.total_messaging_connection');
  const conversations = msgStarted + msgConn;
  const cpl = leads > 0 ? spend / leads : 0;

  const ctrClass = ctr >= 1.5 ? 'ctr-good' : ctr >= 0.5 ? 'ctr-warn' : 'ctr-bad';

  const leadsRows = (leads > 0 || conversations > 0) ? `
      <div class="metric-row">
        <span class="metric-label">🎯 Leads</span>
        <span class="metric-value">${fmtNum(leads)}</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">💬 Conversas</span>
        <span class="metric-value">${fmtNum(conversations)}</span>
      </div>
      ${leads > 0 ? `<div class="metric-row"><span class="metric-label">💸 CPL</span><span class="metric-value">${fmtBRL(cpl)}</span></div>` : ''}
  ` : `
      <div class="metric-row">
        <span class="metric-label">💬 Conversas</span>
        <span class="metric-value">${fmtNum(conversations)}</span>
      </div>
  `;

  const videoRow = videoViews > 0 ? `
      <div class="metric-row">
        <span class="metric-label">▶ Views de vídeo</span>
        <span class="metric-value">${fmtNum(videoViews)}</span>
      </div>` : '';

  return `
  <div class="account-card">
    <div class="account-header">
      <div class="account-avatar">${initial}</div>
      <div class="account-info"><h3>${acc.name}</h3><small>${DATE_RANGE}</small></div>
      ${performanceBadge(ins)}
    </div>
    <div class="metrics-grid">
      <div class="metric-row highlight">
        <span class="metric-label">💰 Investimento</span>
        <span class="metric-value">${fmtBRL(spend)}</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">👁 Impressões</span>
        <span class="metric-value">${fmtNum(impressions)}</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">🌐 Alcance</span>
        <span class="metric-value">${fmtNum(reach)}</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">🔁 Frequência</span>
        <span class="metric-value">${fmtDec(freq)}x</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">🖱 Cliques</span>
        <span class="metric-value">${fmtNum(clicks)}</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">🔗 Link Clicks</span>
        <span class="metric-value">${fmtNum(linkClicks)}</span>
      </div>
      ${leadsRows}
      ${videoRow}
      <div class="metric-row">
        <span class="metric-label">📊 CTR</span>
        <span class="metric-value ${ctrClass}">${fmtPct(ctr)}</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">💡 CPM</span>
        <span class="metric-value">${fmtBRL(cpm)}</span>
      </div>
      <div class="metric-row">
        <span class="metric-label">🚀 CPC</span>
        <span class="metric-value">${fmtBRL(cpc)}</span>
      </div>
    </div>
  </div>`;
}

const now = new Date();
const DATE_RANGE = `01/05/2026 → ${now.toLocaleDateString('pt-BR')}`;
const GENERATED_AT = now.toLocaleString('pt-BR', {day:'2-digit',month:'2-digit',year:'numeric',hour:'2-digit',minute:'2-digit'});

async function main() {
  console.log('Buscando dados de todas as contas...');

  const results = await Promise.all(
    ACCOUNTS.map(async acc => {
      process.stdout.write(`  ${acc.name}...\n`);
      const insights = await fetchInsights(acc.id).catch(() => null);
      return { account: acc, insights };
    })
  );

  const active = results.filter(d => d.insights && parseFloat(d.insights.spend||0) > 0);
  const totalSpend = active.reduce((s,d) => s + parseFloat(d.insights.spend||0), 0);
  const totalImpressions = active.reduce((s,d) => s + parseInt(d.insights.impressions||0), 0);
  const totalClicks = active.reduce((s,d) => s + parseInt(d.insights.clicks||0), 0);
  const totalReach = active.reduce((s,d) => s + parseInt(d.insights.reach||0), 0);

  let totalLeads = 0, totalConversations = 0;
  active.forEach(d => {
    const actions = d.insights.actions || [];
    totalLeads += getAction(actions,'lead') + getAction(actions,'onsite_conversion.lead');
    totalConversations += getAction(actions,'onsite_conversion.messaging_conversation_started_7d') + getAction(actions,'onsite_conversion.total_messaging_connection');
  });

  const totalCTR = totalImpressions > 0 ? (totalClicks / totalImpressions * 100) : 0;
  const avgCPM = totalImpressions > 0 ? (totalSpend / totalImpressions * 1000) : 0;

  const cards = results.map(d => buildCard(d)).join('\n');

  const html = `<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Dashboard Meta Ads — Ao Cubo Marketing</title>
<style>
  *{box-sizing:border-box;margin:0;padding:0}
  body{font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;background:#f5f6fa;color:#1a1a2e}
  .header{background:linear-gradient(135deg,#1a1a2e 0%,#16213e 100%);color:white;padding:32px 40px}
  .header h1{font-size:28px;font-weight:700;letter-spacing:-0.5px}
  .header p{color:rgba(255,255,255,0.6);font-size:13px;margin-top:6px}
  .header .agency{font-size:12px;color:#4fc3f7;font-weight:600;margin-bottom:6px;text-transform:uppercase;letter-spacing:1px}
  .summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px;padding:28px 40px;background:white;border-bottom:1px solid #e8ecf0}
  .kpi{text-align:center;padding:16px;background:#f8f9fc;border-radius:12px}
  .kpi .value{font-size:22px;font-weight:800;color:#1a1a2e}
  .kpi .label{font-size:11px;color:#888;text-transform:uppercase;letter-spacing:0.5px;margin-top:4px}
  .legend{display:flex;gap:16px;padding:14px 40px;background:white;border-bottom:1px solid #e8ecf0;flex-wrap:wrap;align-items:center}
  .legend-title{font-size:12px;font-weight:600;color:#555}
  .badge{font-size:11px;font-weight:600;padding:4px 10px;border-radius:20px}
  .badge-good{background:#e8f5e9;color:#2e7d32}
  .badge-warning{background:#fff8e1;color:#f57f17}
  .badge-bad{background:#ffebee;color:#c62828}
  .badge-nodata{background:#f5f5f5;color:#9e9e9e}
  .container{padding:28px 40px;display:grid;grid-template-columns:repeat(auto-fill,minmax(360px,1fr));gap:20px}
  .account-card{background:white;border-radius:16px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.06);border:1px solid #e8ecf0;transition:box-shadow 0.2s}
  .account-card:hover{box-shadow:0 6px 24px rgba(0,0,0,0.1)}
  .account-card.no-data{opacity:0.6}
  .account-header{display:flex;align-items:center;gap:14px;padding:18px 20px;border-bottom:1px solid #f0f2f5}
  .account-avatar{width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,#1a1a2e,#4fc3f7);color:white;display:flex;align-items:center;justify-content:center;font-size:18px;font-weight:700;flex-shrink:0}
  .account-info{flex:1;min-width:0}
  .account-info h3{font-size:14px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .account-info small{font-size:11px;color:#aaa}
  .metrics-grid{padding:14px 20px 18px}
  .metric-row{display:flex;justify-content:space-between;align-items:center;padding:7px 0;border-bottom:1px solid #f5f6fa}
  .metric-row:last-child{border-bottom:none}
  .metric-row.highlight{background:#f8f9fc;margin:0 -4px 4px;padding:8px 4px;border-radius:8px;border-bottom:none}
  .metric-label{font-size:13px;color:#666}
  .metric-value{font-size:13px;font-weight:700;color:#1a1a2e}
  .ctr-good{color:#2e7d32}
  .ctr-warn{color:#f57f17}
  .ctr-bad{color:#c62828}
  .no-data-msg{padding:24px;text-align:center;color:#bbb;font-size:13px}
  footer{text-align:center;padding:20px;color:#bbb;font-size:12px;background:white;border-top:1px solid #e8ecf0;margin-top:10px}
  @media(max-width:600px){
    .header,.summary,.legend,.container{padding-left:16px;padding-right:16px}
    .container{grid-template-columns:1fr}
  }
</style>
</head>
<body>

<div class="header">
  <div class="agency">Ao Cubo Marketing</div>
  <h1>Dashboard Meta Ads</h1>
  <p>Período: ${DATE_RANGE} &nbsp;·&nbsp; Gerado em ${GENERATED_AT}</p>
</div>

<div class="summary">
  <div class="kpi"><div class="value">${active.length}</div><div class="label">Contas ativas</div></div>
  <div class="kpi"><div class="value">${fmtBRL(totalSpend)}</div><div class="label">Investimento total</div></div>
  <div class="kpi"><div class="value">${fmtNum(totalImpressions)}</div><div class="label">Impressões</div></div>
  <div class="kpi"><div class="value">${fmtNum(totalReach)}</div><div class="label">Alcance total</div></div>
  <div class="kpi"><div class="value">${fmtNum(totalClicks)}</div><div class="label">Cliques</div></div>
  <div class="kpi"><div class="value">${fmtNum(totalLeads + totalConversations)}</div><div class="label">Leads / Conversas</div></div>
  <div class="kpi"><div class="value">${fmtPct(totalCTR)}</div><div class="label">CTR médio</div></div>
  <div class="kpi"><div class="value">${fmtBRL(avgCPM)}</div><div class="label">CPM médio</div></div>
</div>

<div class="legend">
  <span class="legend-title">Desempenho CTR:</span>
  <span class="badge badge-good">✓ Bom (CTR ≥ 1,5%)</span>
  <span class="badge badge-warning">⚠ Atenção (0,5% – 1,5%)</span>
  <span class="badge badge-bad">✗ Baixo (CTR &lt; 0,5%)</span>
  <span class="badge badge-nodata">Sem dados</span>
</div>

<div class="container">
${cards}
</div>

<footer>Ao Cubo Marketing · Dashboard Meta Ads · ${GENERATED_AT}</footer>

</body>
</html>`;

  fs.writeFileSync('dashboard_meta_ads.html', html, 'utf8');
  console.log(`\n✓ Dashboard gerado: dashboard_meta_ads.html`);
  console.log(`  Contas ativas: ${active.length}/${ACCOUNTS.length}`);
  console.log(`  Investimento total: ${fmtBRL(totalSpend)}`);
  console.log(`  Impressões: ${fmtNum(totalImpressions)}`);
  console.log(`  CTR médio: ${fmtPct(totalCTR)}`);
}

main().catch(console.error);
