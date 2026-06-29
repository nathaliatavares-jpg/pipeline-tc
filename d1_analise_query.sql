WITH

proposal_ajustada AS (
  SELECT
    CAST(A.CCARD_PROP_CREATION_DT AS DATE)  AS DT_ENCENDIDO,
    CCARD_PROP_STATUS,
    CAST(A.CCARD_PROP_UPDATE_DT AS DATE)    AS DT_CONV,
    SAFE_CAST(A.CUS_CUST_ID AS INT64)       AS cus_cust_id,
    A.CCARD_PROP_ID,
    CASE WHEN A.CCARD_GLOBAL_LIMIT_AMT_LC <= 100 OR CCARD_PRODUCT_ID = 5
         THEN '2. Micro TC' ELSE '1. TC Full' END                              AS FLAG_TC,
    CASE WHEN A.CCARD_PROP_STATUS = 'accepted'
         THEN '1. Convertido' ELSE '2. Nao Convertido' END                     AS FLAG_CONVERSAO,
    CASE
      WHEN LAG(CCARD_GLOBAL_LIMIT_AMT_LC,1) OVER(PARTITION BY A.CUS_CUST_ID ORDER BY A.CCARD_PROP_CREATION_DT) IS NULL
           THEN 'Primeira Proposta'
      ELSE 'Reencendido'
    END AS flag_encen,
    bureaus.FLAG_APP_ATIVO,
    bureaus.nise_tag,
    bureaus.rating_tc
  FROM `meli-bi-data.WHOWNER.BT_CCARD_PROPOSAL` A
  LEFT JOIN `meli-bi-data.SBOX_CREDITSTC.SCORE_PROPOSTAS_CCARD` bureaus
    ON bureaus.CCARD_PROP_ID = A.CCARD_PROP_ID
  WHERE A.SIT_SITE_ID = 'MLB'
    AND CAST(A.CCARD_PROP_CREATION_DT AS DATE) >= '2024-01-01'
),

proposals AS (
  SELECT DISTINCT
    prop.cus_cust_id,
    prop.CCARD_PROP_ID,
    prop.DT_ENCENDIDO            AS data_encendido,
    prop.DT_CONV                 AS data_update,
    prop.flag_encen,
    FORMAT_DATE('%Y-%m', prop.DT_ENCENDIDO) AS safra,
    prop.CCARD_PROP_STATUS,
    prop.FLAG_CONVERSAO          AS flag_conv,
    COALESCE(prop.FLAG_APP_ATIVO,'Sem Info') AS flag_app_ativo,
    COALESCE(prop.nise_tag, 'Sem Info') AS nise_tag,
    CASE
      WHEN LEFT(prop.rating_tc, 1) = 'A' THEN 'A'
      WHEN LEFT(prop.rating_tc, 1) = 'B' THEN 'B'
      WHEN LEFT(prop.rating_tc, 1) = 'C' THEN 'C'
      WHEN prop.rating_tc IS NULL         THEN 'Sem Info'
      ELSE 'Outros'
    END AS rating_tc
  FROM proposal_ajustada prop
  WHERE prop.DT_ENCENDIDO >= '2026-01-01'
    AND prop.FLAG_TC = '1. TC Full'
),

comunic_d1 AS (
  SELECT
    NT.CUS_CUST_ID,
    CAST(SENT_DATE AS DATE)             AS sent_date,
    COUNTIF(EVENT_TYPE = 'test')    > 0 AS fl_sent,
    COUNTIF(EVENT_TYPE = 'arrived') > 0 AS fl_arrived,
    COUNTIF(EVENT_TYPE = 'shown')   > 0 AS fl_shown,
    COUNTIF(EVENT_TYPE = 'open')    > 0 AS fl_open
  FROM `meli-bi-data.SBOX_MARKETING.BT_OC_CUST_EVENT` NT
  LEFT JOIN `meli-bi-data.WHOWNER.LK_OC_MERCURIO_CONTENTS` B
    ON CAST(NT.COMMUNICATION_ID AS STRING) = CAST(B.CAMPAIGN_ID AS STRING)
  WHERE NT.SIT_SITE_ID = 'MLB'
    AND NT.FLAG_NOTIFICATION_CENTER = 'N'
    AND NT.EVENT_TYPE IN ('test','shown','open','arrived')
    AND CAST(SENT_DATE AS DATE) >= '2026-01-01'
    AND (
      CAMPAIGN_NAME = 'MLB-ML-I-EG-XSELLT1-PUSH-NIA-CCARDACQ-D1'
      OR CAMPAIGN_NAME LIKE '%MLB_I_EG_NEW_TC_SOL_ENC%'
    )
    AND NOTIFICATION_TITLE_DESC = 'Seu cartão de Crédito chegou 💳'
    AND NOTIFICATION_TEXT_DESC  = 'Parcele em até 18x sem juros no Mercado Livre com anuidade grátis, de verdade. Peça já!'
  GROUP BY NT.CUS_CUST_ID, CAST(SENT_DATE AS DATE)
),

