-- Distribuição de quantidade de comunicações por proposta, por safra de encendido -- complementa
-- o grid_comunicacoes_por_proposta_query.sql (que só traz media/mediana) com o formato completo
-- da distribuição: quantas propostas receberam exatamente 0, 1, 2, ..., 9 ou 10+ comunicações.
-- Objetivo: ver se a queda de MEDIA (já vista no outro grid) é um deslocamento geral da curva
-- (todo mundo recebe um pouco menos) ou uma polarização (mais gente indo pra 0/poucas, enquanto
-- outra parte continua recebendo muito).
--
-- Mesma base, mesma janela FIXA D0..D30 pos-encendido e mesmo escopo de campanhas (regex "Método
-- B") do grid_comunicacoes_por_proposta_query.sql -- pra ser diretamente comparável.
--
-- Traz as DUAS populações (Todos e Aceitas, por safra de CRIAÇÃO = mesma data de encendido) na
-- MESMA passada pela base cara (comunic/proposal_touches escaneia BT_OC_MP_NOTIFICATION_CUST_EVENT,
-- ~3,8TB/mês) via UNION ALL sobre o mesmo `bucketed` -- em vez de rodar a query de novo só pra
-- filtrar aceitas, o que pagaria o scan caro 2x pelo mesmo mês.
--
-- TEMPLATE MENSAL, mesmos placeholders: {{MES_INICIO}}, {{MES_FIM}}, {{COMUNIC_ATE}} (MES_FIM + 30 dias).

WITH

proposal_base AS (
  SELECT
    CAST(A.CCARD_PROP_CREATION_DT AS DATE) AS DT_ENCENDIDO,
    SAFE_CAST(A.CUS_CUST_ID AS INT64) AS cus_cust_id,
    A.CCARD_PROP_ID AS ccard_prop_id,
    A.CCARD_PROP_STATUS AS ccard_prop_status,
    CASE WHEN A.CCARD_GLOBAL_LIMIT_AMT_LC <= 100 OR A.CCARD_PRODUCT_ID = 5
         THEN '2. Micro TC' ELSE '1. TC Full' END AS FLAG_TC
  FROM `meli-bi-data.WHOWNER.BT_CCARD_PROPOSAL` A
  WHERE A.sit_site_id = 'MLB'
    AND CAST(A.CCARD_PROP_CREATION_DT AS DATE) BETWEEN '{{MES_INICIO}}' AND '{{MES_FIM}}'
),

comunic AS (
  SELECT DISTINCT
    SAFE_CAST(CUS_CUST_ID AS INT64) AS cus_cust_id,
    CAMPAIGN_NAME,
    CAST(SENT_DATE AS DATE) AS sent_date
  FROM `meli-bi-data.SBOX_MARKETING.BT_OC_MP_NOTIFICATION_CUST_EVENT`
  WHERE SIT_SITE_ID = 'MLB'
    AND FLAG_NOTIFICATION_CENTER = 'N'
    AND SENT_DATE BETWEEN '{{MES_INICIO}}' AND '{{COMUNIC_ATE}}'
    AND EVENT_TYPE = 'arrived'
    AND REGEXP_CONTAINS(UPPER(CAMPAIGN_NAME), r'TC|CCARD|BARRIDA|PENDING|ELDO_MAR|MMAIS\.HFP|WILLBAN')
),

proposal_touches AS (
  SELECT
    p.ccard_prop_id,
    COUNT(*) AS qtd_comunicacoes_d30
  FROM proposal_base p
  JOIN comunic c
    ON c.cus_cust_id = p.cus_cust_id
   AND c.sent_date BETWEEN p.DT_ENCENDIDO AND DATE_ADD(p.DT_ENCENDIDO, INTERVAL 30 DAY)
  GROUP BY 1
),

bucketed AS (
  SELECT
    FORMAT_DATE('%Y%m', p.DT_ENCENDIDO) AS anomes_encendido,
    p.FLAG_TC,
    p.ccard_prop_status,
    CASE
      WHEN IFNULL(t.qtd_comunicacoes_d30, 0) >= 10 THEN '10+'
      ELSE CAST(IFNULL(t.qtd_comunicacoes_d30, 0) AS STRING)
    END AS bucket,
    -- ordinal só pra ordenar '0','1',...,'9','10+' corretamente (string ordena '10+' antes de '2')
    LEAST(IFNULL(t.qtd_comunicacoes_d30, 0), 10) AS bucket_ord
  FROM proposal_base p
  LEFT JOIN proposal_touches t ON t.ccard_prop_id = p.ccard_prop_id
)

SELECT anomes_encendido, FLAG_TC, 'Todos' AS flag_populacao, bucket, bucket_ord, COUNT(*) AS qtd_propostas
FROM bucketed
GROUP BY 1, 2, 3, 4, 5

UNION ALL

SELECT anomes_encendido, FLAG_TC, 'Aceitas' AS flag_populacao, bucket, bucket_ord, COUNT(*) AS qtd_propostas
FROM bucketed
WHERE ccard_prop_status = 'accepted'
GROUP BY 1, 2, 3, 4, 5

ORDER BY 1, 2, 3, 5
