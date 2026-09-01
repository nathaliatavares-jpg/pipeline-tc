-- v3 — Velocidade de recebimento por safra: para cada App Ativo, % acumulado de encendidos
-- que já receberam (e que já viram) comunicação até D dias após o encendido, por safra
-- (mês de encendido). Objetivo: comparar se o tempo até a 1ª comunicação está aumentando
-- entre safras. Mesmos filtros da aba de tabelas: Reencendido, Status Limite, Tipo TC, Canal.
--
-- Denominador FIXO por corte (não encolhe com o dia — senão a % pode cair só por causa da
-- composição da base). dias_maturidade = idade (dias desde o encendido) do membro MAIS ANTIGO
-- do corte — usado só pra saber até onde a curva já faz sentido (não trava o mês corrente em
-- D0 só porque teve gente que encendeu ontem).

WITH

app_instalado AS (
  SELECT
    B1.CUS_CUST_ID,
    STRING_AGG(DISTINCT MARKETPLACE ORDER BY MARKETPLACE ASC) AS APP_INST
  FROM `meli-bi-data.WHOWNER.BT_MKT_OWNCHANNELS_DEVICES` B1
  WHERE UPPER(B1.PLATFORM) IN ('IOS', 'ANDROID')
    AND UPPER(B1.STATUS) = 'ACTIVE'
    AND UPPER(B1.SIT_SITE_ID) = 'MLB'
    AND MARKETPLACE IN ('MERCADOPAGO', 'MERCADOLIBRE', 'MERCADOLIVRE')
  GROUP BY 1
),

congrats_ea AS (
  -- mesmo padrao do funil_encendidos_v3_conversao_query.sql -- travado em PLACEMENT = 'EA',
  -- casando por cus_cust_id + mes de aceite (nao mes de encendido)
  SELECT DISTINCT
    CUS_CUST_ID AS cus_cust_id,
    DATE_TRUNC(DT_aceite, MONTH) AS mes_aceite
  FROM `meli-bi-data.SBOX_CREDITSTC.0_AUT_TBL_CONGRATS_ADQ_MLB_TOTAL_AJUSTADA`
  WHERE UPPER(PLACEMENT) = 'EA'
),

proposal_base AS (
  SELECT
    CAST(A.CCARD_PROP_CREATION_DT AS DATE) AS DT_ENCENDIDO,
    A.CCARD_PROP_STATUS,
    CAST(A.CCARD_PROP_UPDATE_DT AS DATE) AS DT_CONV,
    SAFE_CAST(A.CUS_CUST_ID AS INT64) AS cus_cust_id,
    A.CCARD_PROP_ID AS ccard_prop_id,
    CASE WHEN A.CCARD_GLOBAL_LIMIT_AMT_LC <= 100 OR A.CCARD_PRODUCT_ID = 5
         THEN '2. Micro TC' ELSE '1. TC Full' END AS FLAG_TC,
    CASE
      WHEN LAG(A.CCARD_GLOBAL_LIMIT_AMT_LC, 1) OVER (PARTITION BY SAFE_CAST(A.CUS_CUST_ID AS INT64) ORDER BY A.CCARD_PROP_CREATION_DT ASC) > A.CCARD_GLOBAL_LIMIT_AMT_LC THEN 'Downsell'
      WHEN LAG(A.CCARD_GLOBAL_LIMIT_AMT_LC, 1) OVER (PARTITION BY SAFE_CAST(A.CUS_CUST_ID AS INT64) ORDER BY A.CCARD_PROP_CREATION_DT ASC) = A.CCARD_GLOBAL_LIMIT_AMT_LC THEN 'Mesmo Limite que Anterior'
      WHEN LAG(A.CCARD_GLOBAL_LIMIT_AMT_LC, 1) OVER (PARTITION BY SAFE_CAST(A.CUS_CUST_ID AS INT64) ORDER BY A.CCARD_PROP_CREATION_DT ASC) < A.CCARD_GLOBAL_LIMIT_AMT_LC THEN 'Upsell'
      WHEN LAG(A.CCARD_GLOBAL_LIMIT_AMT_LC, 1) OVER (PARTITION BY SAFE_CAST(A.CUS_CUST_ID AS INT64) ORDER BY A.CCARD_PROP_CREATION_DT ASC) IS NULL THEN 'Primeira Proposta'
    END AS status_limite_reenc,
    -- próximo encendido do MESMO cliente (se houver) — usado pra não deixar comunicação de um
    -- reencendido futuro "vazar" pra dentro da janela de uma proposta anterior ainda pending
    LEAD(CAST(A.CCARD_PROP_CREATION_DT AS DATE)) OVER (
      PARTITION BY SAFE_CAST(A.CUS_CUST_ID AS INT64) ORDER BY A.CCARD_PROP_CREATION_DT ASC
    ) AS DT_PROXIMO_ENCENDIDO
  FROM `meli-bi-data.WHOWNER.BT_CCARD_PROPOSAL` A
  WHERE A.sit_site_id = 'MLB'
  -- NÃO filtrar data aqui: LAG/LEAD precisam do histórico completo do cliente. Filtro entra
  -- só no SELECT final.
),

