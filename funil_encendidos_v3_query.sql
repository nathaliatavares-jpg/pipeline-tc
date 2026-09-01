-- v3 — base enxuta pra começar: mesma proposal (todos os status, janela do encendido até
-- conversão/cancelamento ou hoje se pending) e mesma lista de campanhas TC ADQ (Método A).
-- Saída: por mês de encendido x App Ativo x 1º Encendido/Reencendido x Upsell/Downsell/Mesmo
-- Limite x Tipo TC — total encendido, qtd que recebeu (sent) e qtd que viu (shown).

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
    END AS status_limite_reenc
  FROM `meli-bi-data.WHOWNER.BT_CCARD_PROPOSAL` A
  WHERE A.sit_site_id = 'MLB'
  -- NÃO filtrar data aqui: o LAG precisa do histórico completo do cliente pra classificar
  -- 1º Encendido vs Reencendido certo. Filtro de data entra só no SELECT final.
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
    -- janela de comunicação: pending -> encendido até hoje; senão -> encendido até data_update
    CASE WHEN p.CCARD_PROP_STATUS = 'pending' THEN CURRENT_DATE ELSE p.DT_CONV END AS DT_FIM_JANELA,
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

comunic_raw AS (
  SELECT
    cus_cust_id,
    CAST(SENT_DATE AS DATE) AS sent_date,
    EVENT_TYPE,
    CHANNEL,
    CASE
      WHEN CAMPAIGN_NAME = 'MLB-ML-I-EG-XSELLT1-PUSH-NIA-CCARDACQ-D1' THEN 'D1 FULL'
      WHEN CAMPAIGN_NAME = 'MLB-ML-I-EG-XSELLT1-PUSH-CCARDACQ-D1-MIC' THEN 'D1 MICRO'
      WHEN CAMPAIGN_NAME = 'flows_communication_MLB_I_EG_NEW_TC_SOL_ENC_mer_1t0' THEN 'D1 MICRO'
      WHEN CAMPAIGN_NAME LIKE '%MLB_I_EG_NEW_TC_SOL_ENC%' THEN 'D1 FULL'
      WHEN CAMPAIGN_NAME = 'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-D6-MIC' THEN 'D6 MICRO'
      WHEN CAMPAIGN_NAME = 'MLB-MP-I-EG-XSELLT1-PUSH-SOL-TC2' THEN 'D10 FULL'
      WHEN CAMPAIGN_NAME = 'MLB_MP_ML-PUSHML_CCC_X_AO-ACQ_ALL_TXS_X_X_DEFAULT_C-EG-CCARDACQ-SIN-TC-ENR-ML' THEN 'D10 FULL'
      WHEN CAMPAIGN_NAME = 'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-D14-MIC' THEN 'D14 MICRO'
      WHEN CAMPAIGN_NAME = 'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-BARRIDA' THEN 'VARRIDA FULL'
      WHEN CAMPAIGN_NAME = 'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-BARRIDA-MI' THEN 'VARRIDA MICRO'
      WHEN CAMPAIGN_NAME = 'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-UP1' THEN 'UPSELL'
      WHEN CAMPAIGN_NAME = 'MLB-ML-C-EG-ACT-CCARDACQ-SIN-TC-ENR-ML' THEN 'NAVEGOU ML'
      WHEN CAMPAIGN_NAME = 'MLB-I-M-XT1-PUSH-NIA-3P-PREVENDAS2026-AQUIS-MELIMUSIC-3107' THEN 'MELIMUSIC PREVENDAS'
      ELSE 'OUTRAS'
    END AS bucket
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
),

comunic AS (
  SELECT
    cus_cust_id,
    sent_date,
    LOGICAL_OR(EVENT_TYPE = 'test')                          AS fl_sent,
    LOGICAL_OR(EVENT_TYPE = 'test' AND CHANNEL = 'PUSH')      AS fl_sent_push,
    LOGICAL_OR(EVENT_TYPE = 'test' AND CHANNEL = 'EMAIL')     AS fl_sent_email,
    LOGICAL_OR(EVENT_TYPE = 'test' AND CHANNEL = 'WHATSAPP')  AS fl_sent_whatsapp,
    LOGICAL_OR(EVENT_TYPE = 'shown')                          AS fl_shown,
    LOGICAL_OR(EVENT_TYPE = 'shown' AND CHANNEL = 'PUSH')     AS fl_shown_push,
    LOGICAL_OR(EVENT_TYPE = 'shown' AND CHANNEL = 'EMAIL')    AS fl_shown_email,
    LOGICAL_OR(EVENT_TYPE = 'shown' AND CHANNEL = 'WHATSAPP') AS fl_shown_whatsapp,
    -- "recebeu de outro bucket que não X" -- pra testar corretamente (dedupado) o efeito de
    -- excluir uma campanha específica, sem inflar por overlap entre campanhas
    LOGICAL_OR(EVENT_TYPE = 'test' AND bucket != 'D1 FULL')             AS fl_sent_excl_d1full,
    LOGICAL_OR(EVENT_TYPE = 'test' AND bucket != 'D1 MICRO')            AS fl_sent_excl_d1micro,
    LOGICAL_OR(EVENT_TYPE = 'test' AND bucket != 'D6 MICRO')            AS fl_sent_excl_d6micro,
    LOGICAL_OR(EVENT_TYPE = 'test' AND bucket != 'D10 FULL')            AS fl_sent_excl_d10full,
    LOGICAL_OR(EVENT_TYPE = 'test' AND bucket != 'D14 MICRO')           AS fl_sent_excl_d14micro,
    LOGICAL_OR(EVENT_TYPE = 'test' AND bucket != 'VARRIDA FULL')        AS fl_sent_excl_varridafull,
    LOGICAL_OR(EVENT_TYPE = 'test' AND bucket != 'VARRIDA MICRO')       AS fl_sent_excl_varridamicro,
    LOGICAL_OR(EVENT_TYPE = 'test' AND bucket != 'UPSELL')              AS fl_sent_excl_upsell,
    LOGICAL_OR(EVENT_TYPE = 'test' AND bucket != 'NAVEGOU ML')          AS fl_sent_excl_navegouml,
    LOGICAL_OR(EVENT_TYPE = 'test' AND bucket != 'MELIMUSIC PREVENDAS') AS fl_sent_excl_melimusic,
    LOGICAL_OR(EVENT_TYPE = 'test' AND bucket != 'OUTRAS')              AS fl_sent_excl_outras
  FROM comunic_raw
  GROUP BY 1, 2
)