joined AS (
  SELECT
    p.safra,
    p.CCARD_PROP_ID,
    p.flag_conv,
    p.flag_encen,
    p.flag_app_ativo,
    p.nise_tag,
    p.rating_tc,
    p.data_update,
    p.CCARD_PROP_STATUS,

    -- primeiro dia que a D1 foi RECEBIDA (arrived) dentro da janela da proposta
    MIN(CASE
      WHEN c.fl_arrived
        AND c.sent_date BETWEEN p.data_encendido
            AND CASE WHEN p.CCARD_PROP_STATUS = 'pending'
                     THEN CURRENT_DATE() ELSE p.data_update END
      THEN c.sent_date
    END) AS data_primeira_d1,

    -- flags de funil (ever, dentro da janela)
    MAX(CASE WHEN c.fl_sent
             AND c.sent_date BETWEEN p.data_encendido
                 AND CASE WHEN p.CCARD_PROP_STATUS = 'pending' THEN CURRENT_DATE() ELSE p.data_update END
             THEN TRUE ELSE FALSE END) AS teve_sent,
    MAX(CASE WHEN c.fl_arrived
             AND c.sent_date BETWEEN p.data_encendido
                 AND CASE WHEN p.CCARD_PROP_STATUS = 'pending' THEN CURRENT_DATE() ELSE p.data_update END
             THEN TRUE ELSE FALSE END) AS teve_arrived,
    MAX(CASE WHEN c.fl_shown
             AND c.sent_date BETWEEN p.data_encendido
                 AND CASE WHEN p.CCARD_PROP_STATUS = 'pending' THEN CURRENT_DATE() ELSE p.data_update END
             THEN TRUE ELSE FALSE END) AS teve_shown,
    MAX(CASE WHEN c.fl_open
             AND c.sent_date BETWEEN p.data_encendido
                 AND CASE WHEN p.CCARD_PROP_STATUS = 'pending' THEN CURRENT_DATE() ELSE p.data_update END
             THEN TRUE ELSE FALSE END) AS teve_open

  FROM proposals p
  LEFT JOIN comunic_d1 c ON p.cus_cust_id = c.CUS_CUST_ID
  GROUP BY ALL
)

SELECT
  safra,
  flag_conv,
  flag_encen,
  flag_app_ativo,
  nise_tag,
  rating_tc,
  CASE
    WHEN teve_open    THEN '4. Abriu (Open)'
    WHEN teve_shown   THEN '3. Viu (Shown)'
    WHEN teve_arrived THEN '2. Recebeu (Arrived)'
    WHEN teve_sent    THEN '1. Enviou (Sent)'
    ELSE                   '0. Sem comunicacao'
  END AS melhor_etapa_funil,

  COUNT(DISTINCT CCARD_PROP_ID)  AS qtd_total,

  -- conversao ever (estado atual da proposta)
  COUNTIF(flag_conv = '1. Convertido')  AS conv_ever,

  -- conversao dentro de N dias de ter RECEBIDO a D1
  COUNTIF(flag_conv = '1. Convertido'
          AND data_primeira_d1 IS NOT NULL
          AND DATE_DIFF(data_update, data_primeira_d1, DAY) <= 1)  AS conv_1d,
  COUNTIF(flag_conv = '1. Convertido'
          AND data_primeira_d1 IS NOT NULL
          AND DATE_DIFF(data_update, data_primeira_d1, DAY) <= 2)  AS conv_2d,
  COUNTIF(flag_conv = '1. Convertido'
          AND data_primeira_d1 IS NOT NULL
          AND DATE_DIFF(data_update, data_primeira_d1, DAY) <= 3)  AS conv_3d,
  COUNTIF(flag_conv = '1. Convertido'
          AND data_primeira_d1 IS NOT NULL
          AND DATE_DIFF(data_update, data_primeira_d1, DAY) <= 5)  AS conv_5d,
  COUNTIF(flag_conv = '1. Convertido'
          AND data_primeira_d1 IS NOT NULL
          AND DATE_DIFF(data_update, data_primeira_d1, DAY) <= 7)  AS conv_7d

FROM joined
GROUP BY ALL
ORDER BY safra, melhor_etapa_funil, flag_conv
