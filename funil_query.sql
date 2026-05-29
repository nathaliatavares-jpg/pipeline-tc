WITH

proposal_ajustada AS (
  SELECT
    CAST(A.CCARD_PROP_CREATION_DT AS DATE) AS DT_ENCENDIDO,
    CASE WHEN CAST(A.CCARD_PROP_CREATION_DT AS DATE) < '2023-09-01'
         THEN DATE '2023-09-01'
         ELSE CAST(A.CCARD_PROP_CREATION_DT AS DATE) END AS DT_ENCENDIDO_NISE,
    ccard_prop_status,
    CAST(A.CCARD_PROP_UPDATE_DT AS DATE) AS DT_CONV,
    SAFE_CAST(A.CUS_CUST_ID AS INT64) AS cus_cust_id,
    a.ccard_prop_id,
    CASE WHEN A.CCARD_GLOBAL_LIMIT_AMT_LC <= 100 OR CCARD_PRODUCT_ID = 5
         THEN '2. Micro TC' ELSE '1. TC Full' END AS FLAG_TC,
    CASE WHEN A.CCARD_PROP_STATUS = 'accepted'
         THEN '1. Convertido' ELSE '2. Nao Convertido' END AS FLAG_CONVERSAO,
    CASE WHEN A.CCARD_PROP_STATUS = 'accepted'
         THEN DATE_DIFF(CAST(A.CCARD_PROP_UPDATE_DT AS DATE), CAST(A.CCARD_PROP_CREATION_DT AS DATE), DAY)
         ELSE NULL END AS DIAS_CONV,
    CASE
      WHEN LAG(CCARD_GLOBAL_LIMIT_AMT_LC,1) OVER(PARTITION BY cus_cust_id ORDER BY ccard_prop_creation_dt) > CCARD_GLOBAL_LIMIT_AMT_LC THEN 'Downsell'
      WHEN LAG(CCARD_GLOBAL_LIMIT_AMT_LC,1) OVER(PARTITION BY cus_cust_id ORDER BY ccard_prop_creation_dt) = CCARD_GLOBAL_LIMIT_AMT_LC THEN 'Mesmo Limite que Anterior'
      WHEN LAG(CCARD_GLOBAL_LIMIT_AMT_LC,1) OVER(PARTITION BY cus_cust_id ORDER BY ccard_prop_creation_dt) < CCARD_GLOBAL_LIMIT_AMT_LC THEN 'Upsell'
      WHEN LAG(CCARD_GLOBAL_LIMIT_AMT_LC,1) OVER(PARTITION BY cus_cust_id ORDER BY ccard_prop_creation_dt) IS NULL THEN 'Primeira Proposta'
    END AS status_limite_reenc,
    CASE WHEN
      MIN(CASE WHEN ccard_prop_status = 'accepted' THEN CAST(ccard_prop_creation_dt AS DATE) ELSE DATE '2099-01-01' END)
        OVER(PARTITION BY cus_cust_id ORDER BY ccard_prop_creation_dt) < CAST(A.CCARD_PROP_CREATION_DT AS DATE)
      THEN TRUE ELSE FALSE END AS status_cancelada_anteriormente,
    LAG(ccard_prop_creation_dt,1) OVER(PARTITION BY cus_cust_id ORDER BY ccard_prop_creation_dt) AS data_ultimo_encendido,
    LAG(CCARD_PROP_UPDATE_DT,1)   OVER(PARTITION BY cus_cust_id ORDER BY ccard_prop_creation_dt) AS data_ultimo_apagado,
    A.CCARD_GLOBAL_LIMIT_AMT_LC AS ccard_global_limit_amt_lc,
    LAG(CCARD_GLOBAL_LIMIT_AMT_LC,1) OVER(PARTITION BY cus_cust_id ORDER BY ccard_prop_creation_dt) AS limite_anterior,
    cenc.campaign_group,
    cenc.campaign_group_desc,
    cenc.policy_description,
    bureaus.FLAG_APP_ATIVO
  FROM `meli-bi-data.WHOWNER.BT_CCARD_PROPOSAL` A
  LEFT JOIN (SELECT CCARD_PROP_ID, FLAG_APP_ATIVO FROM `meli-bi-data.SBOX_CREDITSTC.SCORE_PROPOSTAS_CCARD`) bureaus
    ON bureaus.CCARD_PROP_ID = A.ccard_prop_id
  LEFT JOIN (
    SELECT
      cus_cust_id            AS cenc_cust_id,
      anomes_encendido_riscos,
      campaign_group,
      campaign_group_desc,
      policy_description
    FROM `meli-bi-data.SBOX_CREDITSTC.CONTROLE_ENCENDIDOS_CCARD_MLB`
    QUALIFY ROW_NUMBER() OVER(PARTITION BY cus_cust_id, DATE_TRUNC(fecha_encendido, MONTH) ORDER BY fecha_encendido DESC) = 1
  ) AS cenc
    ON  cenc.cenc_cust_id = SAFE_CAST(A.CUS_CUST_ID AS INT64)
    AND FORMAT_DATE('%Y%m', CAST(A.CCARD_PROP_CREATION_DT AS DATE)) = cenc.anomes_encendido_riscos
  WHERE A.sit_site_id = 'MLB'
),