SELECT
  FORMAT_DATE('%Y%m', p.DT_ENCENDIDO)         AS anomes_encendido,
  p.app_instalado_encendido,
  p.flag_reencendido,
  p.status_limite_reenc,
  p.FLAG_TC,
  p.flag_ea,
  COUNT(DISTINCT p.ccard_prop_id)                                              AS qtd_total_encendido,
  COUNT(DISTINCT CASE WHEN c.fl_sent          THEN p.ccard_prop_id END)        AS qtd_sent,
  COUNT(DISTINCT CASE WHEN c.fl_sent_push     THEN p.ccard_prop_id END)        AS qtd_sent_push,
  COUNT(DISTINCT CASE WHEN c.fl_sent_email    THEN p.ccard_prop_id END)        AS qtd_sent_email,
  COUNT(DISTINCT CASE WHEN c.fl_sent_whatsapp THEN p.ccard_prop_id END)        AS qtd_sent_whatsapp,
  COUNT(DISTINCT CASE WHEN c.fl_shown          THEN p.ccard_prop_id END)       AS qtd_shown,
  COUNT(DISTINCT CASE WHEN c.fl_shown_push     THEN p.ccard_prop_id END)       AS qtd_shown_push,
  COUNT(DISTINCT CASE WHEN c.fl_shown_email    THEN p.ccard_prop_id END)       AS qtd_shown_email,
  COUNT(DISTINCT CASE WHEN c.fl_shown_whatsapp THEN p.ccard_prop_id END)       AS qtd_shown_whatsapp,
  COUNT(DISTINCT CASE WHEN c.fl_sent_excl_d1full       THEN p.ccard_prop_id END) AS qtd_sent_excl_d1full,
  COUNT(DISTINCT CASE WHEN c.fl_sent_excl_d1micro      THEN p.ccard_prop_id END) AS qtd_sent_excl_d1micro,
  COUNT(DISTINCT CASE WHEN c.fl_sent_excl_d6micro      THEN p.ccard_prop_id END) AS qtd_sent_excl_d6micro,
  COUNT(DISTINCT CASE WHEN c.fl_sent_excl_d10full      THEN p.ccard_prop_id END) AS qtd_sent_excl_d10full,
  COUNT(DISTINCT CASE WHEN c.fl_sent_excl_d14micro     THEN p.ccard_prop_id END) AS qtd_sent_excl_d14micro,
  COUNT(DISTINCT CASE WHEN c.fl_sent_excl_varridafull  THEN p.ccard_prop_id END) AS qtd_sent_excl_varridafull,
  COUNT(DISTINCT CASE WHEN c.fl_sent_excl_varridamicro THEN p.ccard_prop_id END) AS qtd_sent_excl_varridamicro,
  COUNT(DISTINCT CASE WHEN c.fl_sent_excl_upsell       THEN p.ccard_prop_id END) AS qtd_sent_excl_upsell,
  COUNT(DISTINCT CASE WHEN c.fl_sent_excl_navegouml    THEN p.ccard_prop_id END) AS qtd_sent_excl_navegouml,
  COUNT(DISTINCT CASE WHEN c.fl_sent_excl_melimusic    THEN p.ccard_prop_id END) AS qtd_sent_excl_melimusic,
  COUNT(DISTINCT CASE WHEN c.fl_sent_excl_outras       THEN p.ccard_prop_id END) AS qtd_sent_excl_outras
FROM proposal_enriquecida p
LEFT JOIN comunic c
  ON p.cus_cust_id = c.cus_cust_id
 AND c.sent_date BETWEEN p.DT_ENCENDIDO AND p.DT_FIM_JANELA
WHERE p.DT_ENCENDIDO >= '2026-01-01'
GROUP BY 1, 2, 3, 4, 5, 6
ORDER BY 1, 2, 3, 4, 5, 6
