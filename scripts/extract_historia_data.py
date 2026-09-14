import re, json

# ---- Slide 2: D1 sent%, App Ativo = ML, por Full/Micro ----
content = open(r'C:\Users\nathtavares\dash_funil_comunic.html', encoding='utf-8').read()
start = content.index('const DATA = [')
end = content.index('];', start)
block = content[start:end]
rows = re.findall(
    r'\{ anomes_encendido: "(\d+)", campaign: "([^"]*)", flag_app_ativo: "([^"]*)", flag_tc: "([^"]*)", '
    r'segmento: "([^"]*)", flag_ea: "[^"]*", titulos: "[^"]*", corpos: "[^"]*", '
    r'qtd_total_encendido: (\d+), qtd_sent: (\d+),', block)

from collections import defaultdict
TC_FOR_CAMPAIGN = {'D1 FULL': '1. TC Full', 'D1 MICRO': '2. Micro TC'}
# qtd_total_encendido se repete identico entre as linhas de COM EA / SEM EA do mesmo
# segmento (o total e por segmento, nao por linha de EA) -- por isso agregamos primeiro
# por segmento (tomando o total uma unica vez, mas somando qtd_sent das duas linhas de EA),
# e só depois somamos os segmentos. Somar qtd_total_encendido direto por linha (sem passar
# por essa etapa) conta o denominador em dobro e derruba a % por ~2x -- foi o bug encontrado
# ao comparar com o dash_funil_comunic.html (screenshot da Nathalia mostrando ~67% pra D1
# MICRO/jan, contra os ~34% que essa extração dava antes do fix).
seg_agg = defaultdict(lambda: [0, 0])
for mes, campaign, app, tc, segmento, tot_enc, sent in rows:
    if app == '3. ML' and campaign in TC_FOR_CAMPAIGN and tc == TC_FOR_CAMPAIGN[campaign]:
        key = (mes, campaign, segmento)
        seg_agg[key][0] = max(seg_agg[key][0], int(tot_enc))
        seg_agg[key][1] += int(sent)

d1_agg = defaultdict(lambda: [0, 0])
for (mes, campaign, segmento), (tot, sent) in seg_agg.items():
    d1_agg[(mes, campaign)][0] += tot
    d1_agg[(mes, campaign)][1] += sent

MESES = ['202601', '202602', '202603', '202604', '202605', '202606', '202607', '202608', '202609']
D1_DATA = {'FULL': {}, 'MICRO': {}}
for mes in MESES:
    tot, sent = d1_agg[(mes, 'D1 FULL')]
    D1_DATA['FULL'][mes] = round(100 * sent / tot, 1) if tot else None
    tot, sent = d1_agg[(mes, 'D1 MICRO')]
    D1_DATA['MICRO'][mes] = round(100 * sent / tot, 1) if tot else None

# ---- Slide 4: % Recebimento por App Ativo, Sem EA-MP, por Full/Micro ----
content2 = open(r'C:\Users\nathtavares\dash_encendidos_v3.html', encoding='utf-8').read()
start2 = content2.index('const DATA = [')
end2 = content2.index('];', start2)
block2 = content2[start2:end2]
rows2 = re.findall(
    r'\{ anomes_encendido: "(\d+)", app_instalado: "([^"]*)", flag_reencendido: "[^"]*", '
    r'status_limite: "[^"]*", flag_tc: "([^"]*)", flag_ea: "([^"]*)", qtd_total_encendido: (\d+), qtd_sent: (\d+),',
    block2)

receb_agg = defaultdict(lambda: [0, 0])
for mes, app, tc, ea, tot, sent in rows2:
    if ea == '2. Sem EA-MP':
        receb_agg[(mes, app, tc)][0] += int(tot)
        receb_agg[(mes, app, tc)][1] += int(sent)

APP_MAP = {'1. MP': 'MP', '2. ML': 'ML', '3. Sem App': 'SemApp'}
TC_MAP = {'1. TC Full': 'FULL', '2. Micro TC': 'MICRO'}
RECEBIMENTO_DATA = {'FULL': {}, 'MICRO': {}}
for tc_full, tc_key in TC_MAP.items():
    for mes in MESES:
        RECEBIMENTO_DATA[tc_key][mes] = {}
        for app_full, app_key in APP_MAP.items():
            tot, sent = receb_agg[(mes, app_full, tc_full)]
            RECEBIMENTO_DATA[tc_key][mes][app_key] = round(100 * sent / tot, 1) if tot else None

# ---- Slide 7: Conversao por BU (MP vs ML), Sem EA, Automatizada+MKT, por Full/Micro ----
blob = json.load(open(r'C:\Users\nathtavares\dash_data_blob.json', encoding='utf-8'))
t = blob['TIPO_BY_BU_TC_CANAL']
canais = ['AUTOMATIZADA', 'MKT']
BU_DATA = {'FULL': {}, 'MICRO': {}}
for tc in ['FULL', 'MICRO']:
    mp_total = [0] * 8
    ml_total = [0] * 8
    for canal in canais:
        node_mp = t['MP'][tc][canal]
        node_ml = t['ML'][tc][canal]
        for tipo, arr in node_mp.items():
            for i in range(8):
                mp_total[i] += arr[i]
        for tipo, arr in node_ml.items():
            for i in range(8):
                ml_total[i] += arr[i]
    for i, mes in enumerate(MESES[:8]):
        BU_DATA[tc][mes] = {'MP': mp_total[i], 'ML': ml_total[i]}