proposal_enriquecida AS (
  SELECT
    p.*,
    CASE WHEN p.status_limite_reenc = 'Primeira Proposta' THEN '1. Primeiro Encendido' ELSE '2. Reencendido' END AS flag_reencendido,
    CASE
      WHEN app2.APP_INST LIKE '%MERCADOPAGO%' THEN '1. MP'
      WHEN app2.APP_INST LIKE '%MERCADOLIBRE%' OR app2.APP_INST LIKE '%MERCADOLIVRE%' THEN '2. ML'
      ELSE '3. Sem App'
    END AS app_instalado_encendido,
    -- fim da janela: conversão/cancelamento (ou hoje se pending), mas nunca depois do dia
    -- anterior ao próximo encendido do mesmo cliente — evita contaminar a safra de maio com
    -- comunicação que na verdade é do reencendido de agosto
    LEAST(
      CASE WHEN p.CCARD_PROP_STATUS = 'pending' THEN CURRENT_DATE ELSE p.DT_CONV END,
      COALESCE(DATE_SUB(p.DT_PROXIMO_ENCENDIDO, INTERVAL 1 DAY), DATE '9999-12-31')
    ) AS DT_FIM_JANELA,
    -- mesmo padrao do funil_encendidos_v3_conversao_query.sql -- só pode ser EA quem de fato
    -- converteu (accepted); quem não converteu cai sempre em "Sem EA-MP"
    CASE WHEN congrats.cus_cust_id IS NOT NULL AND p.CCARD_PROP_STATUS = 'accepted'
         THEN '1. Com EA-MP' ELSE '2. Sem EA-MP' END AS flag_ea
  FROM proposal_base p
  LEFT JOIN app_instalado app2 ON app2.CUS_CUST_ID = p.cus_cust_id
  LEFT JOIN congrats_ea congrats
    ON congrats.cus_cust_id = p.cus_cust_id
   AND congrats.mes_aceite = DATE_TRUNC(p.DT_CONV, MONTH)
),

