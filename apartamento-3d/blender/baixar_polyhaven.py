# Baixa (só leitura, API pública) os assets gratuitos CC0 do Poly Haven usados no modelo, para ./polyhaven
# uso: python3 baixar_polyhaven.py
import json, os, subprocess
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'polyhaven'); UA = 'apartamento-3d-render/1.0'
MODELOS_2K = ['modern_arm_chair_01', 'coffee_table_round_01', 'side_table_01', 'potted_plant_01', 'potted_plant_02', 'throw_pillows_01']
MODELOS_1K = ['outdoor_table_chair_set_01', 'mid_century_lounge_chair', 'modern_ceiling_lamp_01', 'hanging_picture_frame_01', 'hanging_picture_frame_02',
              'book_encyclopedia_set_01', 'ceramic_vase_01', 'ceramic_vase_02', 'ceramic_vase_03', 'ceramic_vase_04', 'lambis_shell', 'wooden_bowl_01',
              'wicker_basket_02', 'potted_plant_04', 'jug_01', 'tea_set_01']
TEXTURAS_2K = ['laminate_floor_02', 'oak_veneer_01', 'teak_veneer', 'sapele_veneer', 'rough_linen', 'poly_wool_herringbone', 'marble_01', 'painted_plaster_wall']
HDRI_4K = ['kloofendal_48d_partly_cloudy_puresky']

def get_json(url): return json.loads(subprocess.check_output(['curl', '-sSfL', '-A', UA, url]))
def fetch(url, path):
    if os.path.exists(path) and os.path.getsize(path) > 0: return
    os.makedirs(os.path.dirname(path), exist_ok=True); subprocess.check_call(['curl', '-sSfL', '-A', UA, '-o', path, url])

for res, ids in (('2k', MODELOS_2K), ('1k', MODELOS_1K)):
    for aid in ids:
        g = get_json(f'https://api.polyhaven.com/files/{aid}')['gltf']; g = (g.get(res) or g[sorted(g)[0]])['gltf']
        base = os.path.join(OUT, 'models', aid); fetch(g['url'], os.path.join(base, os.path.basename(g['url'])))
        for rel, inc in g.get('include', {}).items(): fetch(inc['url'], os.path.join(base, rel))
        print('modelo', aid)
for aid in TEXTURAS_2K:
    f = get_json(f'https://api.polyhaven.com/files/{aid}')
    for short, keys in {'diff': ['Diffuse', 'diff'], 'nor': ['nor_gl'], 'rough': ['Rough', 'rough']}.items():
        k = next((k for k in keys if k in f), None)
        if k and '2k' in f[k]: fetch(f[k]['2k']['jpg']['url'], os.path.join(OUT, 'tex', aid, f'{short}.jpg'))
    print('textura', aid)
for aid in HDRI_4K:
    fetch(get_json(f'https://api.polyhaven.com/files/{aid}')['hdri']['4k']['hdr']['url'], os.path.join(OUT, 'hdri', f'{aid}_4k.hdr')); print('hdri', aid)
