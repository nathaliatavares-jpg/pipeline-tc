"""
ACOMPANHAMENTO TC — Pipeline Python
Replica fiel do workflow n8n exportado de meli-bi-data.

Schedule : 08:45 todo dia (45 8 * * *)
BigQuery : meli-bi-data
Planilha : 15b3opBLlZ6KpX2YAvWEfrHHUtcvWL6u2FEUOojX1GVI
Slack    : #testebotcomunic

Dependências:
  pip install google-cloud-bigquery gspread google-auth slack_sdk apscheduler
"""

import asyncio
import re
import os
from datetime import datetime

from google.cloud import bigquery
import google.auth
import gspread
from slack_sdk import WebClient

# ─── Configuração ─────────────────────────────────────────────────────────────

SLACK_BOT_TOKEN = os.environ.get("SLACK_BOT_TOKEN", "")
SLACK_CHANNEL   = "comunicações-tc-adq-bot"
BQ_PROJECT      = "meli-bi-data"
SHEET_ID        = "15b3opBLlZ6KpX2YAvWEfrHHUtcvWL6u2FEUOojX1GVI"

# Escopos necessários (BigQuery + Sheets)
GOOGLE_SCOPES = [
    "https://www.googleapis.com/auth/bigquery.readonly",
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# ─── Clientes (usa Application Default Credentials — sua conta Google) ────────

def _creds():
    """
    Usa as credenciais configuradas via:
      gcloud auth application-default login --scopes="..."
    Não precisa de service account nem admin no projeto.
    """
    creds, _ = google.auth.default(scopes=GOOGLE_SCOPES)
    return creds

def get_bq():
    return bigquery.Client(project=BQ_PROJECT, credentials=_creds())

def get_gc():
    return gspread.authorize(_creds())

# ─── SQL Queries (idênticas ao n8n) ───────────────────────────────────────────

SQL_AUTOMATIZADAS = """
SELECT
  CASE
    WHEN CAMPAIGN_NAME = 'MLB_MP_ML-PUSHML_CCC_X_AO-ACQ_ALL_TXS_X_X_DEFAULT_C-EG-CCARDACQ-SIN-TC-ENR-ML'
    THEN 'MLB-ML-C-EG-ACT-CCARDACQ-SIN-TC-ENR-ML'
    ELSE CAMPAIGN_NAME
  END AS CAMPAIGN,
  MIN(SENT_DATE) AS MIN_NOT_DATE,
  COUNT(DISTINCT CUS_CUST_ID) AS qtd_send
FROM `meli-bi-data.SBOX_MARKETING.BT_OC_CUST_EVENT`
WHERE
  SENT_DATE = CURRENT_DATE - 1
  AND SIT_SITE_ID = 'MLB'
  AND FLAG_NOTIFICATION_CENTER = 'N'
  AND EVENT_TYPE IN ('shown', 'open', 'arrived', 'control')
  AND CAMPAIGN_NAME IN (
    'MLB-ML-I-EG-XSELLT1-PUSH-NIA-CCARDACQ-D1',
    'MLB-ML-I-EG-XSELLT1-PUSH-CCARDACQ-D1-MIC',
    'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-D6-MIC',
    'MLB-MP-I-EG-XSELLT1-PUSH-SOL-TC2',
    'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-D14-MIC',
    ' MLB-ML-C-EG-ACT-PUSH-CCARDACQ-BARRIDA',
    'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-BARRIDA-MI',
    'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-UP1',
    'MLB-ML-C-EG-ACT-CCARDACQ-SIN-TC-ENR-ML',
    'MLB_MP_ML-PUSHML_CCC_X_AO-ACQ_ALL_TXS_X_X_DEFAULT_C-EG-CCARDACQ-SIN-TC-ENR-ML'
  )
GROUP BY ALL
"""

SQL_ADHOC_ENVIADAS = """
SELECT
  CAMPAIGN_NAME AS CAMPANHA,
  MIN(SENT_DATE) AS DATA_ENVIO,
  COUNT(DISTINCT CUS_CUST_ID) AS QTD_SEND,
  NOTIFICATION_TITLE_DESC AS TITULO,
  NOTIFICATION_TEXT_DESC AS CORPO
FROM `meli-bi-data.SBOX_MARKETING.BT_OC_CUST_EVENT` NT
LEFT JOIN `meli-bi-data.WHOWNER.LK_OC_MERCURIO_CONTENTS` B
  ON CAST(NT.COMMUNICATION_ID AS STRING) = CAST(B.CAMPAIGN_ID AS STRING)
WHERE
  SENT_DATE = CURRENT_DATE - 1
  AND NT.SIT_SITE_ID = 'MLB'
  AND FLAG_NOTIFICATION_CENTER = 'N'
  AND EVENT_TYPE IN ('shown', 'open', 'arrived', 'control')
  AND (
    CAMPAIGN_NAME LIKE '%TC-AQS%'
    OR CAMPAIGN_NAME LIKE '%TCADQ%'
    OR CAMPAIGN_NAME LIKE '%TCAQUI%'
    OR CAMPAIGN_NAME LIKE '%TCAQUISICAO%'
    OR UPPER(CAMPAIGN_NAME) LIKE '%FLOWS_COMMUNICATION_ELDO_FEV_ML_%'
  )
GROUP BY ALL
"""

SQL_RESULTADOS_ADHOC = """
WITH NT AS (
  SELECT DISTINCT CAMPAIGN_NAME, COMMUNICATION_ID, SENT_DATE
  FROM `meli-bi-data.SBOX_MARKETING.BT_OC_CUST_EVENT`
  WHERE
    SIT_SITE_ID = 'MLB'
    AND sent_date = CURRENT_DATE - 4
    AND (
      CAMPAIGN_NAME LIKE '%TC-AQS%'
      OR CAMPAIGN_NAME LIKE '%TCADQ%'
      OR CAMPAIGN_NAME LIKE '%TCAQUI%'
      OR CAMPAIGN_NAME LIKE '%TCAQUISICAO%'
      OR UPPER(CAMPAIGN_NAME) LIKE '%FLOWS_COMMUNICATION_ELDO_FEV_ML_%'
    )
),
B AS (
  SELECT DISTINCT CAMPAIGN_ID, NOTIFICATION_TEXT_DESC, NOTIFICATION_TITLE_DESC
  FROM `meli-bi-data.WHOWNER.LK_OC_MERCURIO_CONTENTS`
  WHERE SIT_SITE_ID = 'MLB'
)
SELECT
  nt.CAMPAIGN_NAME,
  FIRST_SENT_DATE AS DATA_ENVIO,
  CHANNEL AS CANAL,
  COUNT_TOTAL_USERS_TEST AS QTD_ENVIO,
  ROUND(OPEN_RATE * 100, 2) AS OPEN_RATE,
  ROUND(LIFT * 100, 2) AS LIFT,
  NOTIFICATION_TITLE_DESC AS TITULO,
  NOTIFICATION_TEXT_DESC AS CORPO
FROM `meli-bi-data.SBOX_MARKETING.BT_OC_MP_NOTIFICATION_MONTHLY` A
LEFT JOIN NT ON A.CAMPAIGN_NAME = NT.CAMPAIGN_NAME
LEFT JOIN B ON CAST(NT.COMMUNICATION_ID AS STRING) = CAST(B.CAMPAIGN_ID AS STRING)
WHERE
  A.SIT_SITE_ID = 'MLB'
  AND A.FLAG_NOTIFICATION_CENTER = 'N'
  AND FIRST_SENT_DATE = CURRENT_DATE - 4
  AND MATCH_KPI_PPAL <> 'NO_MATCH'
  AND (
    A.CAMPAIGN_NAME LIKE '%TC-AQS%'
    OR A.CAMPAIGN_NAME LIKE '%TCADQ%'
    OR A.CAMPAIGN_NAME LIKE '%TCAQUI%'
    OR A.CAMPAIGN_NAME LIKE '%TCAQUISICAO%'
    OR UPPER(A.CAMPAIGN_NAME) LIKE '%FLOWS_COMMUNICATION_ELDO_FEV_ML_%'
  )
GROUP BY ALL
"""

# ─── Constantes (VerdiCode) ───────────────────────────────────────────────────

# Lista fixa de campanhas para o pivot (VerdiCode - Branch 1)
CAMPANHAS_FIXAS = [
    'MLB-ML-I-EG-XSELLT1-PUSH-NIA-CCARDACQ-D1',
    'MLB-ML-I-EG-XSELLT1-PUSH-CCARDACQ-D1-MIC',
    'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-D6-MIC',
    'MLB-MP-I-EG-XSELLT1-PUSH-SOL-TC2',
    'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-D14-MIC',
    ' MLB-ML-C-EG-ACT-PUSH-CCARDACQ-BARRIDA',   # espaço intencional (igual ao n8n)
    'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-BARRIDA-MI',
    'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-UP1',
    'MLB-ML-C-EG-ACT-CCARDACQ-SIN-TC-ENR-ML',
]

# De-para para nomes amigáveis (VerdiCode3)
NOMES_CAMPANHAS = {
    'MLB-ML-I-EG-XSELLT1-PUSH-NIA-CCARDACQ-D1':    'D1 FULL',
    'MLB-ML-I-EG-XSELLT1-PUSH-CCARDACQ-D1-MIC':    'D1 MICRO',
    'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-D6-MIC':        'D6 MICRO',
    'MLB-MP-I-EG-XSELLT1-PUSH-SOL-TC2':            'D10 FULL',
    'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-D14-MIC':       'D14 MICRO',
    ' MLB-ML-C-EG-ACT-PUSH-CCARDACQ-BARRIDA':      'VARRIDA FULL',
    'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-BARRIDA-MI':    'VARRIDA MICRO',
    'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-UP1':           'UPSELL',
    'MLB-ML-C-EG-ACT-CCARDACQ-SIN-TC-ENR-ML':      'NAVEGOU ML',
}

# ─── Funções auxiliares ───────────────────────────────────────────────────────

def formatar_numero(valor) -> str:
    """Formata número em K ou MM (igual ao n8n)."""
    try:
        if isinstance(valor, str):
            valor = float(valor.replace(",", ".")) if valor else 0
        valor = float(valor or 0)
    except (ValueError, TypeError):
        return "0"
    if valor >= 1_000_000:
        return f"{valor / 1_000_000:.1f}MM".replace(".", ",")
    elif valor >= 1_000:
        return f"{valor / 1_000:.1f}K".replace(".", ",")
    return str(int(valor))


def limpar_freemarker(texto: str) -> str:
    """
    VerdiCode1 / VerdiCode2:
    Remove tags FreeMarker <#if...><#else>FALLBACK</#if> → mantém só FALLBACK.
    Substitui ${user.first_name} por [name].
    """
    if not texto:
        return ""
    texto = re.sub(r"<#if[^>]*>.*?<#else>(.*?)</#if>", r"\1", texto, flags=re.DOTALL)
    texto = texto.replace("${user.first_name}", "[name]")
    return texto


def bq_query(bq: bigquery.Client, sql: str) -> list[dict]:
    return [dict(row) for row in bq.query(sql).result()]

# ─── Branch 1: Automatizadas ──────────────────────────────────────────────────
# SQL → VerdiCode (pivot) → AUTOMATIZADAS sheet → VerdiCode3 (alerta Slack)

async def branch_automatizadas(bq: bigquery.Client, gc: gspread.Client) -> str:
    print("[Branch 1] SQL automatizadas...")
    rows = await asyncio.to_thread(bq_query, bq, SQL_AUTOMATIZADAS)

    # VerdiCode: monta linha pivotada com todas as campanhas
    resultados = {r["CAMPAIGN"]: r["qtd_send"] for r in rows}
    data = str(rows[0]["MIN_NOT_DATE"]) if rows else ""

    row_sheet = {"DATA": data}
    for camp in CAMPANHAS_FIXAS:
        row_sheet[camp] = resultados.get(camp, "")

    # Append → aba "AUTOMATIZADAS"
    print("[Branch 1] Gravando em AUTOMATIZADAS...")
    ws = await asyncio.to_thread(
        lambda: gc.open_by_key(SHEET_ID).worksheet("AUTOMATIZADAS")
    )
    await asyncio.to_thread(ws.append_row, list(row_sheet.values()), value_input_option="USER_ENTERED", insert_data_option="INSERT_ROWS")

    # VerdiCode3: gera mensagem de alertas
    nulos, mais_50k = [], []
    for chave, valor in row_sheet.items():
        if chave == "DATA":
            continue
        nome = NOMES_CAMPANHAS.get(chave, chave)
        if valor == "" or valor is None:
            nulos.append(nome)
        else:
            try:
                if float(str(valor).replace(",", ".") or 0) > 50_000:
                    mais_50k.append(f"*{nome}:*  {formatar_numero(valor)} envios")
            except (ValueError, TypeError):
                pass

    msg = f"📊 *Relatório de Envios - {data}*\n\n"
    if mais_50k:
        msg += "🟢 *Envios de automatizadas acima de 50K:*\n"
        msg += "".join(f"• {m}\n" for m in mais_50k) + "\n"
    if nulos:
        msg += "⚠️ *Sem envio de automatizada ontem:*\n"
        msg += "".join(f"• {n}\n" for n in nulos)
    if not nulos and not mais_50k:
        msg += "✅ Nenhum alerta hoje sobre automatizadas."

    return msg


# ─── Branch 2: Adhoc Enviadas ─────────────────────────────────────────────────
# SQL → VerdiCode2 (limpa FreeMarker) → "ADHOC ENVIADAS" sheet → VerdiCode4

async def branch_adhoc_enviadas(bq: bigquery.Client, gc: gspread.Client) -> str:
    print("[Branch 2] SQL adhoc enviadas...")
    rows = await asyncio.to_thread(bq_query, bq, SQL_ADHOC_ENVIADAS)

    # VerdiCode2: limpa templates FreeMarker
    for r in rows:
        r["TITULO"] = limpar_freemarker(r.get("TITULO") or "")
        r["CORPO"]  = limpar_freemarker(r.get("CORPO") or "")

    # Append → aba "ADHOC ENVIADAS" (gid=1483226623)
    print("[Branch 2] Gravando em ADHOC ENVIADAS...")
    ws = await asyncio.to_thread(
        lambda: gc.open_by_key(SHEET_ID).get_worksheet_by_id(1483226623)
    )
    for r in rows:
        await asyncio.to_thread(ws.append_row, [
            str(r.get("DATA_ENVIO", "")),
            r.get("CAMPANHA", ""),
            str(r.get("QTD_SEND", "")),
            r.get("TITULO", ""),
            r.get("CORPO", ""),
        ], value_input_option="USER_ENTERED", insert_data_option="INSERT_ROWS")

    # VerdiCode4: monta mensagem (pula seção se não houver dados)
    if not rows:
        return ""

    msg = "*COMUNICAÇÕES DISPARADAS ONTEM:*\n\n"
    for r in rows:
        msg += f"*{r.get('CAMPANHA', '')}*\n"
        msg += f"*Envios:* {formatar_numero(r.get('QTD_SEND', 0))}\n"
        msg += f"_{r.get('TITULO', '')}_\n"
        msg += f"_{r.get('CORPO', '')}_\n"
        msg += "━━━━━━━━━━━━━━━━━\n\n"

    return msg


# ─── Branch 3: Resultados Adhoc ───────────────────────────────────────────────
# SQL → VerdiCode1 (formata %, p.p, FreeMarker) → "RESULTADOS ADHOC" → VerdiCode5

async def branch_resultados_adhoc(bq: bigquery.Client, gc: gspread.Client) -> str:
    print("[Branch 3] SQL resultados adhoc (D-4)...")
    rows = await asyncio.to_thread(bq_query, bq, SQL_RESULTADOS_ADHOC)

    # VerdiCode1: formata OPEN_RATE / LIFT + limpa FreeMarker
    for r in rows:
        open_rate = r.get("OPEN_RATE")
        lift      = r.get("LIFT")
        r["OPEN_RATE"] = (str(open_rate).replace(".", ",") + "%") if open_rate is not None else ""
        r["LIFT"]      = (str(lift).replace(".", ",") + "p.p")    if lift      is not None else ""
        r["TITULO"]    = limpar_freemarker(r.get("TITULO") or "")
        r["CORPO"]     = limpar_freemarker(r.get("CORPO") or "")

    # Append → aba "RESULTADOS ADHOC" (gid=851285418)
    print("[Branch 3] Gravando em RESULTADOS ADHOC...")
    ws = await asyncio.to_thread(
        lambda: gc.open_by_key(SHEET_ID).get_worksheet_by_id(851285418)
    )
    for r in rows:
        await asyncio.to_thread(ws.append_row, [
            r.get("CAMPAIGN_NAME", ""),
            str(r.get("DATA_ENVIO", "")),
            r.get("CANAL", ""),
            str(r.get("QTD_ENVIO", "")),
            r.get("OPEN_RATE", ""),
            r.get("LIFT", ""),
            r.get("TITULO", ""),
            r.get("CORPO", ""),
        ], value_input_option="USER_ENTERED", insert_data_option="INSERT_ROWS")

    # VerdiCode5: monta mensagem (pula seção se não houver dados)
    if not rows:
        return ""

    msg = "*RESULTADO DOS ÚLTIMOS DISPAROS*\n\n"
    for r in rows:
        msg += f"*{r.get('CAMPAIGN_NAME', '')}*\n"
        msg += f"*Envios:* {formatar_numero(r.get('QTD_ENVIO', 0))} | *Canal:* {r.get('CANAL', '')}\n"
        msg += f"*Open Rate:* {r.get('OPEN_RATE', '')}  |  *Lift:* {r.get('LIFT', '')}\n"
        msg += f"_{r.get('TITULO', '')}_\n"
        msg += f"_{r.get('CORPO', '')}_\n"
        msg += "━━━━━━━━━━━━━━━━━\n\n"

    return msg


# ─── Pipeline principal ───────────────────────────────────────────────────────

async def run_pipeline():
    print(f"\n{'=' * 55}")
    print(f"ACOMPANHAMENTO TC — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'=' * 55}\n")

    bq = await asyncio.to_thread(get_bq)
    gc = await asyncio.to_thread(get_gc)

    # Executa as 3 branches em paralelo (igual ao n8n)
    msg1, msg2, msg3 = await asyncio.gather(
        branch_automatizadas(bq, gc),
        branch_adhoc_enviadas(bq, gc),
        branch_resultados_adhoc(bq, gc),
    )

    # VerdiCode6: une apenas seções com dados + link da planilha
    sep = "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    secoes = [m for m in [msg1, msg2, msg3] if m]
    if not secoes:
        mensagem_final = "Sem comunicações ✅"
    else:
        mensagem_final = sep.join(secoes)
    mensagem_final += (
        "\n\n📎 Para todo o histórico: "
        "<https://docs.google.com/spreadsheets/d/"
        "15b3opBLlZ6KpX2YAvWEfrHHUtcvWL6u2FEUOojX1GVI"
        "/edit?gid=0#gid=0|planilha>"
    )

    # Send a message → Slack #testebotcomunic
    print(f"[Slack] Enviando para #{SLACK_CHANNEL}...")
    slack = WebClient(token=SLACK_BOT_TOKEN)
    await asyncio.to_thread(
        slack.chat_postMessage,
        channel=SLACK_CHANNEL,
        text=mensagem_final,
    )

    print("✅ Pipeline concluído!\n")


# ─── Schedule Trigger: 45 8 * * * ────────────────────────────────────────────

def start_scheduled():
    from apscheduler.schedulers.blocking import BlockingScheduler
    scheduler = BlockingScheduler(timezone="America/Sao_Paulo")
    scheduler.add_job(
        lambda: asyncio.run(run_pipeline()),
        "cron",
        hour=8,
        minute=45,
    )
    print("Agendado: todo dia às 08:45 (America/Sao_Paulo). Ctrl+C para parar.")
    scheduler.start()


if __name__ == "__main__":
    import sys
    if "--schedule" in sys.argv:
        start_scheduled()
    else:
        asyncio.run(run_pipeline())