comunic AS (
  SELECT
    cus_cust_id,
    CAST(SENT_DATE AS DATE) AS sent_date,
    LOGICAL_OR(EVENT_TYPE = 'test')                          AS fl_sent,
    LOGICAL_OR(EVENT_TYPE = 'test' AND CHANNEL = 'PUSH')      AS fl_sent_push,
    LOGICAL_OR(EVENT_TYPE = 'test' AND CHANNEL = 'EMAIL')     AS fl_sent_email,
    LOGICAL_OR(EVENT_TYPE = 'test' AND CHANNEL = 'WHATSAPP')  AS fl_sent_whatsapp,
    LOGICAL_OR(EVENT_TYPE = 'shown')                          AS fl_shown
  FROM `meli-bi-data.SBOX_MARKETING.BT_OC_CUST_EVENT`
  WHERE SENT_DATE >= '2026-01-01'
    AND SIT_SITE_ID = 'MLB'
    AND FLAG_NOTIFICATION_CENTER = 'N'
    AND EVENT_TYPE IN ('test', 'shown')
    AND (
      CAMPAIGN_NAME IN (
        'MLB-ML-I-EG-XSELLT1-PUSH-NIA-CCARDACQ-D1', 'MLB-ML-I-EG-XSELLT1-PUSH-CCARDACQ-D1-MIC',
        'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-D6-MIC', 'MLB-MP-I-EG-XSELLT1-PUSH-SOL-TC2',
        'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-D14-MIC', 'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-BARRIDA',
        'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-BARRIDA-MI', 'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-UP1',
        'MLB-ML-C-EG-ACT-CCARDACQ-SIN-TC-ENR-ML', 'MLB_MP_ML-PUSHML_CCC_X_AO-ACQ_ALL_TXS_X_X_DEFAULT_C-EG-CCARDACQ-SIN-TC-ENR-ML',
        'flows_communication_MLB_I_EG_NEW_TC_SOL_ENC_mer_nc9', 'flows_communication_MLB_I_EG_NEW_TC_SOL_ENC_mer_1t0',
        'MLB_I_EG_NEW_TC_SOL_ENC', 'MLB_MP_WSPP-WAP_CAR_CRED-CAR_REQ_I-EG-XSELLT1_ENC_TC_NOENG',
        'MLB_I_EG_XSELLT1_T_TC_SOL_ENC', 'MLB_MP_WSPP-WAP_CAR_CRED-CAR_REQ_I-EG-XSELLT1_ENC_TC',
        'MLB-MP-I-EG-XSELLT1-PUSH-NIA-CCARD-BARR', 'MLB_I_EG_XSELLT1_BARRIDA',
        'MLB-ML-C-EG-ACT-PUSH-POST-COMPRA-TC', 'MLB-MP-I-EG-XSELLT1-PUSH-TC-MELIPLUS',
        'MLB-ML-I-EG-XSELLT1-PUSH-MICROUSO', 'MLB-MP-I-EG-XSELLT1-PUSH-USO-30',
        'MLB_I_EG_XSELLT1_T_TC_SOL_UP', 'MLB_MP_WSPP-WAP_CAR_CRED-CAR_REQ_I-EG-XSELLT1_UPSELL_TC',
        'MLB-ML-I-EG-RMKT-PUSH-TC-TRACKS',
        'MLB-I-M-XT1-PUSH-NIA-3P-PREVENDAS2026-AQUIS-MELIMUSIC-3107',
        'MLB_MP_WSPP-WAP_CAR_CRED-CAR_REQ_I-EG_RMKT_TC'
      )
      OR CAMPAIGN_NAME LIKE '%TC-AQS%' OR CAMPAIGN_NAME LIKE '%TCAQS%' OR CAMPAIGN_NAME LIKE '%TCADQ%'
      OR CAMPAIGN_NAME LIKE '%TCAQUI%' OR CAMPAIGN_NAME LIKE '%TC_AQS%' OR CAMPAIGN_NAME LIKE '%TCAQUISICAO%'
      OR UPPER(CAMPAIGN_NAME) LIKE '%FLOWS_COMMUNICATION_ELDO%ML_%'
    )
  GROUP BY 1, 2
),