# ---- Slide 4 (extra): Total -- Antes (Jan,Mar-Mai sem Fev) vs Agora (Jun+), Sem EA-MP ----
# Replica a mesma agregacao ja usada em renderVelocidadeDelta()/aggBySafraDay() do proprio
# dash_encendidos_v3.html (aba Velocidade por Safra): total_safra e qtd_sent_by_day sao
# somados por (safra, dia) ignorando app_instalado (isso dá o "Total"), e o filtro fica so
# em flag_ea (Sem EA-MP) -- Tipo TC fica em "Todos" (soma Full+Micro), igual ao chart nativo.
content3 = open(r'C:\Users\nathtavares\dash_encendidos_v3.html', encoding='utf-8').read()
start3 = content3.index('const DATA_VEL = [')
end3 = content3.index('];', start3)
block3 = content3[start3:end3]
rows3 = re.findall(
    r'\{ anomes_encendido: "(\d+)", app_instalado: "[^"]*", flag_reencendido: "[^"]*", status_limite: "[^"]*", '
    r'flag_tc: "([^"]*)", flag_ea: "([^"]*)", day: (\d+), total_safra: (\d+), dias_maturidade: (\d+), '
    r'qtd_sent_by_day: (\d+),', block3)

DIAS_VEL = list(range(0, 31))

def media_grupo(vel_agg, safras_grupo):
    out_list = []
    for d in DIAS_VEL:
        num = 0; den = 0
        for safra in safras_grupo:
            g = vel_agg.get(safra)
            if not g or d > g['maturidade']:
                continue
            num += g['byDay'].get(d, 0)
            den += g['totals'].get(d, 0)
        out_list.append(round(100 * num / den, 1) if den else None)
    return out_list

VEL_DELTA_DATA = {}
for tc_key, tc_full in {'FULL': '1. TC Full', 'MICRO': '2. Micro TC'}.items():
    vel_agg = {}
    for mes, tc, ea, day, total_safra, maturidade, sent in rows3:
        if ea != '2. Sem EA-MP' or tc != tc_full:
            continue
        day = int(day); total_safra = int(total_safra); maturidade = int(maturidade); sent = int(sent)
        g = vel_agg.setdefault(mes, {'maturidade': 0, 'byDay': {}, 'totals': {}})
        g['maturidade'] = max(g['maturidade'], maturidade)
        g['byDay'][day] = g['byDay'].get(day, 0) + sent
        g['totals'][day] = g['totals'].get(day, 0) + total_safra

    todas_safras = sorted(vel_agg.keys())
    safras_antes = [s for s in todas_safras if s <= '202605' and s != '202602']
    safras_depois = [s for s in todas_safras if s >= '202606']
    VEL_DELTA_DATA[tc_key] = {
        'dias': DIAS_VEL,
        'antes': media_grupo(vel_agg, safras_antes),
        'depois': media_grupo(vel_agg, safras_depois),
    }
    print(f'VEL_DELTA_DATA[{tc_key}] antes D0/D9/D30:', VEL_DELTA_DATA[tc_key]['antes'][0], VEL_DELTA_DATA[tc_key]['antes'][9], VEL_DELTA_DATA[tc_key]['antes'][30])
    print(f'VEL_DELTA_DATA[{tc_key}] depois D0/D9/D30:', VEL_DELTA_DATA[tc_key]['depois'][0], VEL_DELTA_DATA[tc_key]['depois'][9], VEL_DELTA_DATA[tc_key]['depois'][30])

# ---- Slides 5/6/8: reaproveita jsons ja existentes do dash_incremental_por_canal ----
INCREMENTAL_DATA = json.load(open(r'C:\Users\nathtavares\incremental_por_canal_data.json', encoding='utf-8'))
TOTAL_CONV = json.load(open(r'C:\Users\nathtavares\total_conversoes_mes.json', encoding='utf-8'))
COMUNIC_DATA = json.load(open(r'C:\Users\nathtavares\comunicacoes_por_proposta_data.json', encoding='utf-8'))
DIST_DATA = json.load(open(r'C:\Users\nathtavares\distribuicao_comunicacoes_data.json', encoding='utf-8'))

out = {
    'D1_DATA': D1_DATA,
    'RECEBIMENTO_DATA': RECEBIMENTO_DATA,
    'VEL_DELTA_DATA': VEL_DELTA_DATA,
    'BU_DATA': BU_DATA,
    'INCREMENTAL_DATA': INCREMENTAL_DATA,
    'TOTAL_CONV': TOTAL_CONV,
    'COMUNIC_DATA': COMUNIC_DATA,
    'DIST_DATA': DIST_DATA,
}
json.dump(out, open(r'C:\Users\nathtavares\historia_data.json', 'w', encoding='utf-8'), ensure_ascii=False)
print('D1_DATA', D1_DATA)
print('RECEBIMENTO_DATA FULL jan/ago', RECEBIMENTO_DATA['FULL']['202601'], RECEBIMENTO_DATA['FULL']['202608'])
print('BU_DATA FULL jan/ago', BU_DATA['FULL']['202601'], BU_DATA['FULL']['202608'])
print('OK -- historia_data.json escrito')