comunic AS (
  SELECT
    CASE
      WHEN CAMPAIGN_NAME = 'MLB-ML-I-EG-XSELLT1-PUSH-NIA-CCARDACQ-D1'
           AND NOTIFICATION_TITLE_DESC = 'Seu cartão de Crédito chegou 💳'
           AND NOTIFICATION_TEXT_DESC  = 'Parcele em até 18x sem juros no Mercado Livre com anuidade grátis, de verdade. Peça já!'
                                                                          THEN 'D1 FULL'
      WHEN CAMPAIGN_NAME = 'MLB-ML-I-EG-XSELLT1-PUSH-NIA-CCARDACQ-D1'
           AND NOTIFICATION_TITLE_DESC = 'Cartão sem anuidade liberado 💳'
           AND NOTIFICATION_TEXT_DESC  = 'Peça grátis seu Cartão de Crédito Mercado Pago e compre no Mercado Livre em até 18x sem juros.'
                                                                          THEN 'D4 FULL'
      WHEN CAMPAIGN_NAME = 'MLB-ML-I-EG-XSELLT1-PUSH-CCARDACQ-D1-MIC'   THEN 'D1 MICRO'
      WHEN CAMPAIGN_NAME = 'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-D6-MIC'        THEN 'D6 MICRO'
      WHEN CAMPAIGN_NAME = 'MLB_MP_ML-PUSHML_CCC_X_AO-ACQ_ALL_TXS_X_X_DEFAULT_C-EG-CCARDACQ-SIN-TC-ENR-ML' THEN 'D10 FULL'
      WHEN CAMPAIGN_NAME = 'MLB-MP-I-EG-XSELLT1-PUSH-SOL-TC2'            THEN 'D10 FULL'
      WHEN CAMPAIGN_NAME = 'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-D14-MIC'       THEN 'D14 MICRO'
      WHEN CAMPAIGN_NAME = ' MLB-ML-C-EG-ACT-PUSH-CCARDACQ-BARRIDA'      THEN 'VARRIDA FULL'
      WHEN CAMPAIGN_NAME = 'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-BARRIDA-MI'    THEN 'VARRIDA MICRO'
      WHEN CAMPAIGN_NAME = 'MLB-ML-C-EG-ACT-PUSH-CCARDACQ-UP1'           THEN 'UPSELL'
      WHEN CAMPAIGN_NAME = 'MLB-ML-C-EG-ACT-CCARDACQ-SIN-TC-ENR-ML'      THEN 'NAVEGOU ML'
      WHEN CAMPAIGN_NAME LIKE '%MLB_I_EG_NEW_TC_SOL_ENC%'
           AND NOTIFICATION_TITLE_DESC = 'Seu cartão de Crédito chegou 💳'
           AND NOTIFICATION_TEXT_DESC  = 'Parcele em até 18x sem juros no Mercado Livre com anuidade grátis, de verdade. Peça já!'
                                                                          THEN 'D1 FULL'
      WHEN CAMPAIGN_NAME LIKE '%MLB_I_EG_NEW_TC_SOL_ENC%'
           AND NOTIFICATION_TITLE_DESC = 'Cartão sem anuidade liberado 💳'
           AND NOTIFICATION_TEXT_DESC  = 'Peça grátis seu Cartão de Crédito Mercado Pago e compre no Mercado Livre em até 18x sem juros.'
                                                                          THEN 'D4 FULL'
      ELSE CAMPAIGN_NAME
    END AS CAMPAIGN,
    NOTIFICATION_TITLE_DESC,
    NOTIFICATION_TEXT_DESC,
    cus_cust_id,
    CAST(SENT_DATE AS DATE)             AS sent_date,
    COUNTIF(EVENT_TYPE = 'arrived') > 0 AS fl_arrived,
    COUNTIF(EVENT_TYPE = 'shown')   > 0 AS fl_shown,
    COUNTIF(EVENT_TYPE = 'open')    > 0 AS fl_open
  FROM `meli-bi-data.SBOX_MARKETING.BT_OC_CUST_EVENT` NT
  LEFT JOIN `meli-bi-data.WHOWNER.LK_OC_MERCURIO_CONTENTS` B
    ON CAST(NT.COMMUNICATION_ID AS STRING) = CAST(B.CAMPAIGN_ID AS STRING)
  WHERE
    SENT_DATE BETWEEN '2026-01-01' AND CURRENT_DATE - 1
    AND NT.SIT_SITE_ID = 'MLB'
    AND FLAG_NOTIFICATION_CENTER = 'N'
    AND EVENT_TYPE IN ('shown','open','arrived','control')
    AND (
      CAMPAIGN_NAME IN (
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
      OR CAMPAIGN_NAME LIKE '%MLB_I_EG_NEW_TC_SOL_ENC%'
      OR CAMPAIGN_NAME LIKE '%MLB_I_EG_XSELLT1_T_TC_SOL_UP%'
      OR CAMPAIGN_NAME LIKE '%MLB_I_EG_XSELLT1_T_TC_SOL_ST%'
      OR CAMPAIGN_NAME LIKE '%MLB_I_EG_XSELLT1_T_TC_SOL_ENC%'
    )
  GROUP BY CAMPAIGN, NOTIFICATION_TITLE_DESC, NOTIFICATION_TEXT_DESC, cus_cust_id, CAST(SENT_DATE AS DATE)
),

total_enc AS (
  SELECT
    CAST(DT_ENCENDIDO AS STRING FORMAT 'YYYYMM') AS anomes_encendido,
    FLAG_APP_ATIVO,
    FLAG_TC,
    COUNT(DISTINCT ccard_prop_id) AS qtd_total_encendido
  FROM proposal_ajustada
  WHERE DT_ENCENDIDO >= '2026-01-01'
  GROUP BY 1, 2, 3
)

SELECT
    CAST(prop.DT_ENCENDIDO AS STRING FORMAT 'YYYYMM')                                     AS anomes_encendido,
    c.CAMPAIGN                                                                             AS campaign,
    prop.FLAG_APP_ATIVO                                                                    AS flag_app_ativo,
    prop.FLAG_TC                                                                           AS flag_tc,
    STRING_AGG(DISTINCT c.NOTIFICATION_TITLE_DESC, ' | ' ORDER BY c.NOTIFICATION_TITLE_DESC) AS titulos,
    STRING_AGG(DISTINCT c.NOTIFICATION_TEXT_DESC,  ' | ' ORDER BY c.NOTIFICATION_TEXT_DESC)  AS corpos,
    ANY_VALUE(te.qtd_total_encendido)                                                      AS qtd_total_encendido,
    COUNT(DISTINCT CASE WHEN c.fl_arrived THEN prop.ccard_prop_id END)                      AS qtd_arrived,
    COUNT(DISTINCT CASE WHEN c.fl_shown   THEN prop.ccard_prop_id END)                      AS qtd_shown,
    COUNT(DISTINCT CASE WHEN c.fl_open    THEN prop.ccard_prop_id END)                      AS qtd_open,
    COUNT(DISTINCT CASE WHEN c.fl_shown AND prop.FLAG_CONVERSAO = '1. Convertido' THEN prop.ccard_prop_id END) AS qtd_conv_shown,
    COUNT(DISTINCT CASE WHEN c.fl_open  AND prop.FLAG_CONVERSAO = '1. Convertido' THEN prop.ccard_prop_id END) AS qtd_conv_open
FROM proposal_ajustada prop
LEFT JOIN comunic c
    ON  prop.cus_cust_id = c.cus_cust_id
    AND c.sent_date BETWEEN prop.DT_ENCENDIDO
                        AND CASE WHEN prop.ccard_prop_status <> 'pending' THEN prop.DT_CONV ELSE CURRENT_DATE END
LEFT JOIN total_enc te
    ON  CAST(prop.DT_ENCENDIDO AS STRING FORMAT 'YYYYMM') = te.anomes_encendido
    AND prop.FLAG_APP_ATIVO = te.FLAG_APP_ATIVO
    AND prop.FLAG_TC        = te.FLAG_TC
WHERE prop.DT_ENCENDIDO >= '2026-01-01'
GROUP BY
    CAST(prop.DT_ENCENDIDO AS STRING FORMAT 'YYYYMM'),
    c.CAMPAIGN,
    prop.FLAG_APP_ATIVO,
    prop.FLAG_TC
ORDER BY anomes_encendido, campaign, flag_tc, flag_app_ativo
