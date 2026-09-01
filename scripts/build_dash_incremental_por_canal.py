import json

rows = json.load(open('incremental_por_canal_data.json', encoding='utf-8'))
DATA_JS = json.dumps(rows, ensure_ascii=False)
TOTAL_CONV = json.load(open('total_conversoes_mes.json', encoding='utf-8'))
TOTAL_CONV_JS = json.dumps(TOTAL_CONV, ensure_ascii=False)
COMUNIC_ROWS = json.load(open('comunicacoes_por_proposta_data.json', encoding='utf-8'))
COMUNIC_JS = json.dumps(COMUNIC_ROWS, ensure_ascii=False)
DIST_ROWS = json.load(open('distribuicao_comunicacoes_data.json', encoding='utf-8'))
DIST_JS = json.dumps(DIST_ROWS, ensure_ascii=False)

html = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>TC Aquisicao - Incremental por Canal (2026)</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { font-family: 'Segoe UI', Arial, sans-serif; background: #f4f5f7; color: #333; }

  .header {
    background: linear-gradient(135deg, #009ee3 0%, #00c1df 100%);
    color: white; padding: 22px 32px;
    display: flex; justify-content: space-between; align-items: flex-end;
  }
  .header h1 { font-size: 21px; font-weight: 700; margin-bottom: 4px; }
  .header p  { font-size: 13px; opacity: 0.85; }
  .header .meta { text-align: right; font-size: 12px; opacity: 0.85; line-height: 1.7; }

  .container { max-width: 1440px; margin: 0 auto; padding: 24px 20px; }

  .global-filter-bar {
    background: white; border-radius: 10px; padding: 12px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,.08); margin-bottom: 18px;
    display: flex; align-items: center; gap: 12px;
  }
  .global-filter-bar label { font-size: 11px; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: .4px; }
  .tc-btn {
    padding: 6px 16px; border: 1.5px solid #dde; border-radius: 7px;
    font-size: 12px; font-weight: 700; cursor: pointer; background: white; color: #666;
    transition: all .15s;
  }
  .tc-btn:hover { border-color: #6c47c9; color: #6c47c9; }
  .tc-btn.active { background: #6c47c9; border-color: #6c47c9; color: white; }
  .tc-btn.active[data-tc="MICRO"] { background: #ff7733; border-color: #ff7733; }

  .kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 20px; }
  .two-charts { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .chart-title { font-size: 13px; font-weight: 700; color: #333; margin-bottom: 2px; }
  .chart-sub { font-size: 11px; color: #777; margin-bottom: 8px; line-height: 1.4; }
  .kpi-card {
    background: white; border-radius: 10px; padding: 14px 16px;
    box-shadow: 0 1px 4px rgba(0,0,0,.08); border-left: 4px solid #009ee3;
  }
  .kpi-card.purple { border-left-color: #6c47c9; }
  .kpi-card.orange { border-left-color: #ff7733; }
  .kpi-label { font-size: 11px; color: #888; text-transform: uppercase; letter-spacing: .4px; margin-bottom: 5px; }
  .kpi-value { font-size: 22px; font-weight: 700; color: #222; }
  .kpi-sub   { font-size: 11px; color: #aaa; margin-top: 2px; }

  .card {
    background: white; border-radius: 10px; padding: 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,.08); margin-bottom: 18px;
  }
  .card-header { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; }
  .card h2 { font-size: 14px; font-weight: 600; color: #444; margin-bottom: 2px; }
  .card .sub { font-size: 11px; color: #aaa; margin-bottom: 16px; }
  .card .note { font-size: 11px; color: #c47a00; background: #fff8ec; border-left: 3px solid #ffb020; padding: 6px 10px; border-radius: 4px; margin-top: 10px; }

  .toggle-pct {
    padding: 5px 12px; border: 1.5px solid #dde; border-radius: 6px;
    font-size: 11px; font-weight: 700; cursor: pointer; background: white; color: #666;
    transition: all .15s; white-space: nowrap; flex-shrink: 0;
  }
  .toggle-pct:hover  { border-color: #6c47c9; color: #6c47c9; }
  .toggle-pct.active { background: #6c47c9; border-color: #6c47c9; color: white; }

  .filter-row { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }
  .filter-row label { font-size: 11px; font-weight: 700; color: #666; text-transform: uppercase; letter-spacing: .4px; }
  select#canalSelect {
    padding: 6px 12px; border: 1.5px solid #dde; border-radius: 6px;
    font-size: 13px; font-weight: 600; color: #333; background: white;
  }

  table.heat { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 14px; }
  table.heat th { background: #f0f6fb; color: #555; font-weight: 600; padding: 7px 8px; text-align: center; border-bottom: 2px solid #dde8f0; position: sticky; top: 0; }
  table.heat th:first-child { text-align: left; }
  table.heat td { padding: 6px 8px; text-align: center; border-bottom: 1px solid #f2f2f2; font-weight: 600; }
  table.heat td:first-child {
    text-align: left; font-weight: 700; color: #333;
    max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: help;
  }
  table.heat td.pos .abs { color: #00723a; }
  table.heat td.neg .abs { color: #a3001a; }
  table.heat td .abs { display: block; }
  table.heat td .pct { display: block; font-size: 9px; font-weight: 400; color: #999; }
  table.heat tr:last-child td { border-bottom: none; }
  .table-scroll { max-height: 560px; overflow-y: auto; margin-top: 14px; }
  .table-scroll table.heat { margin-top: 0; }

  .badge { display: inline-block; padding: 2px 8px; border-radius: 10px; font-size: 10px; font-weight: 700; color: white; }
  .badge.MKT { background: #6c47c9; }
  .badge.AUTOMATIZADA { background: #009ee3; }
  .badge.ELDORADO { background: #ff7733; }
</style>
</head>
<body>

<div class="header">
  <div>
    <h1>TC Aquisicao - Incremental por Canal</h1>
    <p>Quantidade INCREMENTAL de aquisicao de TC atribuivel a comunicacao, por canal (MKT x Automatizada) -- calculado por cohort de dia de envio</p>
  </div>
  <div class="meta">
    Metodologia: janela D0..D0+3 por cohort de envio<br>
    Escopo: campanhas TC/CCARD com grupo controle (2026)
  </div>
</div>

<div class="container">

  <div class="global-filter-bar">
    <label>Tipo TC</label>
    <button class="tc-btn active" data-tc="TODOS">Todos</button>
    <button class="tc-btn" data-tc="FULL">Full</button>
    <button class="tc-btn" data-tc="MICRO">Micro</button>
  </div>

  <div class="kpi-grid" id="kpiGrid"></div>

  <div class="card">
    <div class="card-header">
      <div>
        <h2>Incremental por canal, mes a mes</h2>
        <div class="sub">Quantidade incremental de aquisicao de TC atribuida a cada canal (soma de todas as campanhas daquele canal no mes)</div>
      </div>
      <div style="display:flex; gap:6px;">
        <button class="toggle-pct active" data-mode="abs">Valor absoluto</button>
        <button class="toggle-pct" data-mode="pct">% do total</button>
      </div>
    </div>
    <canvas id="chartCanal" height="90"></canvas>
    <div class="note">MKT = disparo unico/manual (blast datado); Automatizada = fluxo continuo/gatilho (flows_communication, D1/D6/D10/D14, BARRIDA, UPSELL, RMKT, USO etc). Classificacao pelo comportamento de envio dentro do mes, nao pelo nome da campanha -- exceto Eldorado, que conta como Automatizada sempre (mesmo quando dispara em 1 dia so).</div>
  </div>

  <div class="card">
    <div class="card-header">
      <div>
        <h2>Incremental como % do total de conversoes do mes</h2>
        <div class="sub">Quanto o incremental (por canal) representa do total de conversoes de TC no mes (todas as conversoes, nao so as ligadas a comunicacao) -- respeita o filtro de Tipo TC acima</div>
      </div>
    </div>
    <canvas id="chartPctConv" height="80"></canvas>
    <div class="note">Denominador = total de propostas aceitas no mes (FULL+MICRO, ou so o tipo filtrado), independente de ter recebido comunicacao ou nao.</div>

    <table class="heat" id="tblPerda" style="margin-top:20px;">
      <thead><tr>
        <th>Mes</th><th>% incremental (real)</th><th>Conversoes totais (real)</th>
        <th>Conversoes incrementais (real)</th>
        <th>Meta (media Fev-Abr)</th><th>Perda estimada</th>
      </tr></thead>
      <tbody id="tblPerdaBody"></tbody>
    </table>
    <div class="note">Base = Fev-Abr (Jan excluido -- teve um pico pontual de MKT/"MASSIVA" que nao se repete, inflaria a meta). Meta = % incremental ponderado por volume (soma incremental / soma conversoes de Fev-Abr). Perda so calculada a partir de Mai (Fev-Abr e a propria base de referencia). Formula assume que a conversao <b>organica</b> (nao-incremental) fica constante -- so a incremental muda: base_organica = total_real - incremental_real; total_necessario = base_organica / (1 - meta%); perda = total_necessario - total_real. Arredondamento sempre pra cima.</div>
  </div>

  <div class="card">
    <div class="card-header">
      <div>
        <h2>Comunicacoes por proposta -- por safra de encendido</h2>
        <div class="sub">Quantidade media de comunicacoes (toques distintos campanha+dia) que cada proposta recebeu numa janela FIXA de D0..D30 pos-encendido -- pra validar se a queda de incremental (grafico acima) coincide com contatar menos os usuarios. Mesmo escopo de campanhas do resto do dashboard (regex "Metodo B").</div>
      </div>
    </div>
    <canvas id="chartComunicacoes" height="80"></canvas>
    <div class="note">Janela fixa (nao a janela aberta até conversão/hoje) -- senao safras mais antigas pareceriam "mais comunicadas" so por terem tido mais tempo acumulando toques. Safra de <b>Ago/26 ainda nao maturou</b> (nao completou 30 dias corridos ainda) -- tratar como parcial, nao comparar direto com as outras.</div>
  </div>

  <div class="card">
    <div class="card-header">
      <div>
        <h2 id="distTitle">Distribuicao de comunicacoes por proposta ACEITA -- por safra de criacao</h2>
        <div class="sub" id="distSub">Apenas propostas com status aceito (CCARD_PROP_STATUS='accepted'), por safra de criacao (= mesma data de encendido). % que recebeu exatamente 0, 1, 2, ... 9 ou 10+ comunicacoes na janela D0..D30 -- mostra se a queda da media (grafico acima) e um deslocamento geral ou uma polarizacao, especificamente entre quem converteu.</div>
      </div>
    </div>
    <div class="filter-row">
      <div style="display:flex; gap:6px;">
        <button class="toggle-pct active" id="btnPopAceitas" data-mode="Aceitas">Proposta aceita</button>
        <button class="toggle-pct" id="btnPopTodos" data-mode="Todos">Proposta (todos)</button>
      </div>
      <div style="display:flex; gap:6px;">
        <button class="toggle-pct active" id="btnDistGranular" data-mode="granular">Granular (0,1,2...)</button>
        <button class="toggle-pct" id="btnDistFaixa" data-mode="faixa">Por faixa (1-3,4-6...)</button>
      </div>
      <div style="display:flex; gap:6px;">
        <button class="toggle-pct active" id="btnDistPct" data-mode="pct">% do total</button>
        <button class="toggle-pct" id="btnDistAbs" data-mode="abs">Valor absoluto</button>
      </div>
    </div>
    <canvas id="chartDistribuicao" height="80"></canvas>
    <div class="note">Cor = intensidade (0 comunicacoes = mais claro, 10+ = mais escuro) -- e uma progressao ordenada, nao categorias. Ago/26 ainda imaturo (mesma ressalva do grafico acima).</div>
  </div>

  <div class="card">
    <div class="card-header">
      <div>
        <h2>Taxa de conversao por faixa de comunicacoes -- por safra de criacao</h2>
        <div class="sub">Os dois graficos abaixo respondem perguntas diferentes com o mesmo dado de base.</div>
      </div>
    </div>
    <div class="filter-row">
      <div style="display:flex; gap:6px;">
        <button class="toggle-pct active" id="btnConvGranular" data-mode="granular">Granular (0,1,2...)</button>
        <button class="toggle-pct" id="btnConvFaixa" data-mode="faixa">Por faixa (1-3,4-6...)</button>
      </div>
    </div>
    <div class="two-charts">
      <div>
        <div class="chart-title">% de conversao DENTRO de cada grupo (aceitas / total do grupo)</div>
        <div class="chart-sub">Do total de propostas que receberam exatamente N comunicacoes, quantos % foram aceitas -- mostra se a conversao de cada faixa (ex: quem nao recebeu nenhuma) esta subindo, caindo ou estavel ao longo do tempo.</div>
        <canvas id="chartConvRateBucket" height="110"></canvas>
      </div>
      <div>
        <div class="chart-title">% do TOTAL ENCENDIDO que converteu com N comunicacoes</div>
        <div class="chart-sub">Do total encendido do mes (todas as propostas, nao so as de uma faixa), quantos % converteram tendo recebido exatamente N comunicacoes -- decompoe a taxa de conversao geral por faixa de comunicacao.</div>
        <canvas id="chartConvShareTotal" height="110"></canvas>
      </div>
    </div>
    <div class="note">Ago/26 ainda imaturo (mesma ressalva dos graficos acima) -- a faixa de poucas comunicacoes fica artificialmente inflada nesse mes.</div>
  </div>

  <div class="card">
    <div class="card-header">
      <div>
        <h2>Campanhas -- incremental mes a mes</h2>
        <div class="sub">Uma linha por campanha; cada celula mostra o valor absoluto e o % que a campanha representa do total do MES (dentro do canal filtrado). Todas as campanhas Eldorado (cupom 20/35/50/70/100%) sao agregadas numa unica linha "ELDORADO" -- canal continua Automatizada, Eldorado e so um sub-grupo dentro dele.</div>
      </div>
    </div>
    <div class="filter-row">
      <label>Canal</label>
      <select id="canalSelect">
        <option value="AUTOMATIZADA">Automatizada</option>
        <option value="MKT">MKT</option>
        <option value="TODOS">Todos</option>
      </select>
      <label>Visao</label>
      <button class="toggle-pct active" id="btnPorCampanha" data-mode="campanha">Por campanha</button>
      <button class="toggle-pct" id="btnPorJornada" data-mode="jornada">Por jornada</button>
    </div>
    <div class="table-scroll">
      <table class="heat" id="tblCampanhas">
        <thead><tr id="tblCampanhasHead"></tr></thead>
        <tbody></tbody>
      </table>
    </div>
  </div>

</div>

<script>
const DATA = __DATA_JS__;
const TOTAL_CONV = __TOTAL_CONV_JS__;
const COMUNIC_DATA = __COMUNIC_JS__;
const DIST_DATA = __DIST_JS__;

const MESES = [...new Set(DATA.map(r => r.mes))].sort();
const MES_LABELS = { '01':'Jan','02':'Fev','03':'Mar','04':'Abr','05':'Mai','06':'Jun','07':'Jul','08':'Ago','09':'Set','10':'Out','11':'Nov','12':'Dez' };
function mesLabel(m) { return MES_LABELS[m.slice(4,6)] + '/' + m.slice(2,4); }

function fmtInt(n) { return Math.round(n).toLocaleString('pt-BR'); }

// ---- Filtro global de Tipo TC (Full/Micro/Todos) ----
let tcFilter = 'TODOS';

function incVal(r) {
  if (tcFilter === 'FULL') return r.incremental_full;
  if (tcFilter === 'MICRO') return r.incremental_micro;
  return r.incremental;
}
function totalConvVal(mes) {
  const m = TOTAL_CONV[mes] || {};
  if (tcFilter === 'FULL') return m.FULL || 0;
  if (tcFilter === 'MICRO') return m.MICRO || 0;
  return (m.FULL || 0) + (m.MICRO || 0);
}

document.querySelectorAll('.tc-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tc-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    tcFilter = btn.dataset.tc;
    buildKpis();
    buildChart();
    buildChartPctConv();
    buildTabelaPerda();
    buildChartComunicacoes();
    buildChartDistribuicao();
    buildChartConvRates();
    renderTabela();
  });
});

// ---- KPIs ----
function buildKpis() {
  const totalInc = DATA.reduce((s,r) => s + incVal(r), 0);
  const totalShown = DATA.reduce((s,r) => s + r.shown, 0);
  const incMkt = DATA.filter(r => r.canal === 'MKT').reduce((s,r) => s + incVal(r), 0);
  const incAuto = DATA.filter(r => r.canal === 'AUTOMATIZADA').reduce((s,r) => s + incVal(r), 0);

  const cards = [
    { label: 'Incremental total (Jan-Ago)', value: fmtInt(totalInc), sub: new Set(DATA.map(r => r.campanha)).size + ' campanhas com grupo controle', cls: '' },
    { label: 'Incremental via Automatizada', value: fmtInt(incAuto), sub: (100*incAuto/totalInc).toFixed(1) + '% do total', cls: '' },
    { label: 'Incremental via MKT', value: fmtInt(incMkt), sub: (100*incMkt/totalInc).toFixed(1) + '% do total', cls: 'purple' },
    { label: 'Total exposto (shown, acao)', value: fmtInt(totalShown), sub: 'base de usuarios que viram alguma comunicacao', cls: '' },
  ];
  document.getElementById('kpiGrid').innerHTML = cards.map(c => `
    <div class="kpi-card ${c.cls}">
      <div class="kpi-label">${c.label}</div>
      <div class="kpi-value">${c.value}</div>
      <div class="kpi-sub">${c.sub}</div>
    </div>
  `).join('');
}

// ---- Chart: incremental por canal, mes a mes (2 vias: Automatizada / MKT) ----
let chartMode = 'abs';
let chartCanal = null;

function buildChart() {
  const byMonth = { MKT: [], AUTOMATIZADA: [] };
  MESES.forEach(m => {
    const incMkt = DATA.filter(r => r.mes === m && r.canal === 'MKT').reduce((s,r) => s + incVal(r), 0);
    const incAuto = DATA.filter(r => r.mes === m && r.canal === 'AUTOMATIZADA').reduce((s,r) => s + incVal(r), 0);
    if (chartMode === 'pct') {
      const total = incMkt + incAuto;
      byMonth.MKT.push(total ? 100 * incMkt / total : 0);
      byMonth.AUTOMATIZADA.push(total ? 100 * incAuto / total : 0);
    } else {
      byMonth.MKT.push(Math.round(incMkt));
      byMonth.AUTOMATIZADA.push(Math.round(incAuto));
    }
  });

  const cfg = {
    type: 'bar',
    data: {
      labels: MESES.map(mesLabel),
      datasets: [
        { label: 'Automatizada', data: byMonth.AUTOMATIZADA, backgroundColor: '#009ee3', stack: 's' },
        { label: 'MKT', data: byMonth.MKT, backgroundColor: '#6c47c9', stack: 's' },
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
        datalabels: {
          color: '#fff', font: { weight: 700, size: 10 },
          formatter: v => chartMode === 'pct' ? (v ? v.toFixed(0)+'%' : '') : (v ? v.toLocaleString('pt-BR') : '')
        }
      },
      scales: {
        x: { stacked: true },
        y: { stacked: true, ticks: { callback: v => chartMode === 'pct' ? v+'%' : v.toLocaleString('pt-BR') } }
      }
    },
    plugins: [ChartDataLabels]
  };

  if (chartCanal) chartCanal.destroy();
  chartCanal = new Chart(document.getElementById('chartCanal'), cfg);
}

document.querySelectorAll('.toggle-pct[data-mode="abs"], .toggle-pct[data-mode="pct"]').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.toggle-pct[data-mode="abs"], .toggle-pct[data-mode="pct"]').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    chartMode = btn.dataset.mode;
    buildChart();
  });
});

// ---- Chart: incremental como % do total de conversoes do mes (linha) ----
let chartPctConv = null;

function buildChartPctConv() {
  const pctAuto = [], pctMkt = [], pctTotal = [];
  MESES.forEach(m => {
    const incMkt = DATA.filter(r => r.mes === m && r.canal === 'MKT').reduce((s,r) => s + incVal(r), 0);
    const incAuto = DATA.filter(r => r.mes === m && r.canal === 'AUTOMATIZADA').reduce((s,r) => s + incVal(r), 0);
    const denom = totalConvVal(m);
    pctAuto.push(denom ? 100 * incAuto / denom : 0);
    pctMkt.push(denom ? 100 * incMkt / denom : 0);
    pctTotal.push(denom ? 100 * (incAuto + incMkt) / denom : 0);
  });

  const cfg = {
    type: 'line',
    data: {
      labels: MESES.map(mesLabel),
      datasets: [
        { label: 'Total', data: pctTotal, borderColor: '#333', backgroundColor: '#333', tension: .2, borderWidth: 2.5 },
        { label: 'Automatizada', data: pctAuto, borderColor: '#009ee3', backgroundColor: '#009ee3', tension: .2 },
        { label: 'MKT', data: pctMkt, borderColor: '#6c47c9', backgroundColor: '#6c47c9', tension: .2 },
      ]
    },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
        datalabels: {
          align: 'top', color: '#555', font: { weight: 700, size: 10 },
          formatter: v => v.toFixed(1) + '%'
        }
      },
      scales: {
        y: { ticks: { callback: v => v + '%' } }
      }
    },
    plugins: [ChartDataLabels]
  };

  if (chartPctConv) chartPctConv.destroy();
  chartPctConv = new Chart(document.getElementById('chartPctConv'), cfg);
}

// ---- Tabela: conversoes perdidas vs base Fev-Abr ----
// Jan excluido da base -- teve um pico pontual de MKT ("MASSIVA") que nao se repete, inflaria a
// meta. Meta = % incremental ponderado por volume (soma incremental Fev-Abr / soma conversoes
// Fev-Abr) -- dinamica, recalcula com o filtro de Tipo TC. Assume que a conversao ORGANICA
// (nao-incremental) fica constante e so a incremental muda -- por isso a meta% se aplica sobre o
// TOTAL NECESSARIO, nao sobre o total atual direto (ver nota no card). Arredonda pra cima.
const MESES_BASE = MESES.slice(1, 4); // Fev-Abr (Jan excluido)

function buildTabelaPerda() {
  const porMes = MESES.map(m => {
    const incAuto = DATA.filter(r => r.mes === m && r.canal === 'AUTOMATIZADA').reduce((s,r) => s + incVal(r), 0);
    const incMkt = DATA.filter(r => r.mes === m && r.canal === 'MKT').reduce((s,r) => s + incVal(r), 0);
    const incTotal = incAuto + incMkt;
    const totalConv = totalConvVal(m);
    const pct = totalConv ? incTotal / totalConv : 0;
    return { mes: m, incTotal, totalConv, pct };
  });

  const baseRows = porMes.filter(r => MESES_BASE.includes(r.mes));
  const incBase = baseRows.reduce((s,r) => s + r.incTotal, 0);
  const convBase = baseRows.reduce((s,r) => s + r.totalConv, 0);
  const metaMedia = convBase ? incBase / convBase : 0;

  const tbody = document.getElementById('tblPerdaBody');
  tbody.innerHTML = porMes.map(r => {
    const isBase = MESES_BASE.includes(r.mes);
    if (isBase) {
      return `
      <tr style="background:#f0f6fb;">
        <td>${mesLabel(r.mes)}</td>
        <td>${(r.pct * 100).toFixed(1)}% <span class="badge" style="background:#009ee3; font-size:9px;">BASE FEV-ABR</span></td>
        <td>${fmtInt(r.totalConv)}</td>
        <td>${fmtInt(r.incTotal)}</td>
        <td>-</td><td><span style="color:#ccc;">base</span></td>
      </tr>`;
    }
    const baseOrganica = r.totalConv - r.incTotal;
    const totalNecessario = Math.ceil(baseOrganica / (1 - metaMedia));
    const perda = totalNecessario - r.totalConv;
    const perdaTxt = perda !== 0 ? (perda > 0 ? '-' : '+') + fmtInt(Math.abs(perda)) : '-';
    const perdaCls = perda > 0 ? 'neg' : (perda < 0 ? 'pos' : '');
    return `
    <tr>
      <td>${mesLabel(r.mes)}</td>
      <td>${(r.pct * 100).toFixed(1)}%</td>
      <td>${fmtInt(r.totalConv)}</td>
      <td>${fmtInt(r.incTotal)}</td>
      <td>${(metaMedia * 100).toFixed(1)}%</td>
      <td class="${perdaCls}" style="font-weight:700;">${perdaTxt}</td>
    </tr>`;
  }).join('');
}

// ---- Chart: comunicacoes por proposta, por safra de encendido (janela fixa D0-D30) ----
// COMUNIC_DATA: [{ mes, flag_tc, qtd_propostas, avg_comunicacoes, mediana_comunicacoes, qtd_zero }]
// Respeita o filtro global de Tipo TC (Full/Micro/Todos) igual ao resto do dashboard.
let chartComunicacoes = null;

function buildChartComunicacoes() {
  const mesesComunic = [...new Set(COMUNIC_DATA.map(r => r.mes))].sort();
  const seriesFull = mesesComunic.map(m => {
    const r = COMUNIC_DATA.find(x => x.mes === m && x.flag_tc === '1. TC Full');
    return r ? r.avg_comunicacoes : null;
  });
  const seriesMicro = mesesComunic.map(m => {
    const r = COMUNIC_DATA.find(x => x.mes === m && x.flag_tc === '2. Micro TC');
    return r ? r.avg_comunicacoes : null;
  });
  const seriesTotal = mesesComunic.map(m => {
    const rows = COMUNIC_DATA.filter(x => x.mes === m);
    const props = rows.reduce((s, x) => s + x.qtd_propostas, 0);
    const total = rows.reduce((s, x) => s + x.avg_comunicacoes * x.qtd_propostas, 0);
    return props ? +(total / props).toFixed(2) : null;
  });

  const datasets = [];
  if (tcFilter === 'TODOS' || tcFilter === 'FULL') datasets.push({ label: 'TC Full', data: seriesFull, borderColor: '#009ee3', backgroundColor: '#009ee3', tension: .2 });
  if (tcFilter === 'TODOS' || tcFilter === 'MICRO') datasets.push({ label: 'Micro TC', data: seriesMicro, borderColor: '#ff7733', backgroundColor: '#ff7733', tension: .2 });
  if (tcFilter === 'TODOS') datasets.push({ label: 'Total', data: seriesTotal, borderColor: '#333', backgroundColor: '#333', tension: .2, borderWidth: 2.5 });

  const cfg = {
    type: 'line',
    data: { labels: mesesComunic.map(mesLabel), datasets },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top' },
        datalabels: { align: 'top', color: '#555', font: { weight: 700, size: 10 }, formatter: v => v != null ? v.toFixed(1) : '' }
      },
      scales: { y: { title: { display: true, text: 'Comunicacoes por proposta (media)' } } }
    },
    plugins: [ChartDataLabels]
  };

  if (chartComunicacoes) chartComunicacoes.destroy();
  chartComunicacoes = new Chart(document.getElementById('chartComunicacoes'), cfg);
}

// ---- Chart: distribuicao de comunicacoes por proposta ACEITA (barras 100% empilhadas por safra) ----
// DIST_DATA: [{ mes, flag_tc, flag_populacao, bucket, bucket_ord, qtd_propostas }]
// So olha flag_populacao === 'Aceitas' (propostas com status accepted) -- a populacao 'Todos'
// tambem vem no mesmo dado (calculada na mesma passada da query, sem custo extra) mas nao e usada
// aqui, esse grafico foi substituido pra focar em quem converteu.
// Buckets = progressao ordenada -- cor sequencial (claro->escuro), nao categorica.
const BUCKET_ORDER = ['0','1','2','3','4','5','6','7','8','9','10+'];
// rampa sequencial de 1 hue (azul do dashboard), clara -> escura
const BUCKET_COLORS = ['#e8f6fd','#c9ecfa','#a3dff5','#7ad0ef','#4fc0e8','#009ee3','#0084bd','#006a97','#005071','#00374d','#001c28'];
// Modo "por faixa": agrupa bucket_ord em faixas mais largas pra leitura rapida.
const RANGE_BUCKETS = [
  { key: '0', label: '0 (nenhuma)', min: 0, max: 0 },
  { key: '1-3', label: '1-3', min: 1, max: 3 },
  { key: '4-6', label: '4-6', min: 4, max: 6 },
  { key: '7-9', label: '7-9', min: 7, max: 9 },
  { key: '10+', label: '10+', min: 10, max: Infinity }
];
const RANGE_COLORS = ['#e8f6fd','#7ad0ef','#009ee3','#005071','#001c28'];
let chartDistribuicao = null;
let distBucketMode = 'granular';

let distPopulacao = 'Aceitas';
let distValueMode = 'pct';

function buildChartDistribuicao() {
  const tcVals = tcFilter === 'FULL' ? ['1. TC Full'] : (tcFilter === 'MICRO' ? ['2. Micro TC'] : ['1. TC Full', '2. Micro TC']);
  const rows = DIST_DATA.filter(r => tcVals.includes(r.flag_tc) && r.flag_populacao === distPopulacao);
  const mesesDist = [...new Set(rows.map(r => r.mes))].sort();

  const buckets = distBucketMode === 'faixa' ? RANGE_BUCKETS : BUCKET_ORDER.map(b => ({ key: b, label: b === '0' ? '0 (nenhuma)' : b }));
  const colors = distBucketMode === 'faixa' ? RANGE_COLORS : BUCKET_COLORS;

  // soma qtd_propostas por (mes, bucket-ou-faixa) entre os FLAG_TC selecionados
  const porMesBucket = {};
  mesesDist.forEach(m => { porMesBucket[m] = {}; buckets.forEach(b => porMesBucket[m][b.key] = 0); });
  rows.forEach(r => {
    const key = distBucketMode === 'faixa'
      ? RANGE_BUCKETS.find(rb => r.bucket_ord >= rb.min && r.bucket_ord <= rb.max).key
      : r.bucket;
    porMesBucket[r.mes][key] = (porMesBucket[r.mes][key] || 0) + r.qtd_propostas;
  });

  const isAbs = distValueMode === 'abs';
  const datasets = buckets.map((b, i) => ({
    label: b.label,
    data: mesesDist.map(m => {
      if (isAbs) return porMesBucket[m][b.key];
      const total = buckets.reduce((s, bb) => s + porMesBucket[m][bb.key], 0);
      return total ? +(100 * porMesBucket[m][b.key] / total).toFixed(1) : 0;
    }),
    backgroundColor: colors[i],
    stack: 's'
  }));

  const t = document.getElementById('distTitle');
  const sub = document.getElementById('distSub');
  const popLabel = distPopulacao === 'Aceitas' ? 'ACEITA' : '(TODOS OS STATUS)';
  t.textContent = `Distribuicao de comunicacoes por proposta ${popLabel} -- por safra de criacao`;
  sub.textContent = distPopulacao === 'Aceitas'
    ? "Apenas propostas com status aceito (CCARD_PROP_STATUS='accepted'), por safra de criacao (= mesma data de encendido). Mostra se a queda da media e um deslocamento geral ou uma polarizacao, especificamente entre quem converteu."
    : 'Todas as propostas (aceitas, canceladas, pendentes), por safra de criacao -- referencia pra comparar contra o corte de aceitas ao lado.';

  const darkFromIdx = Math.ceil(buckets.length * 0.55);
  const cfg = {
    type: 'bar',
    data: { labels: mesesDist.map(mesLabel), datasets },
    options: {
      responsive: true,
      plugins: {
        legend: { position: 'top', labels: { boxWidth: 12, font: { size: 10 } } },
        datalabels: {
          color: c => (buckets.findIndex(b => b.label === c.dataset.label) >= darkFromIdx ? '#fff' : '#333'),
          font: { weight: 700, size: 9 },
          formatter: v => {
            if (isAbs) return v > 0 ? v.toLocaleString('pt-BR') : '';
            return v >= 5 ? v.toFixed(0) + '%' : '';
          }
        }
      },
      scales: {
        x: { stacked: true },
        y: isAbs
          ? { stacked: true, ticks: { callback: v => v.toLocaleString('pt-BR') } }
          : { stacked: true, max: 100, ticks: { callback: v => v + '%' } }
      }
    },
    plugins: [ChartDataLabels]
  };

  if (chartDistribuicao) chartDistribuicao.destroy();
  chartDistribuicao = new Chart(document.getElementById('chartDistribuicao'), cfg);
}

// Paletas de linha -- mesma progressao sequencial (claro->escuro = poucas->muitas
// comunicacoes) das barras acima, mas com piso de luminosidade mais alto: as cores
// mais claras da rampa de barra (ex #e8f6fd) ficam quase invisiveis como traco de
// linha sobre fundo branco.
const LINE_BUCKET_COLORS = ['#b8e4f5','#93d6ef','#6ec8e9','#4ab8e2','#26a6d6','#009ee3','#0084bd','#006a97','#005071','#00374d','#001c28'];
const LINE_RANGE_COLORS = ['#93d6ef','#4ab8e2','#009ee3','#005071','#001c28'];
let chartConvRateBucket = null;
let chartConvShareTotal = null;
let convBucketMode = 'granular';

// ---- 2 graficos de linha (toggle Granular/Faixa proprio, independente do grafico de
// distribuicao acima), respondendo perguntas diferentes com o mesmo dado base (Todos x
// Aceitas por bucket):
//  1) % de conversao DENTRO do grupo -- aceitas_bucket / todos_bucket. Ex: de quem nao
//     recebeu nenhuma comunicacao, quantos % converteram -- e essa taxa esta subindo/caindo?
//  2) % do TOTAL ENCENDIDO do mes que converteu tendo recebido N comunicacoes -- decompoe a
//     taxa de conversao geral em quanto vem de cada faixa de comunicacao.
function buildChartConvRates() {
  const tcVals = tcFilter === 'FULL' ? ['1. TC Full'] : (tcFilter === 'MICRO' ? ['2. Micro TC'] : ['1. TC Full', '2. Micro TC']);
  const rows = DIST_DATA.filter(r => tcVals.includes(r.flag_tc));
  const mesesDist = [...new Set(rows.map(r => r.mes))].sort();

  const buckets = convBucketMode === 'faixa' ? RANGE_BUCKETS : BUCKET_ORDER.map(b => ({ key: b, label: b === '0' ? '0 (nenhuma)' : b }));
  const colors = convBucketMode === 'faixa' ? LINE_RANGE_COLORS : LINE_BUCKET_COLORS;

  const porMesBucketPop = {};
  mesesDist.forEach(m => {
    porMesBucketPop[m] = {};
    buckets.forEach(b => { porMesBucketPop[m][b.key] = { Todos: 0, Aceitas: 0 }; });
  });
  rows.forEach(r => {
    const key = convBucketMode === 'faixa'
      ? RANGE_BUCKETS.find(rb => r.bucket_ord >= rb.min && r.bucket_ord <= rb.max).key
      : r.bucket;
    porMesBucketPop[r.mes][key][r.flag_populacao] += r.qtd_propostas;
  });

  const totalEncendidoMes = {};
  mesesDist.forEach(m => { totalEncendidoMes[m] = buckets.reduce((s, b) => s + porMesBucketPop[m][b.key].Todos, 0); });

  const mkDatasets = (valueFn) => buckets.map((b, i) => ({
    label: b.label,
    data: mesesDist.map(m => valueFn(porMesBucketPop[m][b.key], totalEncendidoMes[m])),
    borderColor: colors[i], backgroundColor: colors[i], borderWidth: 2.5, pointRadius: 3, tension: .15, fill: false, spanGaps: true
  }));

  const datasetsRate = mkDatasets((g) => g.Todos ? +(100 * g.Aceitas / g.Todos).toFixed(1) : null);
  const datasetsShare = mkDatasets((g, total) => total ? +(100 * g.Aceitas / total).toFixed(1) : null);

  const lineOpts = {
    responsive: true,
    plugins: {
      legend: { position: 'top', labels: { boxWidth: 12, font: { size: 9 } } },
      datalabels: { display: false }
    },
    scales: { y: { ticks: { callback: v => v + '%' } } }
  };

  if (chartConvRateBucket) chartConvRateBucket.destroy();
  chartConvRateBucket = new Chart(document.getElementById('chartConvRateBucket'), {
    type: 'line', data: { labels: mesesDist.map(mesLabel), datasets: datasetsRate }, options: lineOpts
  });

  if (chartConvShareTotal) chartConvShareTotal.destroy();
  chartConvShareTotal = new Chart(document.getElementById('chartConvShareTotal'), {
    type: 'line', data: { labels: mesesDist.map(mesLabel), datasets: datasetsShare }, options: lineOpts
  });
}

// ---- Tabela pivot: campanha x mes, abs + % do mes (dentro do canal filtrado) ----
// Campanhas Eldorado (cupom 20/35/50/70/100%) sao agregadas numa unica linha "ELDORADO" --
// substitui o nome da campanha, canal continua o que já era (normalmente Automatizada).
//
// Jornada: campanhas "flows_communication_..._mer_XXX" (e variantes "flows_..._mer_XXX") sao
// testes A/B do mesmo fluxo -- a jornada é o nome sem o sufixo "_mer_XXX" (mesma regra ja usada
// no dash_encendidos_v3 pra agrupar essas variantes). No modo "Por jornada", agrupa todas as
// variantes numa unica linha; no modo "Por campanha" (default), mostra cada variante separada.
const canalSelect = document.getElementById('canalSelect');
const btnPorCampanha = document.getElementById('btnPorCampanha');
const btnPorJornada = document.getElementById('btnPorJornada');
let viewMode = 'campanha';

function journeyKey(campanha) {
  return campanha.replace(/_mer_[a-z0-9]{2,5}$/i, '');
}

const theadRow = document.getElementById('tblCampanhasHead');
theadRow.innerHTML = '<th>Campanha</th>' +
  MESES.map(m => `<th>${mesLabel(m)}</th>`).join('') +
  '<th>Total</th>';

function renderTabela() {
  const canal = canalSelect.value;
  let rows = DATA;
  if (canal !== 'TODOS') rows = rows.filter(r => r.canal === canal);

  // pivot: 1 linha por campanha ou por jornada (Eldorado sempre colapsa numa unica linha
  // "ELDORADO", independente do modo), 1 coluna por mes
  const porCampanha = {};
  rows.forEach(r => {
    const key = r.eldorado ? 'ELDORADO' : (viewMode === 'jornada' ? journeyKey(r.campanha) : r.campanha);
    if (!porCampanha[key]) porCampanha[key] = { campanha: key, canal: r.canal, eldorado: r.eldorado, porMes: {}, total: 0, variantes: new Set() };
    const v = incVal(r);
    porCampanha[key].porMes[r.mes] = (porCampanha[key].porMes[r.mes] || 0) + v;
    porCampanha[key].total += v;
    porCampanha[key].variantes.add(r.campanha);
  });
  const list = Object.values(porCampanha).sort((a,b) => b.total - a.total);

  // total do MES (denominador do % por celula), dentro do canal filtrado
  const totalPorMes = {};
  MESES.forEach(m => {
    totalPorMes[m] = rows.filter(r => r.mes === m).reduce((s,r) => s + incVal(r), 0);
  });

  const tbody = document.querySelector('#tblCampanhas tbody');
  tbody.innerHTML = list.map(r => {
    const cols = MESES.map(m => {
      const v = r.porMes[m];
      if (v === undefined) return '<td style="color:#ccc;">-</td>';
      const cls = v >= 0 ? 'pos' : 'neg';
      const denom = totalPorMes[m];
      const pct = denom ? (100 * v / denom).toFixed(1) + '%' : '-';
      return `<td class="${cls}"><span class="abs">${fmtInt(v)}</span><span class="pct">${pct}</span></td>`;
    }).join('');
    const badge = r.eldorado ? `<span class="badge ELDORADO" style="font-size:9px;">ELDORADO</span>` : `<span class="badge ${r.canal}" style="font-size:9px;">${r.canal}</span>`;
    const qtdVariantes = r.variantes.size;
    const variantesBadge = qtdVariantes > 1 ? `<span class="badge" style="font-size:9px; background:#888;">${qtdVariantes} variantes</span>` : '';
    const tooltip = qtdVariantes > 1 ? Array.from(r.variantes).join(', ') : r.campanha;
    return `
    <tr>
      <td title="${tooltip}">${r.campanha} ${badge} ${variantesBadge}</td>
      ${cols}
      <td style="font-weight:700;" class="${r.total >= 0 ? 'pos' : 'neg'}"><span class="abs">${fmtInt(r.total)}</span></td>
    </tr>`;
  }).join('');
}

canalSelect.addEventListener('change', renderTabela);
[btnPorCampanha, btnPorJornada].forEach(btn => {
  btn.addEventListener('click', () => {
    [btnPorCampanha, btnPorJornada].forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    viewMode = btn.dataset.mode;
    renderTabela();
  });
});

const btnDistGranular = document.getElementById('btnDistGranular');
const btnDistFaixa = document.getElementById('btnDistFaixa');
[btnDistGranular, btnDistFaixa].forEach(btn => {
  btn.addEventListener('click', () => {
    [btnDistGranular, btnDistFaixa].forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    distBucketMode = btn.dataset.mode;
    buildChartDistribuicao();
  });
});

const btnPopAceitas = document.getElementById('btnPopAceitas');
const btnPopTodos = document.getElementById('btnPopTodos');
[btnPopAceitas, btnPopTodos].forEach(btn => {
  btn.addEventListener('click', () => {
    [btnPopAceitas, btnPopTodos].forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    distPopulacao = btn.dataset.mode;
    buildChartDistribuicao();
  });
});

const btnDistPct = document.getElementById('btnDistPct');
const btnDistAbs = document.getElementById('btnDistAbs');
[btnDistPct, btnDistAbs].forEach(btn => {
  btn.addEventListener('click', () => {
    [btnDistPct, btnDistAbs].forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    distValueMode = btn.dataset.mode;
    buildChartDistribuicao();
  });
});

const btnConvGranular = document.getElementById('btnConvGranular');
const btnConvFaixa = document.getElementById('btnConvFaixa');
[btnConvGranular, btnConvFaixa].forEach(btn => {
  btn.addEventListener('click', () => {
    [btnConvGranular, btnConvFaixa].forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    convBucketMode = btn.dataset.mode;
    buildChartConvRates();
  });
});

buildKpis();
buildChart();
buildChartPctConv();
buildTabelaPerda();
buildChartComunicacoes();
buildChartDistribuicao();
buildChartConvRates();
renderTabela();
</script>

</body>
</html>
"""

html = html.replace("__DATA_JS__", DATA_JS)
html = html.replace("__TOTAL_CONV_JS__", TOTAL_CONV_JS)
html = html.replace("__COMUNIC_JS__", COMUNIC_JS)
html = html.replace("__DIST_JS__", DIST_JS)

with open('dash_incremental_por_canal.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("OK", len(html), "bytes")