proposal_first_event AS (
  SELECT
    p.ccard_prop_id,
    ANY_VALUE(FORMAT_DATE('%Y%m', p.DT_ENCENDIDO))     AS anomes_encendido,
    ANY_VALUE(p.app_instalado_encendido)               AS app_instalado_encendido,
    ANY_VALUE(p.flag_reencendido)                      AS flag_reencendido,
    ANY_VALUE(p.status_limite_reenc)                   AS status_limite_reenc,
    ANY_VALUE(p.FLAG_TC)                               AS flag_tc,
    ANY_VALUE(p.flag_ea)                               AS flag_ea,
    DATE_DIFF(CURRENT_DATE, ANY_VALUE(p.DT_ENCENDIDO), DAY) AS dias_desde_encendido,
    DATE_DIFF(MIN(CASE WHEN c.fl_sent          THEN c.sent_date END), ANY_VALUE(p.DT_ENCENDIDO), DAY) AS dias_ate_sent,
    DATE_DIFF(MIN(CASE WHEN c.fl_sent_push     THEN c.sent_date END), ANY_VALUE(p.DT_ENCENDIDO), DAY) AS dias_ate_sent_push,
    DATE_DIFF(MIN(CASE WHEN c.fl_sent_email    THEN c.sent_date END), ANY_VALUE(p.DT_ENCENDIDO), DAY) AS dias_ate_sent_email,
    DATE_DIFF(MIN(CASE WHEN c.fl_sent_whatsapp THEN c.sent_date END), ANY_VALUE(p.DT_ENCENDIDO), DAY) AS dias_ate_sent_whatsapp,
    DATE_DIFF(MIN(CASE WHEN c.fl_shown         THEN c.sent_date END), ANY_VALUE(p.DT_ENCENDIDO), DAY) AS dias_ate_shown
  FROM proposal_enriquecida p
  LEFT JOIN comunic c
    ON p.cus_cust_id = c.cus_cust_id
   AND c.sent_date BETWEEN p.DT_ENCENDIDO AND p.DT_FIM_JANELA
  WHERE p.DT_ENCENDIDO >= '2026-01-01'
  GROUP BY p.ccard_prop_id
),

days_seq AS (
  SELECT day FROM UNNEST(GENERATE_ARRAY(0, 30)) AS day
),

cohort_totals AS (
  SELECT
    anomes_encendido, app_instalado_encendido, flag_reencendido, status_limite_reenc, flag_tc, flag_ea,
    COUNT(DISTINCT ccard_prop_id) AS total_safra,
    MAX(dias_desde_encendido) AS dias_maturidade
  FROM proposal_first_event
  GROUP BY 1, 2, 3, 4, 5, 6
)

SELECT
  wd.anomes_encendido,
  wd.app_instalado_encendido,
  wd.flag_reencendido,
  wd.status_limite_reenc,
  wd.flag_tc,
  wd.flag_ea,
  d.day,
  ct.total_safra,
  ct.dias_maturidade,
  COUNT(DISTINCT CASE WHEN wd.dias_ate_sent          <= d.day THEN wd.ccard_prop_id END) AS qtd_sent_by_day,
  COUNT(DISTINCT CASE WHEN wd.dias_ate_sent_push     <= d.day THEN wd.ccard_prop_id END) AS qtd_sent_push_by_day,
  COUNT(DISTINCT CASE WHEN wd.dias_ate_sent_email    <= d.day THEN wd.ccard_prop_id END) AS qtd_sent_email_by_day,
  COUNT(DISTINCT CASE WHEN wd.dias_ate_sent_whatsapp <= d.day THEN wd.ccard_prop_id END) AS qtd_sent_whatsapp_by_day,
  COUNT(DISTINCT CASE WHEN wd.dias_ate_shown         <= d.day THEN wd.ccard_prop_id END) AS qtd_shown_by_day
FROM proposal_first_event wd
CROSS JOIN days_seq d
JOIN cohort_totals ct
  ON  ct.anomes_encendido = wd.anomes_encendido AND ct.app_instalado_encendido = wd.app_instalado_encendido
  AND ct.flag_reencendido = wd.flag_reencendido AND ct.status_limite_reenc = wd.status_limite_reenc
  AND ct.flag_tc = wd.flag_tc AND ct.flag_ea = wd.flag_ea
GROUP BY 1, 2, 3, 4, 5, 6, 7, 8, 9
ORDER BY 1, 2, 3, 4, 5, 6, 7
