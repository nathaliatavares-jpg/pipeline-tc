import csv

CSV_PATH = r'C:\Users\NATHTA~1\AppData\Local\Temp\claude\C--Users-nathtavares\693b4b1a-97a9-4280-bd88-e5b02a3c74b9\scratchpad\v3_velocidade.csv'
HTML_PATH = r'C:\Users\nathtavares\dash_encendidos_v3.html'

STR_FIELDS = {'anomes_encendido', 'app_instalado', 'flag_reencendido', 'status_limite', 'flag_tc', 'flag_ea'}
RENAME = {'app_instalado_encendido': 'app_instalado', 'status_limite_reenc': 'status_limite'}

rows_js = []
with open(CSV_PATH, encoding='utf-8') as f:
    reader = csv.DictReader(f)
    fieldnames = [RENAME.get(h, h) for h in reader.fieldnames]
    for row in reader:
        parts = []
        for orig_key, key in zip(reader.fieldnames, fieldnames):
            val = row[orig_key]
            if key in STR_FIELDS:
                parts.append(f'{key}: "{val}"')
            else:
                parts.append(f'{key}: {int(val) if val else 0}')
        rows_js.append('    { ' + ', '.join(parts) + ' },')

new_block = 'const DATA_VEL = [\n' + '\n'.join(rows_js) + '\n];'

html = open(HTML_PATH, encoding='utf-8').read()
start = html.index('const DATA_VEL = [')
end = html.index('];', start) + 2
old_block = html[start:end]
html = html[:start] + new_block + html[end:]
open(HTML_PATH, 'w', encoding='utf-8').write(html)

print(f'Linhas novas: {len(rows_js)}')
print(f'Bloco antigo: {len(old_block)} chars -> Bloco novo: {len(new_block)} chars')
