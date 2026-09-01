import json

D = json.load(open('historia_data.json', encoding='utf-8'))
DATA_JS = json.dumps(D, ensure_ascii=False)

html = r"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A História da Queda de Comunicação em TC</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@2.2.0/dist/chartjs-plugin-datalabels.min.js"></script>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  html, body { width: 100%; height: 100%; overflow: hidden; font-family: 'Segoe UI', Arial, sans-serif; background: #0d1117; color: #222; }

  .topbar {
    position: fixed; top: 0; left: 0; right: 0; height: 64px; z-index: 50;
    background: linear-gradient(135deg, #009ee3 0%, #00c1df 100%);
    display: flex; align-items: center; justify-content: space-between;
    padding: 0 24px; color: white; gap: 16px;
  }
  .topbar .title { font-size: 17px; font-weight: 700; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
  .topbar .controls { display: flex; align-items: center; gap: 20px; flex-shrink: 0; }
  .toggle-group { display: flex; gap: 8px; align-items: center; }
  .toggle-group .glabel { font-size: 12px; opacity: .85; margin-right: 2px; }
  .tc-btn, .lang-btn {
    padding: 7px 18px; border: 2px solid rgba(255,255,255,.6); border-radius: 8px;
    font-size: 14px; font-weight: 700; cursor: pointer; background: transparent; color: white;
    transition: all .15s;
  }
  .tc-btn.active, .lang-btn.active { background: white; color: #009ee3; border-color: white; }
  .topbar .counter { font-size: 14px; opacity: .85; flex-shrink: 0; }

  .slides { position: fixed; top: 64px; left: 0; right: 0; bottom: 56px; }
  .slide {
    display: none; position: absolute; inset: 0; overflow-y: auto;
    background: #f4f5f7; padding: 44px 72px 30px;
    flex-direction: column;
  }
  .slide.active { display: flex; }

  .slide h1 { font-size: 40px; font-weight: 800; color: #17384d; margin-bottom: 6px; line-height: 1.15; }
  .slide .kicker { font-size: 16px; font-weight: 700; color: #009ee3; text-transform: uppercase; letter-spacing: .6px; margin-bottom: 10px; }
  .slide .lead { font-size: 21px; color: #444; margin-bottom: 22px; line-height: 1.4; max-width: 1200px; }
  .slide .body-text { font-size: 19px; color: #333; line-height: 1.55; max-width: 1100px; }
  .slide .body-text b { color: #005a80; }
  .slide .body-text.warn { color: #a35400; }

  .chart-wrap { flex: 1; min-height: 0; display: flex; flex-direction: column; }
  .chart-wrap canvas { max-height: 100%; }
  .two-col { display: flex; gap: 30px; flex: 1; min-height: 0; }
  .two-col > div { flex: 1; display: flex; flex-direction: column; min-height: 0; }

  .note-box {
    font-size: 16px; color: #a35400; background: #fff8ec; border-left: 4px solid #ffb020;
    padding: 12px 18px; border-radius: 6px; margin-top: 14px; line-height: 1.5;
  }
  .highlight-box {
    font-size: 20px; color: #17384d; background: white; border-left: 6px solid #009ee3;
    padding: 18px 26px; border-radius: 8px; margin-top: 18px; box-shadow: 0 2px 10px rgba(0,0,0,.08);
    line-height: 1.5;
  }
  .link-box {
    font-size: 20px; background: white; border-radius: 10px; padding: 26px 32px;
    box-shadow: 0 2px 14px rgba(0,0,0,.1); margin-top: 20px; display: inline-block;
  }
  .link-box a { color: #009ee3; font-weight: 700; word-break: break-all; }

  .story-tbl-wrap { background: white; border-radius: 10px; box-shadow: 0 2px 12px rgba(0,0,0,.1); border-left: 6px solid #a3001a; overflow: hidden; margin-top: 14px; }
  table.story-tbl { width: 100%; border-collapse: collapse; font-size: 18px; }
  table.story-tbl th, table.story-tbl td { padding: 12px 14px; text-align: center; border-bottom: 1px solid #e5e8eb; white-space: nowrap; }
  table.story-tbl th { background: #eef5fa; color: #444; font-weight: 700; }
  table.story-tbl td:first-child, table.story-tbl th:first-child { text-align: right; font-weight: 700; padding-right: 20px; width: 1%; white-space: nowrap; }
  table.story-tbl td:not(:first-child), table.story-tbl th:not(:first-child) { width: 16%; }
  table.story-tbl td.neg { color: #a3001a; font-weight: 800; }
  table.story-tbl td.pos { color: #00723a; font-weight: 800; }
  table.story-tbl th.total-col, table.story-tbl td.total-col { width: 22%; background: #fdecea; font-size: 26px; font-weight: 900; }
  table.story-tbl th.total-col { background: #a3001a; color: white; font-size: 16px; }

  .cover { align-items: center; justify-content: center; text-align: center; background: linear-gradient(135deg, #0d1117 0%, #17384d 100%); }
  .cover h1 { color: white; font-size: 56px; margin-bottom: 24px; }
  .cover .lead { color: #b8d4e3; font-size: 24px; max-width: 900px; }
  .cover .kicker { color: #4fc0e8; }

  .bottombar {
    position: fixed; bottom: 0; left: 0; right: 0; height: 56px;
    background: white; border-top: 1px solid #e5e8eb;
    display: flex; align-items: center; justify-content: center; gap: 18px;
  }
  .nav-btn {
    padding: 8px 20px; border: none; border-radius: 8px; background: #009ee3; color: white;
    font-size: 15px; font-weight: 700; cursor: pointer;
  }
  .nav-btn:disabled { background: #ccc; cursor: default; }
  .dots { display: flex; gap: 8px; }
  .dot { width: 12px; height: 12px; border-radius: 50%; background: #d5dde3; cursor: pointer; }
  .dot.active { background: #009ee3; width: 28px; border-radius: 6px; }

  .badge { display: inline-block; padding: 3px 10px; border-radius: 10px; font-size: 13px; font-weight: 700; color: white; }
  .badge.full { background: #009ee3; }
  .badge.micro { background: #ff7733; }

  .bf-wrap { display: flex; flex-direction: column; }
  .bf-row { display: flex; align-items: center; width: 100%; }
  .bf-label { width: 260px; flex: 0 0 260px; text-align: right; padding-right: 12px; font-size: 19px; color: #666; line-height: 1.2; }
  .bf-funnel { flex: 1 1 auto; min-width: 0; display: flex; justify-content: center; }
  .bf-band { display: flex; align-items: center; justify-content: center; height: 44px; color: #fff; text-align: center; }
  .bf-band .val { font-size: 23px; font-weight: 800; white-space: nowrap; }
  .bf-drop { width: 120px; flex: 0 0 120px; display: flex; align-items: center; gap: 6px; padding-left: 8px; }
  .bf-drop-line { width: 10px; height: 1px; background: #ccc; flex-shrink: 0; }
  .bf-drop-badge { font-size: 18px; font-weight: 700; color: #B3261E; background: #FDECEA; border: 1px solid #F5C6C2; border-radius: 20px; padding: 3px 10px; white-space: nowrap; }
  .bf-drop-badge.pos { color: #1B5E20; background: #E8F5E9; border-color: #A5D6A7; }
  .bf-stats { margin-top: 10px; margin-left: 260px; margin-right: 120px; display: flex; gap: 16px; }
  .bf-final { flex: 1; background: white; border: 1px solid #D4BF00; border-radius: 10px; padding: 12px 10px; text-align: center; }
  .bf-final .big { font-size: 32px; font-weight: 900; color: #B8860B; }
  .bf-final .sub { font-size: 19px; color: #555; margin-top: 4px; line-height: 1.3; }
  .bf-kpi-row { display: flex; align-items: center; margin-top: 12px; width: 100%; }
  .bf-kpi-band { display: flex; align-items: center; justify-content: center; gap: 8px; height: 50px; width: 270px; background: linear-gradient(180deg,#FFE600,#D4BF00); border: 2px solid #B8860B; border-radius: 12px; box-shadow: 0 2px 8px rgba(212,191,0,.35); }
  .bf-kpi-band .val { font-size: 23px; font-weight: 900; color: #222; }
  .bf-kpi-band .icon { font-size: 23px; }
</style>
</head>
<body>

<div class="topbar">
  <div class="title" id="topbarTitleText"></div>
  <div class="controls">
    <div class="toggle-group">
      <span class="glabel">TIPO TC:</span>
      <button class="tc-btn active" data-tc="FULL">Full</button>
      <button class="tc-btn" data-tc="MICRO">Micro</button>
    </div>
    <div class="toggle-group">
      <span class="glabel">IDIOMA:</span>
      <button class="lang-btn active" data-lang="PT">PT-BR</button>
      <button class="lang-btn" data-lang="ES">ES-AR</button>
    </div>
  </div>
  <div class="counter" id="slideCounter">1 / 8</div>
</div>

<div class="slides" id="slidesContainer"></div>

<div class="bottombar">
  <button class="nav-btn" id="btnPrev">&larr; <span id="btnPrevText"></span></button>
  <div class="dots" id="dotsContainer"></div>
  <button class="nav-btn" id="btnNext"><span id="btnNextText"></span> &rarr;</button>
</div>

<script>
window.addEventListener('error', e => {
  const box = document.createElement('div');
  box.id = 'jsErrorBox';
  box.style = 'position:fixed;top:70px;left:20px;right:20px;background:#ffdddd;border:2px solid red;color:#900;padding:12px;z-index:999;font-size:14px;';
  box.textContent = 'JS ERROR: ' + e.message + ' @ ' + e.filename + ':' + e.lineno;
  document.body.appendChild(box);
});
const D = __DATA_JS__;
const MESES = ['202601','202602','202603','202604','202605','202606','202607','202608'];

// ================= I18N =================

const MES_LABELS = {
  PT: { '01':'Jan','02':'Fev','03':'Mar','04':'Abr','05':'Mai','06':'Jun','07':'Jul','08':'Ago' },
  ES: { '01':'Ene','02':'Feb','03':'Mar','04':'Abr','05':'May','06':'Jun','07':'Jul','08':'Ago' }
};

const I18N = {
  PT: {
    topbarTitle: 'A História da Queda de Comunicação em TC',
    navPrev: 'Anterior', navNext: 'Próxima',
    modelChangeLabel: 'mudança de modelo (mai/26)',
    antesLabel: v => `Antes (sem Fev): ${v}`,
    antesLabelPct: v => `Antes (Fev-Abr): ${v}%`,
    depoisLabel: (v, d) => `Depois: ${v} (${d >= 0 ? '+' : ''}${d}%)`,
    depoisLabelPct: (v, d) => `Depois: ${v}% (${d >= 0 ? '+' : ''}${d}%)`,
    s0: {
      kicker: 'TC Aquisição -- Retrospectiva',
      h1: 'Por que a comunicação com o usuário caiu -- e o que isso custou',
      lead: 'Uma investigação que começou com uma queda no envio da comunicação D1 do encendido, e terminou gerando impacto em conversão, em volume incremental e no mix de usuários que trazemos pra dentro do produto.'
    },
    s1: {
      kicker: 'O Início',
      h1: 'Tudo começou quando percebemos que caiu o envio da nossa D1',
      lead: '% de encendidos (App Ativo = ML) que receberam a comunicação D1 -- primeira comunicação depois do encendido.',
      note: 'O padrão se repete em {FULL} e {MICRO}: estável em torno de 60-70% até junho/julho, e uma queda abrupta em ago/26 -- o primeiro sinal de que algo mudou na comunicação.'
    },
    s2: {
      kicker: 'A Investigação',
      h1: 'Isso levou à pesquisa da Bruna: por que esse envio está caindo?',
      body: 'Isso levou a Bruna a investigar por que esse envio estava caindo -- o comparativo de funis dela está abaixo (cobre só D1 Full -- ainda não tem visão de D1 Micro).',
      statBase: n => `da base inicial chega à audiência final entregável (${n})`,
      statCard: n => `da audiência final entregável vira cartão emitido (${n})`
    },
    s3: {
      kicker: 'Foi Além de D1',
      h1: 'Olhando o share de comunicação por safra de encendido',
      lead: '% Recebimento de Comunicação por Mês -- por App Ativo (Sem EA-MP, EA converte sem passar pelo funil).',
      velDeltaTitle: 'Total -- Antes (Jan,Mar-Mai) vs Agora (Jun+), Sem EA-MP',
      mecFull: 'Em <b>Full</b>, o que sustenta o share agregado é a D10 -- que <b>não</b> foi migrada pro flows, só teve a data alterada pra D7, e continua no sistema antigo. As comunicações que <b>não</b> foram migradas são o que puxa o número pra cima -- e isso mascara a queda real das que já foram pro flows.',
      mecMicro: 'Em <b>Micro</b>, a D6 nunca foi migrada pro flows -- continua no icamp, no sistema antigo. É exatamente essa comunicação que não migrou que está segurando o share pra cima.'
    },
    s4: {
      kicker: 'Quantificando',
      h1: 'Quanto isso significa em comunicações por usuário?',
      lead: 'Média de comunicações distintas (campanha+dia) por proposta, janela fixa D0..D30 pós-encendido.',
      note: 'Janela fixa pra não comparar safras com tempos diferentes de maturação. Ago/26 ainda não maturou (parcial).'
    },
    s5: {
      kicker: 'O Impacto Em $',
      h1: 'E aquela demora custou conversão',
      lead1: 'Incremental de aquisição de TC atribuível às comunicações, por mês',
      lead2: 'Incremental como % do total de conversões do mês',
      mesHeader: 'Mês',
      totalHeader: 'Total perdido até agora',
      perdaLabel: 'Perda estimada vs meta fev-abr ({PCT}%)'
    },
    s6: {
      kicker: 'Um Achado Paralelo',
      h1: 'No mesmo período, o mix de usuários também mudou',
      lead: 'Conversão por BU: Mercado Pago vs Mercado Livre (Sem EA, só canais Automatizada + MKT).',
      moveUpMarket: 'Trazer menos usuários via ML vai contra a estratégia de <b>move up market</b> -- sabemos historicamente que usuários ML são melhores que usuários MP.'
    },
    s7: {
      kicker: 'Pra Fechar',
      h1: 'O impacto real provavelmente é do mesmo tamanho nos dois -- só que em Full ele fica escondido',
      lead: 'Distribuição de comunicações por proposta (buckets de toques), Full e Micro sempre lado a lado nesse slide -- é o contraste entre os dois que é o ponto.',
      highlight: '{MICRO} não teve mudança de política de risco no período -- é a comparação mais limpa que temos entre safras, e mostra a erosão do grupo de alta frequência (10+ toques) de forma muito clara. <b>Full TC provavelmente sofreu um impacto do mesmo tamanho</b> -- só que fica disfarçado, porque mudanças de risco/elegibilidade no Full aconteceram no mesmo período e misturam o sinal.'
    },
    chart: {
      d1Full: 'D1 Full -- % enviado (ML)', d1Micro: 'D1 Micro -- % enviado (ML)',
      mercadoPago: 'Mercado Pago', mercadoLivre: 'Mercado Livre', semApp: 'Sem App Ativo',
      comunicMedia: 'Comunicações por proposta (média)', pctConv: '% do total de conversões',
      incremental: 'Incremental', antesLabel: 'Jan,Mar-Mai (sem Fev)', depoisLabel: 'Jun em diante'
    }
  },
  ES: {
    topbarTitle: 'La Historia de la Caída de Comunicación en TC',
    navPrev: 'Anterior', navNext: 'Siguiente',
    modelChangeLabel: 'cambio de modelo (may/26)',
    antesLabel: v => `Antes (sin Feb): ${v}`,
    antesLabelPct: v => `Antes (Feb-Abr): ${v}%`,
    depoisLabel: (v, d) => `Después: ${v} (${d >= 0 ? '+' : ''}${d}%)`,
    depoisLabelPct: (v, d) => `Después: ${v}% (${d >= 0 ? '+' : ''}${d}%)`,
    s0: {
      kicker: 'TC Adquisición -- Retrospectiva',
      h1: 'Por qué cayó la comunicación con el usuario -- y cuánto costó',
      lead: 'Una investigación que empezó con una caída en el envío de la comunicación D1 del encendido, y terminó generando impacto en conversión, en volumen incremental y en el mix de usuarios que traemos al producto.'
    },
    s1: {
      kicker: 'El Comienzo',
      h1: 'Todo empezó cuando notamos que cayó el envío de nuestra D1',
      lead: '% de encendidos (App Activa = ML) que recibieron la comunicación D1 -- primera comunicación después del encendido.',
      note: 'El patrón se repite en {FULL} y {MICRO}: estable alrededor de 60-70% hasta junio/julio, y una caída abrupta en ago/26 -- la primera señal de que algo cambió en la comunicación.'
    },
    s2: {
      kicker: 'La Investigación',
      h1: 'Esto llevó a la investigación de Bruna: ¿por qué está cayendo este envío?',
      body: 'Esto llevó a Bruna a investigar por qué estaba cayendo este envío -- el comparativo de funnels de ella está abajo (cubre solo D1 Full -- todavía no tiene visión de D1 Micro).',
      statBase: n => `de la base inicial llega a la audiencia final entregable (${n})`,
      statCard: n => `de la audiencia final entregable se convierte en tarjeta emitida (${n})`
    },
    s3: {
      kicker: 'Fue Más Allá de D1',
      h1: 'Mirando el share de comunicación por cohorte de encendido',
      lead: '% de Recepción de Comunicación por Mes -- por App Activa (Sin EA-MP, EA convierte sin pasar por el funnel).',
      velDeltaTitle: 'Total -- Antes (Ene,Mar-May) vs Ahora (Jun+), Sin EA-MP',
      mecFull: 'En <b>Full</b>, lo que sostiene el share agregado es la D10 -- que <b>no</b> fue migrada a flows, solo tuvo la fecha cambiada a D7, y sigue en el sistema anterior. Las comunicaciones que <b>no</b> fueron migradas son las que empujan el número para arriba -- y esto enmascara la caída real de las que ya migraron a flows.',
      mecMicro: 'En <b>Micro</b>, la D6 nunca fue migrada a flows -- sigue en icamp, en el sistema anterior. Es exactamente esa comunicación que no migró la que está manteniendo el share para arriba.'
    },
    s4: {
      kicker: 'Cuantificando',
      h1: '¿Cuánto significa esto en comunicaciones por usuario?',
      lead: 'Promedio de comunicaciones distintas (campaña+día) por propuesta, ventana fija D0..D30 post-encendido.',
      note: 'Ventana fija para no comparar cohortes con tiempos distintos de maduración. Ago/26 todavía no maduró (parcial).'
    },
    s5: {
      kicker: 'El Impacto en $',
      h1: 'Y esa demora costó conversión',
      lead1: 'Incremental de adquisición de TC atribuible a las comunicaciones, por mes',
      lead2: 'Incremental como % del total de conversiones del mes',
      mesHeader: 'Mes',
      totalHeader: 'Total perdido hasta ahora',
      perdaLabel: 'Pérdida estimada vs meta feb-abr ({PCT}%)'
    },
    s6: {
      kicker: 'Un Hallazgo Paralelo',
      h1: 'En el mismo período, el mix de usuarios también cambió',
      lead: 'Conversión por BU: Mercado Pago vs Mercado Libre (Sin EA, solo canales Automatizada + MKT).',
      moveUpMarket: 'Traer menos usuarios vía ML va en contra de la estrategia de <b>move up market</b> -- sabemos históricamente que los usuarios ML son mejores que los usuarios MP.'
    },
    s7: {
      kicker: 'Para Cerrar',
      h1: 'El impacto real probablemente es del mismo tamaño en los dos -- solo que en Full queda escondido',
      lead: 'Distribución de comunicaciones por propuesta (buckets de contactos), Full y Micro siempre lado a lado en esta diapositiva -- el contraste entre los dos es el punto.',
      highlight: '{MICRO} no tuvo cambios de política de riesgo en el período -- es la comparación más limpia que tenemos entre cohortes, y muestra la erosión del grupo de alta frecuencia (10+ contactos) de forma muy clara. <b>Full TC probablemente sufrió un impacto del mismo tamaño</b> -- solo que queda disfrazado, porque cambios de riesgo/elegibilidad en Full ocurrieron en el mismo período y mezclan la señal.'
    },
    chart: {
      d1Full: 'D1 Full -- % enviado (ML)', d1Micro: 'D1 Micro -- % enviado (ML)',
      mercadoPago: 'Mercado Pago', mercadoLivre: 'Mercado Libre', semApp: 'Sin App Activa',
      comunicMedia: 'Comunicaciones por propuesta (promedio)', pctConv: '% del total de conversiones',
      incremental: 'Incremental', antesLabel: 'Ene,Mar-May (sin Feb)', depoisLabel: 'Jun en adelante'
    }
  }
};

let lang = 'PT';
function L() { return I18N[lang]; }
function mesLabel(m) { return MES_LABELS[lang][m.slice(4,6)] + '/' + m.slice(2,4); }
function numLocale() { return lang === 'PT' ? 'pt-BR' : 'es-AR'; }
function fmtInt(n) { return Math.round(n).toLocaleString(numLocale()); }

let tcFilter = 'FULL';
const charts = {};
function upsertChart(id, cfg) {
  if (charts[id]) charts[id].destroy();
  charts[id] = new Chart(document.getElementById(id), cfg);
  requestAnimationFrame(() => requestAnimationFrame(() => { if (charts[id]) charts[id].resize(); }));
}

// Linha vertical leve marcando a mudanca de modelo (mai/26) -- usada em todo grafico
// mensal pra dar o mesmo ponto de referencia visual em qualquer slide.
const modelChangeLinePlugin = {
  id: 'modelChangeLine',
  afterDraw(chart, args, opts) {
    if (!opts || !opts.show) return;
    const xScale = chart.scales.x;
    if (!xScale) return;
    const before = opts.boundaryBefore;
    const x = (xScale.getPixelForValue(before - 1) + xScale.getPixelForValue(before)) / 2;
    const { top, bottom } = chart.chartArea;
    const ctx = chart.ctx;
    ctx.save();
    ctx.strokeStyle = 'rgba(200,30,30,.35)';
    ctx.lineWidth = 1.5;
    ctx.setLineDash([4, 4]);
    ctx.beginPath();
    ctx.moveTo(x, top);
    ctx.lineTo(x, bottom);
    ctx.stroke();
    if (opts.label) {
      ctx.setLineDash([]);
      ctx.fillStyle = 'rgba(170,30,30,.8)';
      ctx.font = "600 10px 'Segoe UI', sans-serif";
      ctx.textAlign = 'left';
      ctx.textBaseline = 'top';
      ctx.fillText(opts.label, x + 6, top + 6);
    }
    ctx.restore();
  }
};
function modelChangeOpts() { return { show: true, boundaryBefore: 4, label: L().modelChangeLabel }; }

// Linha horizontal tracejada mostrando a media de um intervalo de meses -- usada pra
// comparar "antes" vs "depois" da mudanca de modelo no mesmo grafico de linha.
const avgRangeLinePlugin = {
  id: 'avgRangeLine',
  afterDatasetsDraw(chart, args, opts) {
    if (!opts || !opts.ranges) return;
    const xScale = chart.scales.x, yScale = chart.scales.y;
    const ctx = chart.ctx;
    const half = (xScale.getPixelForValue(1) - xScale.getPixelForValue(0)) / 2;
    opts.ranges.forEach(r => {
      if (r.value == null) return;
      const y = yScale.getPixelForValue(r.value);
      const x1 = xScale.getPixelForValue(r.fromIdx) - half;
      const x2 = xScale.getPixelForValue(r.toIdx) + half;
      ctx.save();
      ctx.strokeStyle = r.color;
      ctx.lineWidth = 2.5;
      ctx.setLineDash([6, 4]);
      ctx.beginPath();
      ctx.moveTo(x1, y);
      ctx.lineTo(x2, y);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = r.color;
      ctx.font = "700 13px 'Segoe UI', sans-serif";
      ctx.textAlign = 'center';
      ctx.textBaseline = r.labelAbove ? 'bottom' : 'top';
      ctx.fillText(r.label, (x1 + x2) / 2, r.labelAbove ? y - 6 : y + 6);
      ctx.restore();
    });
  }
};

// ================= SLIDE DEFINITIONS =================

function slide0() {
  const t = L().s0;
  return `
  <div class="slide cover" id="slide-0">
    <div class="kicker">${t.kicker}</div>
    <h1>${t.h1}</h1>
    <div class="lead">${t.lead}</div>
  </div>`;
}

function slide1() {
  const t = L().s1;
  const note = t.note.replace('{FULL}', '<span class="badge full">Full</span>').replace('{MICRO}', '<span class="badge micro">Micro</span>');
  return `
  <div class="slide" id="slide-1">
    <div class="kicker">${t.kicker}</div>
    <h1>${t.h1}</h1>
    <div class="lead">${t.lead}</div>
    <div class="chart-wrap"><canvas id="chartD1"></canvas></div>
    <div class="highlight-box">${note}</div>
  </div>`;
}

function slide2() {
  const t = L().s2;
  return `
  <div class="slide" id="slide-2">
    <div class="kicker">${t.kicker}</div>
    <h1>${t.h1}</h1>
    <div class="body-text">${t.body}</div>
    <div class="chart-wrap" id="bfScaleWrap" style="position:relative;">
      <div class="two-col" id="bfContent" style="position:absolute; top:0; left:0; width:100%; transform-origin:top center;">
        <div><div class="lead" style="font-size:19px; margin-bottom:10px; margin-left:260px; margin-right:120px; text-align:center;">D1 - Mercurio 04/26</div><div class="bf-wrap" id="bf-mercurio"></div></div>
        <div><div class="lead" style="font-size:19px; margin-bottom:10px; margin-left:260px; margin-right:120px; text-align:center;">D1 - flows julho/2026</div><div class="bf-wrap" id="bf-flows"></div></div>
      </div>
    </div>
  </div>`;
}

function slide3() {
  const t = L().s3;
  return `
  <div class="slide" id="slide-3">
    <div class="kicker">${t.kicker}</div>
    <h1>${t.h1}</h1>
    <div class="lead">${t.lead}</div>
    <div class="two-col" style="flex: 1.4;">
      <div style="flex: 1.6;" class="chart-wrap"><canvas id="chartRecebimento"></canvas></div>
      <div><div class="lead" style="font-size:15px; margin-bottom:6px;">${t.velDeltaTitle}</div><div class="chart-wrap"><canvas id="chartVelDelta"></canvas></div></div>
    </div>
    <div class="highlight-box" id="mecanismoText"></div>
  </div>`;
}

function slide4() {
  const t = L().s4;
  return `
  <div class="slide" id="slide-4">
    <div class="kicker">${t.kicker}</div>
    <h1>${t.h1}</h1>
    <div class="lead">${t.lead}</div>
    <div class="chart-wrap"><canvas id="chartComunic"></canvas></div>
    <div class="note-box">${t.note}</div>
  </div>`;
}

function slide5() {
  const t = L().s5;
  return `
  <div class="slide" id="slide-5">
    <div class="kicker">${t.kicker}</div>
    <h1>${t.h1}</h1>
    <div class="two-col" style="flex: 1.3;">
      <div><div class="lead" style="font-size:17px; margin-bottom:6px;">${t.lead1}</div><div class="chart-wrap"><canvas id="chartIncTotal"></canvas></div></div>
      <div><div class="lead" style="font-size:17px; margin-bottom:6px;">${t.lead2}</div><div class="chart-wrap"><canvas id="chartIncPct"></canvas></div></div>
    </div>
    <div id="lossTableWrap"></div>
  </div>`;
}

function slide6() {
  const t = L().s6;
  return `
  <div class="slide" id="slide-6">
    <div class="kicker">${t.kicker}</div>
    <h1>${t.h1}</h1>
    <div class="lead">${t.lead}</div>
    <div class="chart-wrap"><canvas id="chartBU"></canvas></div>
    <div class="highlight-box">${t.moveUpMarket}</div>
  </div>`;
}

function slide7() {
  const t = L().s7;
  const highlight = t.highlight.replace('{MICRO}', '<span class="badge micro">Micro TC</span>');
  return `
  <div class="slide" id="slide-7">
    <div class="kicker">${t.kicker}</div>
    <h1>${t.h1}</h1>
    <div class="lead" style="font-size:16px;">${t.lead}</div>
    <div class="two-col">
      <div><canvas id="chartDistFinalFull"></canvas></div>
      <div><canvas id="chartDistFinalMicro"></canvas></div>
    </div>
    <div class="highlight-box">${highlight}</div>
  </div>`;
}

const SLIDES = [slide0, slide1, slide2, slide3, slide4, slide5, slide6, slide7];
let currentSlide = 0;

function renderSlides() {
  document.getElementById('slidesContainer').innerHTML = SLIDES.map(f => f()).join('');
  document.getElementById('dotsContainer').innerHTML = SLIDES.map((_, i) =>
    `<div class="dot${i===0?' active':''}" data-i="${i}"></div>`).join('');
  document.querySelectorAll('.dot').forEach(dot => {
    dot.addEventListener('click', () => goToSlide(+dot.dataset.i));
  });
}

function applyStaticText() {
  document.getElementById('topbarTitleText').textContent = L().topbarTitle;
  document.getElementById('btnPrevText').textContent = L().navPrev;
  document.getElementById('btnNextText').textContent = L().navNext;
}

function goToSlide(i) {
  if (i < 0 || i >= SLIDES.length) return;
  currentSlide = i;
  document.querySelectorAll('.slide').forEach((s, idx) => s.classList.toggle('active', idx === i));
  document.querySelectorAll('.dot').forEach((d, idx) => d.classList.toggle('active', idx === i));
  document.getElementById('slideCounter').textContent = (i+1) + ' / ' + SLIDES.length;
  document.getElementById('btnPrev').disabled = i === 0;
  document.getElementById('btnNext').disabled = i === SLIDES.length - 1;
  renderChartsForSlide(i);
}

document.getElementById('btnPrev').addEventListener('click', () => goToSlide(currentSlide - 1));
document.getElementById('btnNext').addEventListener('click', () => goToSlide(currentSlide + 1));
window.addEventListener('keydown', e => {
  if (e.key === 'ArrowRight') goToSlide(currentSlide + 1);
  if (e.key === 'ArrowLeft') goToSlide(currentSlide - 1);
});

document.querySelectorAll('.tc-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.tc-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    tcFilter = btn.dataset.tc;
    renderChartsForSlide(currentSlide);
  });
});

document.querySelectorAll('.lang-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    lang = btn.dataset.lang;
    applyStaticText();
    renderSlides();
    goToSlide(currentSlide);
  });
});

// ================= CHART RENDER FUNCTIONS =================

function renderChartsForSlide(i) {
  if (i === 1) renderD1();
  if (i === 2) renderBrunaFunnel();
  if (i === 3) { renderRecebimento(); renderVelDelta(); }
  if (i === 4) renderComunic();
  if (i === 5) { renderLossTable(); renderIncTotal(); renderIncPct(); }
  if (i === 6) renderBU();
  if (i === 7) renderDistFinal();
}

// ---- Slide 2: funil comparativo da Bruna (Mercurio 04/26 x flows julho/2026) --
// mesmos valores do documento dela (D1-Comparativo-de-Funis.html), reconstruidos
// como conteudo nativo do slide (nao mais iframe) pra ficar no mesmo tamanho de
// fonte do resto do deck, legivel em apresentacao.
function bfLerpColor(t) {
  const a = [42, 93, 176], b = [10, 22, 60];
  const c = a.map((v, i) => Math.round(v + (b[i] - v) * t));
  return `rgb(${c[0]}, ${c[1]}, ${c[2]})`;
}

function renderBfFunnel(containerId, stages, cardIssued) {
  const container = document.getElementById(containerId);
  container.innerHTML = '';

  // As linhas sao inseridas SEM largura definida pra banda -- so depois de estarem
  // no DOM (com o layout flex ja resolvido) medimos a largura REAL disponivel na
  // coluna do funil (.bf-funnel), que reflete o espaco de tela de verdade (nao um
  // valor fixo arbitrario). Isso garante que a barra sempre usa 100% do espaco
  // disponivel em qualquer resolucao, em vez de ficar presa a um tamanho de design.
  const rows = stages.map(s => {
    const row = document.createElement('div');
    row.className = 'bf-row';
    const label = document.createElement('div'); label.className = 'bf-label'; label.textContent = s.label;
    const funnelCol = document.createElement('div'); funnelCol.className = 'bf-funnel';
    const band = document.createElement('div'); band.className = 'bf-band';
    band.innerHTML = `<div class="val">${Math.round(s.value).toLocaleString(numLocale())}</div>`;
    funnelCol.appendChild(band);
    const drop = document.createElement('div'); drop.className = 'bf-drop';
    row.appendChild(label); row.appendChild(funnelCol); row.appendChild(drop);
    container.appendChild(row);
    return { band, drop, s };
  });

  const total = stages[0].value;
  const colWidth = rows[0].band.parentElement.clientWidth;
  const widths = stages.map(s => Math.max(s.value / total * colWidth, colWidth * 0.32));

  rows.forEach(({ band, drop, s }, i) => {
    const t = i / (stages.length - 1);
    const top = widths[i];
    const bottom = i < widths.length - 1 ? widths[i + 1] : widths[i];
    const leftInset = ((top - bottom) / 2 / top * 100).toFixed(2);
    const rightInset = (100 - leftInset).toFixed(2);
    band.style.width = top + 'px';
    band.style.background = bfLerpColor(t);
    band.style.clipPath = `polygon(0% 0%, 100% 0%, ${rightInset}% 100%, ${leftInset}% 100%)`;
    if (i > 0) {
      const prev = stages[i - 1].value;
      const dropPct = (1 - s.value / prev) * 100;
      const label = dropPct >= 0 ? `-${dropPct.toFixed(1).replace('.', ',')}%` : `+${Math.abs(dropPct).toFixed(1).replace('.', ',')}%`;
      drop.innerHTML = `<div class="bf-drop-line"></div><div class="bf-drop-badge${dropPct >= 0 ? '' : ' pos'}">${label}</div>`;
    }
  });

  const dropFinal = (1 - cardIssued.value / stages[stages.length - 1].value) * 100;
  const kpiRow = document.createElement('div');
  kpiRow.className = 'bf-kpi-row';
  kpiRow.innerHTML = `<div class="bf-label" style="font-weight:700; color:#B8860B;">${cardIssued.label}</div><div class="bf-funnel"><div class="bf-kpi-band"><span class="icon">💳</span><span class="val">${cardIssued.value.toLocaleString(numLocale())}</span></div></div><div class="bf-drop"><div class="bf-drop-line"></div><div class="bf-drop-badge">-${dropFinal.toFixed(1).replace('.', ',')}%</div></div>`;
  container.appendChild(kpiRow);

  const last = stages[stages.length - 1].value;
  const audiencePct = (last / total * 100).toFixed(1).replace('.', ',');
  const cardsPctRaw = cardIssued.value / last * 100;
  const cardsPct = (cardsPctRaw < 0.1 ? cardsPctRaw.toFixed(2) : cardsPctRaw.toFixed(1)).replace('.', ',');
  const statsRow = document.createElement('div');
  statsRow.className = 'bf-stats';
  statsRow.innerHTML = `<div class="bf-final"><div class="big">${audiencePct}%</div><div class="sub">${L().s2.statBase(last.toLocaleString(numLocale()))}</div></div><div class="bf-final"><div class="big">${cardsPct}%</div><div class="sub">${L().s2.statCard(cardIssued.value.toLocaleString(numLocale()))}</div></div>`;
  container.appendChild(statsRow);
}

function renderBrunaFunnel() {
  const mercurioStages = [
    { label: 'Encendido total ML', value: 7506108 },
    { label: 'Audiência final entregável', value: 6598197 }
  ];
  const flowsStages = [
    { label: 'Encendido total ML', value: 5710166 },
    { label: 'Audiência definida', value: 5282972 },
    { label: 'Excl. não contactados (saturação)', value: 4665715 },
    { label: 'Excl. sem autorização de navegação', value: 4607320 },
    { label: 'Excl. duplicados', value: 4605751 },
    { label: 'Excl. não ativos no país', value: 4605581 },
    { label: 'Excl. desabilitaram promoções', value: 4139936 },
    { label: 'Excl. sem dispositivo contactável', value: 4122276 },
    { label: 'Audiência final entregável', value: 3023833 }
  ];
  renderBfFunnel('bf-mercurio', mercurioStages, { label: 'Cartões emitidos', value: 7847 });
  renderBfFunnel('bf-flows', flowsStages, { label: 'Cartões emitidos', value: 2147 });
  requestAnimationFrame(() => requestAnimationFrame(fitBfContent));
}

function fitBfContent() {
  const wrap = document.getElementById('bfScaleWrap');
  const content = document.getElementById('bfContent');
  if (!wrap || !content) return;
  content.style.transform = 'scale(1)';
  const naturalHeight = content.offsetHeight;
  // Largura ja e 100% real da tela (sem referencia fixa) -- so entra escala aqui
  // se a altura nao couber (janelas baixas), e so entao encolhe tudo junto.
  const scale = Math.min(wrap.clientHeight / naturalHeight, 1);
  content.style.transform = 'scale(' + scale + ')';
}
window.addEventListener('resize', () => { if (currentSlide === 2) fitBfContent(); });

function renderD1() {
  const d = D.D1_DATA[tcFilter];
  upsertChart('chartD1', {
    type: 'line',
    data: {
      labels: MESES.map(mesLabel),
      datasets: [{ label: tcFilter==='FULL' ? L().chart.d1Full : L().chart.d1Micro, data: MESES.map(m => d[m]),
        borderColor: tcFilter==='FULL'?'#009ee3':'#ff7733', backgroundColor: tcFilter==='FULL'?'#009ee3':'#ff7733',
        borderWidth: 4, pointRadius: 6, tension: .15 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { font: { size: 16 } } }, datalabels: { align: 'top', font: { weight: 700, size: 16 }, formatter: v => v!=null? v.toFixed(1)+'%':'' }, modelChangeLine: modelChangeOpts() },
      scales: { y: { ticks: { font: { size: 14 }, callback: v => v+'%' } }, x: { ticks: { font: { size: 15 } } } }
    },
    plugins: [ChartDataLabels, modelChangeLinePlugin]
  });
}

function renderRecebimento() {
  const d = D.RECEBIMENTO_DATA[tcFilter];
  const cores = { MP: '#00a650', ML: '#ff7733', SemApp: '#6c47c9' };
  const nomes = { MP: L().chart.mercadoPago, ML: L().chart.mercadoLivre, SemApp: L().chart.semApp };
  const datasets = ['MP','ML','SemApp'].map(app => ({
    label: nomes[app], data: MESES.map(m => d[m][app]),
    borderColor: cores[app], backgroundColor: cores[app], borderWidth: 3.5, pointRadius: 5, tension: .15
  }));
  upsertChart('chartRecebimento', {
    type: 'line',
    data: { labels: MESES.map(mesLabel), datasets },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { font: { size: 15 } } }, datalabels: { align: 'top', font: { weight: 700, size: 13 }, formatter: v => v!=null? v.toFixed(0)+'%':'' }, modelChangeLine: modelChangeOpts() },
      scales: { y: { ticks: { font: { size: 13 }, callback: v => v+'%' } }, x: { ticks: { font: { size: 14 } } } }
    },
    plugins: [ChartDataLabels, modelChangeLinePlugin]
  });

  const t = L().s3;
  document.getElementById('mecanismoText').innerHTML = tcFilter === 'FULL' ? t.mecFull : t.mecMicro;
}

function renderVelDelta() {
  const d = D.VEL_DELTA_DATA[tcFilter];
  upsertChart('chartVelDelta', {
    type: 'line',
    data: {
      labels: d.dias.map(x => 'D'+x),
      datasets: [
        { label: L().chart.antesLabel, data: d.antes, borderColor: '#111', backgroundColor: '#111', borderWidth: 3, tension: .2, pointRadius: 0 },
        { label: L().chart.depoisLabel, data: d.depois, borderColor: '#e4572e', backgroundColor: '#e4572e', borderWidth: 3, tension: .2, pointRadius: 0 }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { position: 'bottom', labels: { font: { size: 11 }, boxWidth: 12 } }, datalabels: { display: false } },
      scales: { y: { min: 0, max: 100, ticks: { font: { size: 11 }, callback: v=>v+'%' } }, x: { ticks: { font: { size: 9 }, maxTicksLimit: 8 } } }
    }
  });
}

function weightedAvg(rows, meses) {
  let num = 0, den = 0;
  meses.forEach(m => {
    const r = rows.find(x => x.mes === m);
    if (!r) return;
    num += r.avg_comunicacoes * r.qtd_propostas;
    den += r.qtd_propostas;
  });
  return den ? num / den : null;
}

// Media ponderada generica: soma(valueKey) / soma(weightKey) sobre os meses pedidos --
// usada onde a "media" e uma razao (ex: incremental/conversoes), nao uma media direta.
function weightedAvgGeneric(rows, meses, valueKey, weightKey) {
  let num = 0, den = 0;
  meses.forEach(m => {
    const r = rows.find(x => x.mes === m);
    if (!r) return;
    num += r[valueKey];
    den += r[weightKey];
  });
  return den ? num / den : null;
}

function renderComunic() {
  const flagTc = tcFilter === 'FULL' ? '1. TC Full' : '2. Micro TC';
  const rows = D.COMUNIC_DATA.filter(r => r.flag_tc === flagTc);
  const byMes = {}; rows.forEach(r => byMes[r.mes] = r.avg_comunicacoes);
  const cor = tcFilter === 'FULL' ? '#009ee3' : '#ff7733';

  // Antes = Jan,Mar,Abr (Fev excluido -- queda isolada de 1 mes so, mesmo tratamento
  // dado ao Fev no grafico de velocidade do dash_encendidos_v3). Depois = Mai,Jun,Jul
  // (Ago excluido -- ainda imaturo, nota abaixo). Media ponderada por qtd_propostas,
  // nao media simples dos meses.
  const antesAvg = weightedAvg(rows, ['202601', '202603', '202604']);
  const depoisAvg = weightedAvg(rows, ['202605', '202606', '202607']);
  const delta = (antesAvg && depoisAvg) ? ((depoisAvg / antesAvg - 1) * 100) : null;

  upsertChart('chartComunic', {
    type: 'line',
    data: {
      labels: MESES.map(mesLabel),
      datasets: [{ label: L().chart.comunicMedia, data: MESES.map(m => byMes[m]),
        borderColor: cor, backgroundColor: cor,
        borderWidth: 4, pointRadius: 6, tension: .15 }]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { labels: { font: { size: 16 } } },
        datalabels: { align: 'top', font: { weight: 700, size: 16 }, formatter: v => v!=null? v.toFixed(1):'' },
        modelChangeLine: modelChangeOpts(),
        avgRangeLine: { ranges: [
          { fromIdx: 0, toIdx: 3, value: antesAvg, color: '#666', labelAbove: true,
            label: L().antesLabel(antesAvg != null ? antesAvg.toFixed(1) : '--') },
          { fromIdx: 4, toIdx: 6, value: depoisAvg, color: cor, labelAbove: false,
            label: L().depoisLabel(depoisAvg != null ? depoisAvg.toFixed(1) : '--', delta != null ? delta.toFixed(0) : '--') }
        ] }
      },
      scales: { y: { ticks: { font: { size: 14 } } }, x: { ticks: { font: { size: 15 } } } }
    },
    plugins: [ChartDataLabels, modelChangeLinePlugin, avgRangeLinePlugin]
  });
}

function incVal(r) { return tcFilter === 'FULL' ? r.incremental_full : r.incremental_micro; }
function totalConvVal(mes) { const m = D.TOTAL_CONV[mes] || {}; return tcFilter === 'FULL' ? (m.FULL||0) : (m.MICRO||0); }

function renderIncTotal() {
  const vals = MESES.map(m => Math.round(D.INCREMENTAL_DATA.filter(r => r.mes === m).reduce((s,r) => s + incVal(r), 0)));
  upsertChart('chartIncTotal', {
    type: 'bar',
    data: { labels: MESES.map(mesLabel), datasets: [{ label: L().chart.incremental, data: vals, backgroundColor: tcFilter==='FULL'?'#009ee3':'#ff7733' }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { display: false }, datalabels: { anchor: 'end', align: 'top', font: { weight: 700, size: 14 }, formatter: v => v.toLocaleString(numLocale()) }, modelChangeLine: modelChangeOpts() },
      scales: { y: { ticks: { font: { size: 13 }, callback: v => v.toLocaleString(numLocale()) } }, x: { ticks: { font: { size: 14 } } } }
    },
    plugins: [ChartDataLabels, modelChangeLinePlugin]
  });
}

function renderIncPct() {
  const porMes = MESES.map(m => {
    const inc = D.INCREMENTAL_DATA.filter(r => r.mes === m).reduce((s,r) => s + incVal(r), 0);
    const conv = totalConvVal(m);
    return { mes: m, inc, conv };
  });
  const vals = porMes.map(r => r.conv ? +(100*r.inc/r.conv).toFixed(1) : null);

  // Mesma base Fev-Abr (Jan excluido -- pico pontual de MKT/"MASSIVA") ja usada na tabela
  // de perda logo abaixo, pra nao ter duas definicoes diferentes de "antes" na mesma tela.
  // Depois = Mai-Ago, mesmos 4 meses que a tabela de perda ja usa (Ago incluido de proposito
  // aqui, diferente do grafico de comunicacoes -- essa metrica nao depende da janela D0..D30).
  const antesAvg = weightedAvgGeneric(porMes, ['202602','202603','202604'], 'inc', 'conv');
  const depoisAvg = weightedAvgGeneric(porMes, ['202605','202606','202607','202608'], 'inc', 'conv');
  const delta = (antesAvg && depoisAvg) ? ((depoisAvg / antesAvg - 1) * 100) : null;

  upsertChart('chartIncPct', {
    type: 'line',
    data: { labels: MESES.map(mesLabel), datasets: [{ label: L().chart.pctConv, data: vals, borderColor: '#333', backgroundColor: '#333', borderWidth: 3.5, pointRadius: 5, tension: .15 }] },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        datalabels: { align: 'top', font: { weight: 700, size: 14 }, formatter: v => v!=null? v.toFixed(1)+'%':'' },
        modelChangeLine: modelChangeOpts(),
        avgRangeLine: { ranges: [
          { fromIdx: 1, toIdx: 3, value: antesAvg != null ? antesAvg*100 : null, color: '#666', labelAbove: true,
            label: L().antesLabelPct(antesAvg != null ? (antesAvg*100).toFixed(1) : '--') },
          { fromIdx: 4, toIdx: 7, value: depoisAvg != null ? depoisAvg*100 : null, color: '#a3001a', labelAbove: false,
            label: L().depoisLabelPct(depoisAvg != null ? (depoisAvg*100).toFixed(1) : '--', delta != null ? delta.toFixed(0) : '--') }
        ] }
      },
      scales: { y: { ticks: { font: { size: 13 }, callback: v => v+'%' } }, x: { ticks: { font: { size: 14 } } } }
    },
    plugins: [ChartDataLabels, modelChangeLinePlugin, avgRangeLinePlugin]
  });
}

function renderLossTable() {
  const porMes = MESES.map(m => {
    const inc = D.INCREMENTAL_DATA.filter(r => r.mes === m).reduce((s,r) => s + incVal(r), 0);
    const conv = totalConvVal(m);
    return { mes: m, inc, conv, pct: conv ? inc/conv : 0 };
  });
  const baseRows = porMes.filter(r => ['202602','202603','202604'].includes(r.mes));
  const incBase = baseRows.reduce((s,r) => s + r.inc, 0);
  const convBase = baseRows.reduce((s,r) => s + r.conv, 0);
  const meta = convBase ? incBase/convBase : 0;

  const t = L().s5;
  const mesesAlvo = ['202605','202606','202607','202608'];
  let somaPerda = 0;
  let html = '<div class="story-tbl-wrap"><table class="story-tbl"><thead><tr><th>' + t.mesHeader + '</th>' + mesesAlvo.map(m=>`<th>${mesLabel(m)}</th>`).join('') + `<th class="total-col">${t.totalHeader}</th>` + '</tr></thead><tbody>';
  html += '<tr><td>' + t.perdaLabel.replace('{PCT}', (meta*100).toFixed(1)) + '</td>';
  mesesAlvo.forEach(m => {
    const r = porMes.find(x => x.mes === m);
    const baseOrganica = r.conv - r.inc;
    const totalNecessario = Math.ceil(baseOrganica / (1 - meta));
    const perda = totalNecessario - r.conv;
    somaPerda += perda;
    html += `<td class="${perda>0?'neg':'pos'}">${perda>0?'-':'+'}${fmtInt(Math.abs(perda))}</td>`;
  });
  html += `<td class="total-col ${somaPerda>0?'neg':'pos'}">${somaPerda>0?'-':'+'}${fmtInt(Math.abs(somaPerda))}</td>`;
  html += '</tr></tbody></table></div>';
  document.getElementById('lossTableWrap').innerHTML = html;
}

function renderBU() {
  const d = D.BU_DATA[tcFilter];
  const mp = MESES.map(m => d[m].MP);
  const ml = MESES.map(m => d[m].ML);
  const pctMl = MESES.map((m,i) => { const t = mp[i]+ml[i]; return t ? +(100*ml[i]/t).toFixed(1) : null; });
  const pctMp = pctMl.map(v => v!=null ? +(100-v).toFixed(1) : null);
  upsertChart('chartBU', {
    type: 'bar',
    data: {
      labels: MESES.map(mesLabel),
      datasets: [
        { label: L().chart.mercadoPago, data: pctMp, backgroundColor: '#009ee3', stack: 's' },
        { label: L().chart.mercadoLivre, data: pctMl, backgroundColor: '#ffe600', stack: 's' }
      ]
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: { legend: { labels: { font: { size: 16 } } }, datalabels: { color: c => c.dataset.label === L().chart.mercadoLivre ? '#333' : '#fff', font: { weight: 700, size: 15 }, formatter: v => v!=null? v.toFixed(0)+'%':'' }, modelChangeLine: modelChangeOpts() },
      scales: { x: { stacked: true, ticks: { font: { size: 15 } } }, y: { stacked: true, max: 100, ticks: { font: { size: 13 }, callback: v=>v+'%' } } }
    },
    plugins: [ChartDataLabels, modelChangeLinePlugin]
  });
}

const BUCKET_ORDER = ['0','1','2','3','4','5','6','7','8','9','10+'];
const BUCKET_COLORS = ['#e8f6fd','#c9ecfa','#a3dff5','#7ad0ef','#4fc0e8','#009ee3','#0084bd','#006a97','#005071','#00374d','#001c28'];

function distDatasetsFor(tc) {
  const rows = D.DIST_DATA.filter(r => r.flag_tc === tc);
  const porMesBucket = {};
  MESES.forEach(m => { porMesBucket[m] = {}; BUCKET_ORDER.forEach(b => porMesBucket[m][b] = 0); });
  rows.forEach(r => { porMesBucket[r.mes][r.bucket] = (porMesBucket[r.mes][r.bucket]||0) + r.qtd_propostas; });
  return BUCKET_ORDER.map((b,i) => ({
    label: b,
    data: MESES.map(m => { const tot = BUCKET_ORDER.reduce((s,bb)=>s+porMesBucket[m][bb],0); return tot ? +(100*porMesBucket[m][b]/tot).toFixed(1) : 0; }),
    backgroundColor: BUCKET_COLORS[i], stack: 's'
  }));
}

function distChartOptions(titulo) {
  return {
    responsive: true, maintainAspectRatio: false,
    plugins: { legend: { display: false }, title: { display: true, text: titulo, font: { size: 16 } },
      datalabels: { display: c => c.dataset.data[c.dataIndex] >= 10, color: c => (BUCKET_ORDER.indexOf(c.dataset.label)>=6?'#fff':'#333'), font: { size: 10, weight: 700 }, formatter: v => v.toFixed(0)+'%' },
      modelChangeLine: modelChangeOpts() },
    scales: { x: { stacked: true, ticks: { font: { size: 12 } } }, y: { stacked: true, max: 100, ticks: { callback: v=>v+'%' } } }
  };
}

function renderDistFinal() {
  // Slide de fechamento SEMPRE mostra Full e Micro lado a lado (ignora o toggle de TC -- o contraste é o ponto)
  upsertChart('chartDistFinalFull', {
    type: 'bar',
    data: { labels: MESES.map(mesLabel), datasets: distDatasetsFor('1. TC Full') },
    options: distChartOptions('TC FULL'),
    plugins: [ChartDataLabels, modelChangeLinePlugin]
  });
  upsertChart('chartDistFinalMicro', {
    type: 'bar',
    data: { labels: MESES.map(mesLabel), datasets: distDatasetsFor('2. Micro TC') },
    options: distChartOptions('MICRO TC'),
    plugins: [ChartDataLabels, modelChangeLinePlugin]
  });
}

applyStaticText();
renderSlides();
const hashParts = location.hash.replace('#','').split('-');
if (hashParts[1] === 'micro') {
  tcFilter = 'MICRO';
  document.querySelectorAll('.tc-btn').forEach(b => b.classList.toggle('active', b.dataset.tc === 'MICRO'));
}
if (hashParts[2] === 'es' || hashParts[1] === 'es') {
  lang = 'ES';
  document.querySelectorAll('.lang-btn').forEach(b => b.classList.toggle('active', b.dataset.lang === 'ES'));
  applyStaticText();
  renderSlides();
}
const hashSlide = parseInt(hashParts[0], 10);
goToSlide(isNaN(hashSlide) ? 0 : hashSlide);
</script>

</body>
</html>
"""

html = html.replace("__DATA_JS__", DATA_JS)

with open('historia_comunicacao_tc.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("OK", len(html), "bytes")
