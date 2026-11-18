# Apartamento 02 — proposta de interiores modelada do zero em Blender a partir das medidas (dados.js → dados.json).
# Móveis, plantas, texturas e HDRI gratuitos (CC0) do Poly Haven; o restante é modelado aqui com as medidas do projeto.
# uso: blender -b -P apto_build.py -- <vistas: sala,cozinha-pia,cozinha-cafe,quarto[,planta]> <amostras> <largura> <altura> <pasta> [--save arquivo.blend]
# antes: python3 baixar_polyhaven.py (assets em ./polyhaven), python3 artes.py artes, node dados_para_json.js ../dados.js dados.json
import bpy, bmesh, math, json, os, sys, glob, random
from mathutils import Vector, Matrix, Euler

ARGS = sys.argv[sys.argv.index('--') + 1:]
VIEWS, SAMPLES, RW, RH, OUT = ARGS[0].split(','), int(ARGS[1]), int(ARGS[2]), int(ARGS[3]), ARGS[4]
SAVE = ARGS[ARGS.index('--save') + 1] if '--save' in ARGS else None
ROOT = os.path.dirname(os.path.abspath(__file__))
PH = os.path.join(ROOT, 'polyhaven'); D = json.load(open(os.path.join(ROOT, 'dados.json')))
H = D['PE_DIREITO']; PROP = D['PROP']; ITEMS = {i['cod']: i for i in PROP['itens']}
random.seed(7)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene; sc.unit_settings.system = 'METRIC'

def P(x, y, z=0.0): return Vector((x, -y, z))           # planta (x→, y↓) → Blender (X, −Y, Z)
def hexc(h, a=1.0):                                      # cor sRGB hex → linear
    h = h.lstrip('#'); c = [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    return tuple(((v / 12.92) if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4) for v in c) + (a,)

COLL = {}
def coll(name):
    if name not in COLL:
        c = bpy.data.collections.new(name); sc.collection.children.link(c); COLL[name] = c
    return COLL[name]

# ======================================================================== materiais
IMG = {}
def img(path, data=False):
    if path not in IMG:
        im = bpy.data.images.load(path, check_existing=True)
        if data: im.colorspace_settings.name = 'Non-Color'
        IMG[path] = im
    return IMG[path]

def new_mat(name):
    m = bpy.data.materials.new(name); m.use_nodes = True
    nt = m.node_tree; b = nt.nodes['Principled BSDF']; return m, nt, b

def setb(b, **kw):
    for k, v in kw.items():
        k = k.replace('_', ' ')
        if k in b.inputs: b.inputs[k].default_value = v

def mix_rgb(nt, a, b, fac=1.0, blend='MULTIPLY'):
    N, L = nt.nodes, nt.links; mx = N.new('ShaderNodeMix'); mx.data_type = 'RGBA'; mx.blend_type = blend
    sk = {s.identifier: s for s in mx.inputs}; sk['Factor_Float'].default_value = fac
    for key, v in (('A_Color', a), ('B_Color', b)):
        if isinstance(v, bpy.types.NodeSocket): L.new(v, sk[key])
        else: sk[key].default_value = v
    return next(o for o in mx.outputs if o.identifier == 'Result_Color')

def mat_color(name, hex_or_rgb, rough=0.5, metal=0.0, **kw):
    m, nt, b = new_mat(name)
    col = hexc(hex_or_rgb) if isinstance(hex_or_rgb, str) else hex_or_rgb
    setb(b, Base_Color=col, Roughness=rough, Metallic=metal, **kw); return m

def mat_tex(name, tex, size, tint=None, mix=1.0, rough=None, rough_mul=1.0, nor=1.0, rot=0.0, hsv=None, **kw):
    """Textura Poly Haven em UV de mundo (metros). tint multiplica a cor (mix=1) ou substitui a cor (mix=0, só relevo)."""
    m, nt, b = new_mat(name); N = nt.nodes; L = nt.links
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (1 / size, 1 / size, 1); mp.inputs['Rotation'].default_value = (0, 0, math.radians(rot))
    L.new(tc.outputs['UV'], mp.inputs['Vector'])
    d = os.path.join(PH, 'tex', tex)
    def tnode(f, data):
        t = N.new('ShaderNodeTexImage'); t.image = img(os.path.join(d, f), data); L.new(mp.outputs[0], t.inputs['Vector']); return t
    col = None
    if os.path.exists(os.path.join(d, 'diff.jpg')):
        col = tnode('diff.jpg', False).outputs['Color']
        if hsv:
            hs = N.new('ShaderNodeHueSaturation'); hs.inputs['Hue'].default_value = hsv[0]; hs.inputs['Saturation'].default_value = hsv[1]; hs.inputs['Value'].default_value = hsv[2]
            L.new(col, hs.inputs['Color']); col = hs.outputs[0]
    if tint is not None:
        if col is None or mix == 0:
            b.inputs['Base Color'].default_value = hexc(tint); col = None
            if mix == 0 and os.path.exists(os.path.join(d, 'diff.jpg')):   # variação sutil de tom vinda da textura
                gray = N.new('ShaderNodeRGBToBW'); L.new(tnode('diff.jpg', False).outputs['Color'], gray.inputs[0])
                mr = N.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.93; mr.inputs['To Max'].default_value = 1.05
                L.new(gray.outputs[0], mr.inputs['Value'])
                L.new(mix_rgb(nt, hexc(tint), mr.outputs[0]), b.inputs['Base Color'])
        else:
            col = mix_rgb(nt, col, hexc(tint), mix)
    if col is not None: L.new(col, b.inputs['Base Color'])
    if rough is not None: b.inputs['Roughness'].default_value = rough
    elif os.path.exists(os.path.join(d, 'rough.jpg')):
        r = tnode('rough.jpg', True); mm = N.new('ShaderNodeMath'); mm.operation = 'MULTIPLY'; mm.inputs[1].default_value = rough_mul
        L.new(r.outputs['Color'], mm.inputs[0]); L.new(mm.outputs[0], b.inputs['Roughness'])
    if nor > 0 and os.path.exists(os.path.join(d, 'nor.jpg')):
        nm = N.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = nor
        L.new(tnode('nor.jpg', True).outputs['Color'], nm.inputs['Color']); L.new(nm.outputs[0], b.inputs['Normal'])
    setb(b, **kw); return m

def mat_glass(name, color=(0.97, 0.985, 0.99), rough=0.0, tint_shadow=False):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; N.clear(); L = nt.links
    o = N.new('ShaderNodeOutputMaterial'); g = N.new('ShaderNodeBsdfGlass'); g.inputs['Color'].default_value = (*color, 1)
    g.inputs['Roughness'].default_value = rough; g.inputs['IOR'].default_value = 1.5
    t = N.new('ShaderNodeBsdfTransparent'); t.inputs['Color'].default_value = (*color, 1) if tint_shadow else (1, 1, 1, 1)
    lp = N.new('ShaderNodeLightPath'); mx = N.new('ShaderNodeMath'); mx.operation = 'MAXIMUM'
    L.new(lp.outputs['Is Shadow Ray'], mx.inputs[0]); L.new(lp.outputs['Is Diffuse Ray'], mx.inputs[1])
    mix = N.new('ShaderNodeMixShader'); L.new(mx.outputs[0], mix.inputs[0]); L.new(g.outputs[0], mix.inputs[1]); L.new(t.outputs[0], mix.inputs[2])
    L.new(mix.outputs[0], o.inputs['Surface']); return m

def mat_emit(name, color, strength):
    m = bpy.data.materials.new(name); m.use_nodes = True; nt = m.node_tree; N = nt.nodes; N.clear()
    o = N.new('ShaderNodeOutputMaterial'); e = N.new('ShaderNodeEmission'); e.inputs['Color'].default_value = (*color, 1); e.inputs['Strength'].default_value = strength
    nt.links.new(e.outputs[0], o.inputs['Surface']); return m

def mat_tiles(name, tw, th, base='#F3F2EE', grout='#C9C6C0', gw=0.003, rough=0.12, vary=0.03, offset=0.0):
    """Revestimento cerâmico procedural (azulejo / piso) com rejunte em relevo."""
    m, nt, b = new_mat(name); N = nt.nodes; L = nt.links
    tc = N.new('ShaderNodeTexCoord'); br = N.new('ShaderNodeTexBrick')
    br.offset = offset; br.offset_frequency = 2; br.squash = 1.0; br.squash_frequency = 2
    br.inputs['Scale'].default_value = 1.0; br.inputs['Mortar Size'].default_value = gw; br.inputs['Mortar Smooth'].default_value = 0.3
    br.inputs['Brick Width'].default_value = tw; br.inputs['Row Height'].default_value = th; br.inputs['Bias'].default_value = 0
    c1 = hexc(base); br.inputs['Color1'].default_value = c1
    br.inputs['Color2'].default_value = tuple(max(0, v * (1 - vary)) for v in c1[:3]) + (1,)
    br.inputs['Mortar'].default_value = hexc(grout)
    L.new(tc.outputs['UV'], br.inputs['Vector']); L.new(br.outputs['Color'], b.inputs['Base Color'])
    rm = N.new('ShaderNodeMapRange'); rm.inputs['To Min'].default_value = rough; rm.inputs['To Max'].default_value = 0.6
    L.new(br.outputs['Fac'], rm.inputs['Value']); L.new(rm.outputs[0], b.inputs['Roughness'])
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.35; bp.inputs['Distance'].default_value = 0.002; bp.invert = True
    L.new(br.outputs['Fac'], bp.inputs['Height']); L.new(bp.outputs[0], b.inputs['Normal'])
    setb(b, Specular_IOR_Level=0.55); return m

def mat_marble(name, base='#EDE9E2', vein='#C7C0B6', scale=1.2, rough=0.12):
    """Porcelanato marmorizado claro (procedural)."""
    m, nt, b = new_mat(name); N = nt.nodes; L = nt.links
    tc = N.new('ShaderNodeTexCoord'); ns = N.new('ShaderNodeTexNoise'); ns.inputs['Scale'].default_value = 2.2 * scale; ns.inputs['Detail'].default_value = 9; ns.inputs['Roughness'].default_value = 0.62
    L.new(tc.outputs['UV'], ns.inputs['Vector'])
    wv = N.new('ShaderNodeTexWave'); wv.inputs['Scale'].default_value = 0.9 * scale; wv.inputs['Distortion'].default_value = 6.0; wv.inputs['Detail'].default_value = 6
    wv.inputs['Detail Scale'].default_value = 1.2; wv.wave_profile = 'SIN'
    vm = N.new('ShaderNodeVectorMath'); vm.operation = 'ADD'; L.new(tc.outputs['UV'], vm.inputs[0]); L.new(ns.outputs['Color'], vm.inputs[1])
    L.new(vm.outputs[0], wv.inputs['Vector'])
    cr = N.new('ShaderNodeValToRGB'); cr.color_ramp.elements[0].position = 0.0; cr.color_ramp.elements[1].position = 0.035
    cr.color_ramp.elements[0].color = hexc(vein); cr.color_ramp.elements[1].color = hexc(base)
    L.new(wv.outputs['Fac'], cr.inputs['Fac']); L.new(cr.outputs['Color'], b.inputs['Base Color'])
    setb(b, Roughness=rough, Specular_IOR_Level=0.6, Coat_Weight=0.2, Coat_Roughness=0.05); return m

def mat_brushed(name, hexcol='#BFC2C4', rough=0.26):
    m, nt, b = new_mat(name); N = nt.nodes; L = nt.links
    setb(b, Base_Color=hexc(hexcol), Metallic=1.0, Roughness=rough, Anisotropic=0.75)
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (2.0, 260.0, 1)
    L.new(tc.outputs['UV'], mp.inputs['Vector'])
    ns = N.new('ShaderNodeTexNoise'); ns.inputs['Scale'].default_value = 4.0; ns.inputs['Detail'].default_value = 4; L.new(mp.outputs[0], ns.inputs['Vector'])
    rm = N.new('ShaderNodeMapRange'); rm.inputs['To Min'].default_value = rough - 0.07; rm.inputs['To Max'].default_value = rough + 0.07
    L.new(ns.outputs['Fac'], rm.inputs['Value']); L.new(rm.outputs[0], b.inputs['Roughness'])
    tg = N.new('ShaderNodeTangent'); tg.direction_type = 'UV_MAP'; L.new(tg.outputs[0], b.inputs['Tangent']); return m

def mat_slats(name, base_mat_hex, pitch, width, axis='x'):
    pass

# --- paleta e materiais do projeto (dados.js) ---
PAL = {p['cod']: p['hex'] for p in PROP['paleta']}
M = {}
def paint(cod, hexcol, rough=0.86):
    return mat_tex('PINTURA_' + cod, 'painted_plaster_wall', 2.0, tint=hexcol, mix=0, rough=rough, nor=0.25)
M['off'] = paint('PT01', PAL['PT-01']); M['teto'] = paint('PT02', PAL['PT-02'], 0.9)
M['salvia'] = paint('PT03', PAL['PT-03']); M['argila'] = paint('PT04', PAL['PT-04'])
M['greige'] = paint('PT05', PAL['PT-05']); M['nevoa'] = paint('PT06', PAL['PT-06'])
M['fachada'] = mat_color('FACHADA', '#E9E6E0', 0.8)
M['laminado'] = mat_tex('LM01_LAMINADO', 'laminate_floor_02', 1.70, rough_mul=0.85, nor=0.6, hsv=(0.505, 1.12, 1.18), Coat_Weight=0.12, Coat_Roughness=0.3)
M['freijo'] = mat_tex('MD01_FREIJO', 'oak_veneer_01', 1.83, rough_mul=0.9, nor=0.4, hsv=(0.5, 1.05, 1.05))
M['teca'] = mat_tex('MADEIRA_MESA', 'teak_veneer', 1.0, rough_mul=0.8, nor=0.4, hsv=(0.5, 0.95, 1.08))
M['mogno'] = mat_tex('PO01_MOGNO', 'sapele_veneer', 0.9, rough=0.36, nor=0.3, hsv=(0.5, 0.95, 0.42), Coat_Weight=0.3, Coat_Roughness=0.25)
M['linho'] = mat_tex('TX01_LINHO', 'rough_linen', 0.27, tint='#E4DCCD', mix=0, rough=0.92, nor=0.8, Sheen_Weight=0.35)
M['linho_cortina'] = mat_tex('TX01_CORTINA', 'rough_linen', 0.27, tint='#EEE8DD', mix=0, rough=0.95, nor=0.5, Sheen_Weight=0.2)
M['lencol'] = mat_tex('ROUPA_CAMA', 'rough_linen', 0.27, tint='#F2EFE9', mix=0, rough=0.95, nor=0.6, Sheen_Weight=0.3)
M['cabeceira'] = mat_tex('CABECEIRA_LINHO', 'rough_linen', 0.27, tint='#CDBFAA', mix=0, rough=0.95, nor=0.8, Sheen_Weight=0.35)
M['manta'] = mat_tex('MANTA_ARGILA', 'poly_wool_herringbone', 0.27, tint='#B9785A', mix=0, rough=0.95, nor=0.9, Sheen_Weight=0.4)
M['boucle'] = mat_tex('BOUCLE_CARAMELO', 'poly_wool_herringbone', 0.18, tint='#B88458', mix=0, rough=0.97, nor=1.0, Sheen_Weight=0.5)
M['tapete'] = mat_tex('D01_TAPETE', 'poly_wool_herringbone', 0.30, tint='#D6CAB6', mix=0, rough=0.98, nor=1.0, Sheen_Weight=0.4)
M['tapete_q'] = mat_tex('TAPETE_QUARTO', 'poly_wool_herringbone', 0.30, tint='#CBBBA5', mix=0, rough=0.98, nor=1.0, Sheen_Weight=0.4)
M['travertino'] = mat_tex('TRAVERTINO', 'marble_01', 1.5, rough=0.35, nor=0.3)
M['branco_mdf'] = mat_color('MD02_BRANCO_TX', '#F1F0EC', 0.42)
M['marmore'] = mat_marble('PC01_PORCELANATO')
M['inox'] = mat_brushed('IN01_INOX')
M['inox_escuro'] = mat_brushed('INOX_ESCURO', '#8E9194', 0.3)
M['preto'] = mat_color('MT01_PRETO_FOSCO', '#1E1E1E', 0.45)
M['preto_vidro'] = mat_color('VIDRO_PRETO', '#0B0B0C', 0.04, Specular_IOR_Level=0.7, Coat_Weight=0.6, Coat_Roughness=0.02)
M['grafite'] = mat_color('GRAFITE', '#2E2F31', 0.5)
M['aluminio'] = mat_color('ALUMINIO_BRANCO', '#ECECEA', 0.32, metal=0.0, Specular_IOR_Level=0.6)
M['vidro'] = mat_glass('VIDRO')
M['vidro_fosco'] = mat_glass('VIDRO_FOSCO', (0.96, 0.97, 0.97), 0.35)
M['vidro_guarda'] = mat_glass('VIDRO_GUARDA_CORPO', (0.70, 0.84, 0.92), 0.0, tint_shadow=True)
M['espelho'] = mat_color('ESPELHO', '#F2F4F5', 0.01, metal=1.0)
M['azulejo'] = mat_tiles('AZULEJO_BRANCO', 0.32, 0.44, '#F4F4F2', '#DAD8D3', 0.0025, 0.08, 0.02)
M['piso_ceramico'] = mat_tiles('PISO_CERAMICO', 0.45, 0.45, '#EEEDE9', '#BDB9B2', 0.004, 0.18, 0.025)
M['deck'] = mat_tiles('PISO_VARANDA', 0.60, 0.60, '#CFC8BD', '#A49C92', 0.004, 0.45, 0.04)
M['pastilha_b'] = mat_tiles('PASTILHA_BRANCA', 0.025, 0.025, '#ECECE8', '#C6C4BE', 0.06, 0.3, 0.05)
M['pastilha_a'] = mat_tiles('PASTILHA_AZUL', 0.025, 0.025, '#3D6F99', '#C9CED2', 0.06, 0.3, 0.12)
M['granito'] = mat_color('GRANITO_PEITORIL', '#2B2A28', 0.25)
M['rodape'] = mat_color('RD01_RODAPE', '#F6F5F2', 0.4)
M['soleira'] = mat_color('SOLEIRA', '#D9D4CB', 0.3)
M['ceramica'] = mat_color('CERAMICA_FOSCA', '#EDE9E2', 0.55)
M['ceramica_argila'] = mat_color('CERAMICA_ARGILA', '#C08A6A', 0.6)
M['madeira_pe'] = mat_tex('MADEIRA_PES', 'oak_veneer_01', 0.6, rough=0.5, nor=0.2, hsv=(0.5, 1.0, 0.85))
M['tv'] = mat_color('TELA_TV', '#050506', 0.05, Specular_IOR_Level=0.6, Coat_Weight=1.0, Coat_Roughness=0.01)
M['led'] = mat_emit('LED_3000K', (1.0, 0.80, 0.58), 0.0)       # acesas por vista
M['led_coz'] = mat_emit('LED_COZINHA', (1.0, 0.84, 0.66), 0.0)
M['cupula'] = mat_tex('CUPULA_LINHO', 'rough_linen', 0.2, tint='#EFE8DC', mix=0, rough=0.95, nor=0.4, Subsurface_Weight=0.0)
# palhinha / fibra natural: textura do cesto do Poly Haven
def mat_wicker(name, size=0.25, hsv=(0.5, 1.0, 1.0)):
    m, nt, b = new_mat(name); N = nt.nodes; L = nt.links; d = os.path.join(PH, 'models', 'wicker_basket_02', 'textures')
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / size, 1 / size, 1); L.new(tc.outputs['UV'], mp.inputs['Vector'])
    t = N.new('ShaderNodeTexImage'); t.image = img(glob.glob(d + '/*diff*')[0]); L.new(mp.outputs[0], t.inputs['Vector'])
    hs = N.new('ShaderNodeHueSaturation'); hs.inputs['Hue'].default_value, hs.inputs['Saturation'].default_value, hs.inputs['Value'].default_value = hsv
    L.new(t.outputs['Color'], hs.inputs['Color']); L.new(hs.outputs[0], b.inputs['Base Color'])
    n = N.new('ShaderNodeTexImage'); n.image = img(glob.glob(d + '/*nor_gl*')[0], True); L.new(mp.outputs[0], n.inputs['Vector'])
    nm = N.new('ShaderNodeNormalMap'); nm.inputs['Strength'].default_value = 1.0; L.new(n.outputs['Color'], nm.inputs['Color']); L.new(nm.outputs[0], b.inputs['Normal'])
    setb(b, Roughness=0.7); return m
def mat_cane(name, cell=0.014, straw='#D8C29C', hole='#2E241C'):
    m, nt, b = new_mat(name); N = nt.nodes; L = nt.links
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Scale'].default_value = (1 / cell, 1 / cell, 1)
    mp.inputs['Rotation'].default_value = (0, 0, math.radians(45)); L.new(tc.outputs['UV'], mp.inputs['Vector'])
    vo = N.new('ShaderNodeTexVoronoi'); vo.inputs['Randomness'].default_value = 0.0; vo.inputs['Scale'].default_value = 1.0; L.new(mp.outputs[0], vo.inputs['Vector'])
    cr = N.new('ShaderNodeValToRGB'); e0, e1 = cr.color_ramp.elements; e0.position, e1.position = 0.24, 0.31; e0.color = hexc(hole); e1.color = hexc(straw)
    L.new(vo.outputs['Distance'], cr.inputs['Fac'])
    wv = N.new('ShaderNodeTexWave'); wv.wave_type = 'BANDS'; wv.inputs['Scale'].default_value = 2.0; wv.inputs['Distortion'].default_value = 0.5; L.new(mp.outputs[0], wv.inputs['Vector'])
    mr = N.new('ShaderNodeMapRange'); mr.inputs['To Min'].default_value = 0.82; mr.inputs['To Max'].default_value = 1.05; L.new(wv.outputs['Fac'], mr.inputs['Value'])
    L.new(mix_rgb(nt, cr.outputs['Color'], mr.outputs[0]), b.inputs['Base Color'])
    bp = N.new('ShaderNodeBump'); bp.inputs['Strength'].default_value = 0.6; bp.inputs['Distance'].default_value = 0.002
    L.new(vo.outputs['Distance'], bp.inputs['Height']); L.new(bp.outputs[0], b.inputs['Normal'])
    setb(b, Roughness=0.6, Sheen_Weight=0.2); return m
M['palhinha'] = mat_cane('PALHINHA')
M['fibra'] = mat_wicker('FIBRA_NATURAL', 0.22, (0.5, 0.9, 1.35))

# ======================================================================== geometria
def uv_box(bm, rot=0.0):
    """UV em metros por projeção de caixa (piso → xy, paredes → (horizontal, z))."""
    uv = bm.loops.layers.uv.verify(); c, s = math.cos(rot), math.sin(rot)
    for f in bm.faces:
        n = f.normal; ax = max(range(3), key=lambda i: abs(n[i]))
        for l in f.loops:
            p = l.vert.co
            if ax == 2: u, v = p.x, p.y
            elif ax == 0: u, v = p.y, p.z
            else: u, v = p.x, p.z
            l[uv].uv = (u * c - v * s, u * s + v * c)

def mesh_obj(name, bm, mats, collection='geral', smooth=False, uv=True, uvrot=0.0):
    if uv: uv_box(bm, uvrot)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    for m in (mats if isinstance(mats, (list, tuple)) else [mats]): me.materials.append(m)
    if smooth: me.shade_smooth()
    ob = bpy.data.objects.new(name, me); coll(collection).objects.link(ob); return ob

def bm_box(bm, x0, x1, y0, y1, z0, z1, mi=0):
    """caixa em coordenadas da planta (x0<x1, y0<y1)."""
    vs = [bm.verts.new(P(x, y, z)) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    idx = [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4), (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)]
    fs = [bm.faces.new([vs[i] for i in q]) for q in idx]
    for f in fs: f.material_index = mi
    return fs

def box(name, x0, x1, y0, y1, z0, z1, mat, collection='geral', bevel=0.0, seg=2, smooth=False, uvrot=0.0):
    bm = bmesh.new(); bm_box(bm, min(x0, x1), max(x0, x1), min(y0, y1), max(y0, y1), min(z0, z1), max(z0, z1))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = mesh_obj(name, bm, mat, collection, uvrot=uvrot)
    if bevel > 0:
        md = ob.modifiers.new('bevel', 'BEVEL'); md.width = bevel; md.segments = seg; md.limit_method = 'ANGLE'
        md.harden_normals = smooth
        if smooth: ob.data.shade_smooth()
    return ob

def prism(name, pts, z0, z1, mat, collection='geral', uvrot=0.0):
    """prisma vertical a partir de um polígono da planta."""
    bm = bmesh.new(); vb = [bm.verts.new(P(x, y, z0)) for x, y in pts]
    f = bm.faces.new(vb); ext = bmesh.ops.extrude_face_region(bm, geom=[f], use_keep_orig=True)
    for v in [e for e in ext['geom'] if isinstance(e, bmesh.types.BMVert)]: v.co.z = z1
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return mesh_obj(name, bm, mat, collection, uvrot=uvrot)

def cyl(name, cx, cy, z0, z1, r0, r1=None, mat=None, seg=48, collection='geral', smooth=True, bevel=0.0):
    bm = bmesh.new(); r1 = r0 if r1 is None else r1
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=seg, radius1=r0, radius2=r1, depth=z1 - z0,
                          matrix=Matrix.Translation(P(cx, cy, (z0 + z1) / 2)))
    ob = mesh_obj(name, bm, mat, collection)
    if smooth:
        ob.data.shade_smooth(); md = ob.modifiers.new('smooth', 'NODES') if False else None
        ob.modifiers.new('ang', 'BEVEL').width = bevel if bevel else 0.0015
        ob.modifiers['ang'].segments = 2; ob.modifiers['ang'].limit_method = 'ANGLE'; ob.modifiers['ang'].harden_normals = True
    return ob

def rot_obj(ob, pivot, ang):
    """gira um objeto (já em coordenadas de mundo) em torno de um eixo vertical em pivot (planta), ang em graus (anti-horário na planta)."""
    pv = P(*pivot, 0); T = Matrix.Translation(pv) @ Matrix.Rotation(math.radians(-ang), 4, 'Z') @ Matrix.Translation(-pv)
    ob.matrix_world = T @ ob.matrix_world; return ob

def in_poly(x, y, poly):
    inside = False; n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1 + 1e-12) + x1: inside = not inside
    return inside

def room_at(x, y):
    for r in D['ROOMS']:
        for poly in r['floor']:
            if in_poly(x, y, poly): return r['id']
    if in_poly(x, y, D['HALL']): return 'hall'
    return None

# ======================================================================== paredes (uma malha única, unida por booleana)
def wall_boxes(w):
    x0, x1, y0, y1 = w['r']; alongX = (x1 - x0) >= (y1 - y0)
    lo, hi = (x0, x1) if alongX else (y0, y1)
    pcs, cur = [], lo
    for o in sorted(w.get('ops', []), key=lambda o: o['a']):
        a, b, t = o['a'], o['b'], o['t']
        if a > cur + 1e-6: pcs.append((cur, a, 0, H))
        if t in ('door', 'main'): top = 2.10
        elif t == 'open': top = o.get('head', 2.10)
        elif t == 'win': top = o['head']; pcs.append((a, b, 0, o['sill']))
        else: top = o.get('top', 2.50)
        if top < H: pcs.append((a, b, top, H))
        cur = b
    if cur < hi - 1e-6: pcs.append((cur, hi, 0, H))
    return [((a, b, y0, y1) if alongX else (x0, x1, a, b)) + (z0, z1) for a, b, z0, z1 in pcs]

def build_walls():
    bm = bmesh.new()
    for w in D['WALLS']:
        for x0, x1, y0, y1, z0, z1 in wall_boxes(w): bm_box(bm, x0, x1, y0, y1, z0, z1 if z1 < H else H + 0.004)
    # parede curva do quarto 1 (canto arredondado junto à varanda)
    q = D['Q1']; n = 18; ring = []
    for i in range(n + 1):
        t = math.pi + (math.pi / 2) * i / n
        ring.append(((q['cx'] + q['r'] * math.cos(t), q['cy'] + q['r'] * math.sin(t)), (q['cx'] + (q['r'] + 0.15) * math.cos(t), q['cy'] + (q['r'] + 0.15) * math.sin(t))))
    for i in range(n):
        (a_in, a_out), (b_in, b_out) = ring[i], ring[i + 1]
        quad = [a_in, b_in, b_out, a_out]
        vb = [bm.verts.new(P(x, y, 0)) for x, y in quad]; vt = [bm.verts.new(P(x, y, H + 0.004)) for x, y in quad]
        bm.faces.new(vb[::-1]); bm.faces.new(vt)
        for k in range(4): bm.faces.new([vb[k], vb[(k + 1) % 4], vt[(k + 1) % 4], vt[k]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    ob = mesh_obj('PAREDES', bm, [M['off']], 'arquitetura', uv=False)
    bpy.context.view_layer.objects.active = ob; ob.select_set(True)
    bpy.ops.object.mode_set(mode='EDIT'); bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.intersect_boolean(operation='UNION', use_self=True, solver='EXACT')
    bpy.ops.mesh.select_all(action='SELECT'); bpy.ops.mesh.dissolve_limited(angle_limit=math.radians(0.5))
    bpy.ops.object.mode_set(mode='OBJECT')
    # materiais por face, conforme o cômodo do lado da face
    mats = ['off', 'salvia', 'greige', 'nevoa', 'azulejo', 'pastilha_b', 'pastilha_a', 'fachada', 'teto']
    me = ob.data; me.materials.clear()
    for k in mats: me.materials.append(M[k])
    faces = {f['cod']: f for f in PROP['faces']}
    tiled = {'cozinha', 'area', 'wcsocial', 'wcsuite', 'wcserv'}
    for p in me.polygons:
        c, n = p.center, p.normal
        if abs(n.z) > 0.5: p.material_index = mats.index('off'); continue
        sx, sy = c.x + n.x * 0.04, -(c.y + n.y * 0.04); r = room_at(sx, sy)
        k = 'fachada' if r is None else ('azulejo' if r in tiled else 'off')
        if r == 'varanda': k = 'pastilha_a' if abs(-c.y) < 0.01 and n.y < 0 else 'pastilha_b'
        if r in ('sala', 'suite', 'quarto2', 'circ', 'quarto1', 'qemp', 'hall'):
            pn = (n.x, -n.y)          # normal na planta
            for cod, key in (('PT-05', 'greige'), ('PT-06', 'nevoa')):
                f = faces[cod]
                if f['ax'] == 'x' and abs(-c.y - f['c']) < 0.01 and f['a'] - 0.01 <= c.x <= f['b'] + 0.01 and pn[1] * f['n'] > 0.5: k = key
                if f['ax'] == 'y' and abs(c.x - f['c']) < 0.01 and f['a'] - 0.01 <= -c.y <= f['b'] + 0.01 and pn[0] * f['n'] > 0.5: k = key
        p.material_index = mats.index(k)
    bm = bmesh.new(); bm.from_mesh(me); uv_box(bm); bm.to_mesh(me); bm.free()
    return ob

# ======================================================================== portas, janelas e portas de correr
def opening_frame(w, o):
    x0, x1, y0, y1 = w['r']; alongX = (x1 - x0) >= (y1 - y0)
    return alongX, x0, x1, y0, y1

def place(alongX, u0, u1, d0, d1, z0, z1):
    """caixa local da abertura → coordenadas da planta (u ao longo da parede, d na espessura)."""
    return (u0, u1, d0, d1, z0, z1) if alongX else (d0, d1, u0, u1, z0, z1)

DOOR_OPEN = {}
def build_door(w, o, gi):
    alongX, x0, x1, y0, y1 = opening_frame(w, o); a, b = o['a'], o['b']
    d0, d1 = (y0, y1) if alongX else (x0, x1); th = d1 - d0; dc = (d0 + d1) / 2
    cn = f'porta_{gi}'; hd = 2.10
    # batentes e alizares
    for u0, u1 in ((a, a + 0.03), (b - 0.03, b)): box(cn + '_bat', *place(alongX, u0, u1, d0 - 0.008, d1 + 0.008, 0, hd), M['imbuia'], 'portas')
    box(cn + '_bat', *place(alongX, a, b, d0 - 0.008, d1 + 0.008, hd - 0.03, hd), M['imbuia'], 'portas')
    for dd in (d0 - 0.018, d1 + 0.003):
        for u0, u1 in ((a - 0.06, a), (b, b + 0.06)): box(cn + '_ali', *place(alongX, u0, u1, dd, dd + 0.015, 0, hd + 0.06), M['imbuia'], 'portas', bevel=0.004)
        box(cn + '_ali', *place(alongX, a - 0.06, b + 0.06, dd, dd + 0.015, hd, hd + 0.06), M['imbuia'], 'portas', bevel=0.004)
    # folha
    key = (round(a, 2), ('y' if alongX else 'x') + f'{(y0 if alongX else x0):.2f}')
    ang = DOOR_OPEN.get(key, 0)
    hinge_start = o.get('hinge', 'start') == 'start'; swing = o.get('swing', 1)
    lw = b - a - 0.065; u0 = a + 0.032; t = 0.036
    leaf = box(cn + '_folha', *place(alongX, u0, u0 + lw, dc - t / 2, dc + t / 2, 0.012, hd - 0.035), M['mogno'], 'portas', bevel=0.003)
    hu = (a + 0.03) if hinge_start else (b - 0.03)
    latch = (u0 + lw - 0.065) if hinge_start else (u0 + 0.065)
    for side in (-1, 1):   # maçanetas (roseta + haste + alavanca) dos dois lados
        f0 = dc + side * t / 2; f1 = f0 + side * 0.009; f2 = f0 + side * 0.05
        dir_ = -1 if hinge_start else 1
        parts = [box(cn + '_ros', *place(alongX, latch - 0.025, latch + 0.025, min(f0, f1), max(f0, f1), 0.99, 1.04), M['inox'], 'portas', bevel=0.003),
                 box(cn + '_haste', *place(alongX, latch - 0.009, latch + 0.009, min(f0, f2), max(f0, f2), 1.006, 1.024), M['inox'], 'portas', bevel=0.003),
                 box(cn + '_alav', *place(alongX, min(latch, latch + dir_ * 0.13), max(latch, latch + dir_ * 0.13), min(f2 - side * 0.016, f2), max(f2 - side * 0.016, f2), 1.004, 1.026), M['inox'], 'portas', bevel=0.005)]
        for ob in parts: ob.parent = leaf
    if ang:
        pv = (hu, dc + swing * t / 2) if alongX else (dc + swing * t / 2, hu)
        # sentido: abre para o lado "swing" (+d)
        s = 1 if hinge_start else -1
        rot = ang * s * swing * (1 if alongX else -1)
        rot_obj(leaf, pv, rot)
    # soleira
    box(cn + '_sol', *place(alongX, a, b, d0, d1, 0, 0.012), M['soleira'], 'portas')

def build_window(w, o, gi):
    alongX, x0, x1, y0, y1 = opening_frame(w, o); a, b = o['a'], o['b']
    d0, d1 = (y0, y1) if alongX else (x0, x1); dc = (d0 + d1) / 2; cn = f'janela_{gi}'
    z0, z1 = o['sill'], o['head']; f = 0.045; dep = 0.06
    glass = M['vidro_fosco'] if o.get('frost') else M['vidro']
    # contramarco e marco
    for u0, u1 in ((a, a + f), (b - f, b)): box(cn + '_m', *place(alongX, u0, u1, dc - dep / 2, dc + dep / 2, z0, z1), M['aluminio'], 'janelas', bevel=0.002)
    for zz0, zz1 in ((z0, z0 + f), (z1 - f, z1)): box(cn + '_m', *place(alongX, a, b, dc - dep / 2, dc + dep / 2, zz0, zz1), M['aluminio'], 'janelas', bevel=0.002)
    zm = o.get('mid', None)
    if zm and zm < z1 - 0.1:
        box(cn + '_t', *place(alongX, a, b, dc - dep / 2, dc + dep / 2, zm - 0.02, zm + 0.02), M['aluminio'], 'janelas', bevel=0.002)
        box(cn + '_vs', *place(alongX, a + f, b - f, dc - 0.003, dc + 0.003, zm + 0.02, z1 - f), glass, 'janelas')
        top = zm - 0.02
    else: top = z1 - f
    n = o.get('panels', 2); wpan = (b - a - 2 * f) / n
    for i in range(n):
        u0 = a + f + i * wpan - (0.02 if i else 0); u1 = a + f + (i + 1) * wpan + (0.02 if i < n - 1 else 0)
        off = (-0.012 if i % 2 else 0.012)
        box(cn + '_fol', *place(alongX, u0, u0 + 0.035, dc + off - 0.013, dc + off + 0.013, z0 + f, top), M['aluminio'], 'janelas', bevel=0.002)
        box(cn + '_fol', *place(alongX, u1 - 0.035, u1, dc + off - 0.013, dc + off + 0.013, z0 + f, top), M['aluminio'], 'janelas', bevel=0.002)
        box(cn + '_vd', *place(alongX, u0 + 0.035, u1 - 0.035, dc + off - 0.003, dc + off + 0.003, z0 + f + 0.03, top - 0.03), glass, 'janelas')
        for zz in (z0 + f, top - 0.03): box(cn + '_fol', *place(alongX, u0 + 0.035, u1 - 0.035, dc + off - 0.013, dc + off + 0.013, zz, zz + 0.03), M['aluminio'], 'janelas', bevel=0.002)
    # peitoril de granito nos dois lados
    box(cn + '_peit', *place(alongX, a - 0.02, b + 0.02, d0 - 0.025, d1 + 0.025, z0 - 0.02, z0), M['granito'], 'janelas', bevel=0.003)

def build_pj(w, o, gi):
    alongX, x0, x1, y0, y1 = opening_frame(w, o); a, b = o['a'], o['b']
    d0, d1 = (y0, y1) if alongX else (x0, x1); dc = (d0 + d1) / 2; cn = f'pj_{gi}'
    top, tr = o.get('top', 2.50), o.get('transom', 2.18); f = 0.05; dep = 0.09
    for u0, u1 in ((a, a + f), (b - f, b)): box(cn + '_m', *place(alongX, u0, u1, dc - dep / 2, dc + dep / 2, 0, top), M['aluminio'], 'janelas', bevel=0.002)
    box(cn + '_m', *place(alongX, a, b, dc - dep / 2, dc + dep / 2, top - f, top), M['aluminio'], 'janelas', bevel=0.002)
    box(cn + '_tr', *place(alongX, a, b, dc - dep / 2, dc + dep / 2, tr - 0.025, tr + 0.025), M['aluminio'], 'janelas', bevel=0.002)
    box(cn + '_trv', *place(alongX, a + f, b - f, dc - 0.003, dc + 0.003, tr + 0.025, top - f), M['vidro'], 'janelas')
    box(cn + '_tri', *place(alongX, a, b, dc - dep / 2, dc + dep / 2, 0, 0.012), M['aluminio'], 'janelas')
    n = o.get('panels', 2); wpan = (b - a - 2 * f) / n; openfrac = o.get('open', 0); at_end = o.get('openAt', 'end') == 'end'
    for i in range(n):
        u0 = a + f + i * wpan - (0.025 if i else 0); u1 = a + f + (i + 1) * wpan + (0.025 if i < n - 1 else 0)
        off = (-0.02 if i % 2 else 0.02)
        k = (n - 1) if at_end else 0
        if openfrac and i == k:   # folha aberta: desliza sobre a vizinha
            sh = -(u1 - u0) * 0.92 if at_end else (u1 - u0) * 0.92; u0 += sh; u1 += sh
        z0, z1 = 0.015, tr - 0.025
        for uu in ((u0, u0 + 0.045), (u1 - 0.045, u1)): box(cn + '_fol', *place(alongX, *uu, dc + off - 0.016, dc + off + 0.016, z0, z1), M['aluminio'], 'janelas', bevel=0.002)
        for zz in ((z0, z0 + 0.07), (z1 - 0.045, z1)): box(cn + '_fol', *place(alongX, u0 + 0.045, u1 - 0.045, dc + off - 0.016, dc + off + 0.016, *zz), M['aluminio'], 'janelas', bevel=0.002)
        box(cn + '_vd', *place(alongX, u0 + 0.045, u1 - 0.045, dc + off - 0.004, dc + off + 0.004, z0 + 0.07, z1 - 0.045), M['vidro'], 'janelas')

def build_openings():
    gi = 0
    for w in D['WALLS']:
        for o in w.get('ops', []):
            gi += 1
            if o['t'] in ('door', 'main'): build_door(w, o, gi)
            elif o['t'] == 'win': build_window(w, o, gi)
            elif o['t'] == 'pj': build_pj(w, o, gi)

# ======================================================================== pisos, tetos, rodapés, varanda
LAM = set(PROP['laminado']['rooms'])
def build_floors():
    prism('LAJE_PISO', D['OUTLINE'], -0.25, -0.002, M['fachada'], 'arquitetura')
    prism('LAJE_TETO', D['OUTLINE'], H, H + 0.20, M['teto'], 'arquitetura')
    prism('HALL_PISO', D['HALL'], -0.002, 0.004, M['piso_ceramico'], 'arquitetura')
    for r in D['ROOMS']:
        k = 'laminado' if r['id'] in LAM else ('deck' if r['id'] == 'varanda' else 'piso_ceramico')
        for i, poly in enumerate(r['floor']):
            prism(f'PISO_{r["id"]}_{i}', poly, -0.002, 0.012 if k == 'laminado' else 0.006, M[k], 'arquitetura')
    # sanca de gesso na sala, junto à porta-janela (trilho da cortina e fita LED)
    box('SANCA', 2.16, 2.62, 0.0, 2.97, 2.38, H + 0.002, M['teto'], 'arquitetura')
    box('SANCA_LED', 2.61, 2.625, 0.02, 2.95, 2.385, 2.40, M['led'], 'luz')

def build_baseboards(walls):
    """rodapé de madeira existente (mogno escuro / imbuia avermelhada, 7 cm) nas faces de parede dos cômodos com laminado."""
    me = walls.data; bm = bmesh.new()
    for p in me.polygons:
        n = p.normal
        if abs(n.z) > 0.1: continue
        c = p.center; r = room_at(c.x + n.x * 0.04, -(c.y + n.y * 0.04))
        if r not in LAM: continue
        vs = [me.vertices[i].co for i in p.vertices]
        bot = [v for v in vs if abs(v.z) < 1e-3]
        if len(bot) < 2: continue
        a = min(bot, key=lambda v: (v.x, v.y)); b = max(bot, key=lambda v: (v.x, v.y))
        if (b - a).length < 0.05: continue
        t = Vector((n.x, n.y, 0)).normalized() * 0.015; h = 0.07
        q = [a, b, b + t, a + t]
        vb = [bm.verts.new((v.x, v.y, 0.012)) for v in q]; vt = [bm.verts.new((v.x, v.y, 0.012 + h)) for v in q]
        bm.faces.new(vt); bm.faces.new([vb[1], vb[2], vt[2], vt[1]]); bm.faces.new([vb[2], vb[3], vt[3], vt[2]]); bm.faces.new([vb[0], vb[3], vt[3], vt[0]][::-1])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    mesh_obj('RODAPES', bm, M['rodape'], 'arquitetura')

def build_arch():
    a = PROP['arco']; cx, w, h = a['cx'], a['w'], a['h']; r = w / 2; zc = h - r
    pts = [(cx - r, 0.10), (cx + r, 0.10)] + [(cx + r * math.cos(t), zc + r * math.sin(t)) for t in [math.pi * i / 40 for i in range(41)]]
    bm = bmesh.new(); vs = [bm.verts.new((x, -0.0015, z)) for x, z in pts]; bm.faces.new(vs)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:
        if f.normal.y > 0: f.normal_flip()
    mesh_obj('ARCO_PT04', bm, M['argila'], 'arquitetura')

def build_rail():
    pts = D['rail']; bm = bmesh.new(); hz = 1.05
    for i in range(len(pts) - 1):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        q = [bm.verts.new(P(xa, ya, 0.08)), bm.verts.new(P(xb, yb, 0.08)), bm.verts.new(P(xb, yb, hz)), bm.verts.new(P(xa, ya, hz))]
        bm.faces.new(q)
    ob = mesh_obj('GUARDA_CORPO_VIDRO', bm, M['vidro_guarda'], 'arquitetura')
    sol = ob.modifiers.new('esp', 'SOLIDIFY'); sol.thickness = 0.010
    cu = bpy.data.curves.new('corrimao', 'CURVE'); cu.dimensions = '3D'; sp = cu.splines.new('POLY'); sp.points.add(len(pts) - 1)
    for i, (x, y) in enumerate(pts): sp.points[i].co = (*P(x, y, hz + 0.02), 1)
    cu.bevel_depth = 0.025; cu.bevel_resolution = 4
    ob = bpy.data.objects.new('CORRIMAO', cu); coll('arquitetura').objects.link(ob); cu.materials.append(M['aluminio'])
    # borda da laje da varanda
    bm = bmesh.new()
    for i in range(len(pts) - 1):
        (xa, ya), (xb, yb) = pts[i], pts[i + 1]
        q = [bm.verts.new(P(xa, ya, 0.0)), bm.verts.new(P(xb, yb, 0.0)), bm.verts.new(P(xb, yb, 0.08)), bm.verts.new(P(xa, ya, 0.08))]
        bm.faces.new(q)
    ob = mesh_obj('MURETA', bm, M['fachada'], 'arquitetura'); ob.modifiers.new('esp', 'SOLIDIFY').thickness = 0.06

# ======================================================================== Poly Haven
PHC = {}
def ph_source(aid, key=None):
    key = key or aid
    if key in PHC: return PHC[key]
    d = os.path.join(PH, 'models', aid)
    fs = sorted(glob.glob(d + '/*_2k.gltf')) or sorted(glob.glob(d + '/*.gltf'))
    before = set(bpy.data.objects); bpy.ops.import_scene.gltf(filepath=fs[0])
    new = [o for o in bpy.data.objects if o not in before]
    c = bpy.data.collections.new('PH_' + key)
    for o in new:
        for uc in list(o.users_collection): uc.objects.unlink(o)
        c.objects.link(o)
    bpy.context.view_layer.update()
    pts = [o.matrix_world @ Vector(v) for o in new if o.type == 'MESH' for v in o.bound_box]
    mn = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts))); mx = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    c.instance_offset = ((mn.x + mx.x) / 2, (mn.y + mx.y) / 2, mn.z)
    for o in new:
        for slot in getattr(o, 'material_slots', []):
            if slot.material and 'frame' in slot.material.name and 'glass' in slot.material.name: slot.material = M['vidro']
    PHC[key] = (c, mn, mx, new); return PHC[key]

def ph(aid, x, y, z=0.0, rot=0.0, size=None, scale=None, key=None, name=None, collection='moveis'):
    """instancia um modelo do Poly Haven com a base centrada em (x, y, z) da planta; rot em graus (frente do modelo = −Y Blender = +y da planta)."""
    c, mn, mx, _ = ph_source(aid, key)
    s = scale or 1.0
    if size: s = size / max(mx.x - mn.x, mx.y - mn.y) if isinstance(size, (int, float)) else s
    e = bpy.data.objects.new(name or aid, None); e.instance_type = 'COLLECTION'; e.instance_collection = c
    e.location = P(x, y, z); e.rotation_euler = (0, 0, math.radians(rot)); e.scale = (s, s, s) if not isinstance(scale, tuple) else scale
    coll(collection).objects.link(e); return e

def ph_art(aid, key, art):
    """moldura do Poly Haven com arte própria (imagem gerada em tools/art.py)."""
    src = ph_source(aid, key)
    for o in src[3]:
        for slot in o.material_slots:
            if slot.material and 'artwork' in slot.material.name and not slot.material.name.startswith(key):
                m = slot.material.copy(); m.name = key + '_arte'
                for n in m.node_tree.nodes:
                    if n.type == 'TEX_IMAGE' and n.image and 'diff' in n.image.name.lower(): n.image = img(os.path.join(ROOT, 'artes', art))
                slot.material = m
    return key

def ph_dims(aid, key=None):
    c, mn, mx, _ = ph_source(aid, key); return mx - mn

# ======================================================================== sala e jantar
def soft_box(name, x0, x1, y0, y1, z0, z1, mat, r=0.03, collection='moveis'):
    ob = box(name, x0, x1, y0, y1, z0, z1, mat, collection, bevel=r, seg=4, smooth=True)
    return ob

# ---------------------------------------------------------------- sala v2 (ajuste de 18/11)
# Pedido: sofá retrátil grande, sem mesa de centro; nada no caminho da entrada (sem aparador, espelho redondo
# ou pintura em arco); mesa de 6 lugares redonda ou retangular; rodapés e batentes em mogno escuro/imbuia;
# opção A com paredes neutras (PT-01) e opção B com a parede da TV em verde-oliva.
OPCAO = ARGS[ARGS.index('--opcao') + 1] if '--opcao' in ARGS else 'A-redonda'
PAREDE, MESA = OPCAO.split('-')
VERDE_OLIVA = '#767B65'
M['verde_oliva'] = paint('PT07', VERDE_OLIVA)
M['sofa'] = mat_tex('SOFA_LINHO', 'rough_linen', 0.27, tint='#C9BCA7', mix=0, rough=0.93, nor=0.9, Sheen_Weight=0.4)
M['almof_terracota'] = mat_tex('ALMOFADA_TERRACOTA', 'rough_linen', 0.22, tint='#8E4429', mix=0, rough=0.95, nor=0.9, Sheen_Weight=0.4)
M['almof_oliva'] = mat_tex('ALMOFADA_OLIVA', 'ribbed_corduroy', 0.27, tint='#5E6545', mix=0, rough=0.9, nor=0.8, Sheen_Weight=0.5)
M['almof_creme'] = mat_tex('ALMOFADA_BOUCLE', 'curly_teddy_natural', 0.33, tint='#EDE4D3', mix=0, rough=0.97, nor=1.0, Sheen_Weight=0.5)
M['manta_trico'] = mat_tex('MANTA_TRICO', 'knitted_fleece', 0.70, tint='#87402A', mix=0, rough=0.95, nor=1.0, Sheen_Weight=0.4)
M['juta'] = mat_tex('TAPETE_JUTA', 'hessian_230', 0.80, tint='#B39167', mix=0, rough=0.97, nor=1.0)
M['boucle_cad'] = mat_tex('CADEIRA_BOUCLE', 'curly_teddy_natural', 0.33, tint='#EAE1D0', mix=0, rough=0.97, nor=1.0, Sheen_Weight=0.5)
M['pendente_oliva'] = mat_color('PENDENTE_OLIVA', '#5F664B', 0.45, metal=0.3)
M['branco_fosco'] = mat_color('BRANCO_FOSCO', '#F2F0EA', 0.6)
M['lampada'] = mat_emit('LAMPADA_2700K', (1.0, 0.72, 0.45), 0.0)
M['rodape'] = mat_tex('RODAPE_IMBUIA', 'sapele_veneer', 0.9, rough=0.4, nor=0.2, hsv=(0.5, 0.9, 0.30), Coat_Weight=0.25, Coat_Roughness=0.3)
M['imbuia'] = M['rodape']

def translucent(mat, amount, transparent=0.0):
    """mistura translucidez (e transparência) a um material Principled: cúpulas e voal."""
    nt = mat.node_tree; N, L = nt.nodes, nt.links; b = nt.nodes['Principled BSDF']; o = nt.nodes['Material Output']
    tr = N.new('ShaderNodeBsdfTranslucent'); src = b.inputs['Base Color']
    if src.is_linked: L.new(src.links[0].from_socket, tr.inputs['Color'])
    else: tr.inputs['Color'].default_value = src.default_value
    m1 = N.new('ShaderNodeMixShader'); m1.inputs[0].default_value = amount; L.new(b.outputs[0], m1.inputs[1]); L.new(tr.outputs[0], m1.inputs[2]); out = m1.outputs[0]
    if transparent:
        tp = N.new('ShaderNodeBsdfTransparent'); m2 = N.new('ShaderNodeMixShader'); m2.inputs[0].default_value = transparent
        L.new(out, m2.inputs[1]); L.new(tp.outputs[0], m2.inputs[2]); out = m2.outputs[0]
    L.new(out, o.inputs['Surface']); return mat
M['voal'] = translucent(mat_tex('VOAL_LINHO', 'rough_linen', 0.20, tint='#F3EFE7', mix=0, rough=0.95, nor=0.4), 0.45, 0.42)
translucent(M['cupula'], 0.5)

LIGHTS_ON = []
def point_light(name, x, y, z, watts, color=(1.0, 0.70, 0.45), size=0.03):
    ld = bpy.data.lights.new(name, 'POINT'); ld.energy = watts; ld.color = color; ld.shadow_soft_size = size
    ob = bpy.data.objects.new(name, ld); coll('luz').objects.link(ob); ob.location = P(x, y, z); LIGHTS_ON.append((ld, watts)); return ob

def tilt_x(ob, pivot, deg):
    pv = P(*pivot); ob.matrix_world = Matrix.Translation(pv) @ Matrix.Rotation(math.radians(deg), 4, 'X') @ Matrix.Translation(-pv) @ ob.matrix_world

def pillow(name, cx, cy, z, w, h, t, mat, yaw=0.0, tilt=14.0):
    """almofada: esfera achatada puxada para um cubo (modificador Cast)."""
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=20, radius=0.5)
    for v in bm.verts: v.co = Vector((v.co.x * w, v.co.y * t, v.co.z * h))
    ob = mesh_obj(name, bm, mat, 'moveis'); ob.data.shade_smooth()
    cs = ob.modifiers.new('cast', 'CAST'); cs.cast_type = 'CUBOID'; cs.factor = 0.62
    ob.matrix_world = Matrix.Translation(P(cx, cy, z)) @ Matrix.Rotation(math.radians(yaw), 4, 'Z') @ Matrix.Rotation(math.radians(tilt), 4, 'X')
    return ob

def build_sofa_retratil(x0, x1, yb, depth):
    """sofá retrátil e reclinável de 3 módulos (fechado), encostado na parede yb, frente para −y."""
    yf = yb - depth; arm = 0.18; mat = M['sofa']
    box('SOFA_RODAPE', x0 + 0.06, x1 - 0.06, yf + 0.10, yb - 0.06, 0.0, 0.06, M['grafite'], 'moveis')
    soft_box('SOFA_BASE', x0 + arm - 0.01, x1 - arm + 0.01, yf + 0.02, yb - 0.02, 0.06, 0.36, mat, 0.03)
    for xa, xb in ((x0, x0 + arm), (x1 - arm, x1)): soft_box('SOFA_BRACO', xa, xb, yf, yb, 0.04, 0.62, mat, 0.07)
    soft_box('SOFA_CAIXA_ENCOSTO', x0 + arm, x1 - arm, yb - 0.24, yb, 0.34, 0.66, mat, 0.04)
    n = 3; w = (x1 - x0 - 2 * arm) / n
    for i in range(n):
        a = x0 + arm + i * w; c = a + w / 2
        soft_box('SOFA_ASSENTO', a + 0.004, a + w - 0.004, yf + 0.012, yb - 0.30, 0.35, 0.50, mat, 0.065)
        ob = soft_box('SOFA_ENCOSTO', a + 0.008, a + w - 0.008, yb - 0.44, yb - 0.22, 0.47, 0.83, mat, 0.085); tilt_x(ob, (c, yb - 0.33, 0.50), 9)
        ob = soft_box('SOFA_CABECAL', a + 0.008, a + w - 0.008, yb - 0.42, yb - 0.22, 0.80, 1.00, mat, 0.075); tilt_x(ob, (c, yb - 0.32, 0.80), 5)
    return yf

def throw_blanket(name, x0, x1, yb, yf, zs, zb, mat):
    """manta de tricô sobre o assento, dobrando na quina e caindo pela frente."""
    prof = [(yb - (yb - yf) * t, zs + 0.012) for t in [i / 14 for i in range(15)]]
    r = 0.05
    for i in range(1, 9):
        a = math.pi / 2 * i / 8; prof.append((yf - r * math.sin(a) + 0.0, zs + 0.012 - r + r * math.cos(a)))
    for i in range(1, 13): prof.append((yf - r - 0.004 * i, zs - r - (zs - r - zb) * i / 12))
    nx = 28; bm = bmesh.new(); grid = []
    for j, (yy, zz) in enumerate(prof):
        row = []; hang = max(0.0, (zs - zz) / max(zs - zb, 1e-3))
        for i in range(nx + 1):
            t = i / nx; x = x0 + (x1 - x0) * t
            dy = -hang * 0.035 * math.sin(t * math.pi * 5 + 0.7) - hang * 0.02 * math.sin(t * math.pi * 11)
            row.append(bm.verts.new(P(x, yy + dy, zz + 0.006 * math.sin(t * math.pi * 3) * (1 - hang))))
        grid.append(row)
    for j in range(len(grid) - 1):
        for i in range(nx): bm.faces.new([grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]])
    ob = mesh_obj(name, bm, mat, 'moveis'); ob.data.shade_smooth()
    ob.modifiers.new('esp', 'SOLIDIFY').thickness = 0.014; sub = ob.modifiers.new('sub', 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    return ob

def build_curtains(x, panels, z0, z1, depth=0.09, pleat=0.11):
    for k, (ya, yb_) in enumerate(panels):
        n = max(8, int((yb_ - ya) / (pleat / 4))); bm = bmesh.new(); rows = []
        for i in range(n + 1):
            t = i / n; y = ya + (yb_ - ya) * t; xx = x + depth / 2 * math.sin((y - ya) / pleat * 2 * math.pi)
            rows.append((bm.verts.new(P(xx, y, z0)), bm.verts.new(P(xx, y, z1))))
        for i in range(n): bm.faces.new([rows[i][0], rows[i + 1][0], rows[i + 1][1], rows[i][1]])
        ob = mesh_obj(f'CORTINA_VOAL_{k}', bm, M['voal'], 'moveis', uvrot=math.pi / 2); ob.data.shade_smooth()
        ob.modifiers.new('esp', 'SOLIDIFY').thickness = 0.003
        sub = ob.modifiers.new('sub', 'SUBSURF'); sub.levels = 1; sub.render_levels = 2

def build_dining_chair(px, py, face_deg):
    """cadeira de jantar estofada em bouclé creme, pés de freijó; olha para face_deg (planta)."""
    parts = []; w, d, hs = 0.47, 0.50, 0.47
    for lx in (-w / 2 + 0.035, w / 2 - 0.035):
        for ly in (-d / 2 + 0.035, d / 2 - 0.035):
            ob = cyl('CAD_PE', px + lx, py + ly, 0.0, hs - 0.06, 0.016, 0.022, M['freijo'], 16); parts.append(ob)
    parts.append(soft_box('CAD_ASSENTO', px - w / 2, px + w / 2, py - d / 2, py + d / 2, hs - 0.07, hs + 0.02, M['boucle_cad'], 0.035))
    ob = soft_box('CAD_ENCOSTO', px - w / 2 + 0.01, px + w / 2 - 0.01, py - d / 2 - 0.01, py - d / 2 + 0.06, hs + 0.0, hs + 0.40, M['boucle_cad'], 0.03)
    tilt_x(ob, (px, py - d / 2, hs), -8); parts.append(ob)
    for ob in parts: rot_obj(ob, (px, py), face_deg - 90)

def pendant_dome(name, cx, cy, zb, r, drop_to=H):
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=64, v_segments=32, radius=r)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-4], context='VERTS')
    for v in bm.verts: v.co = Vector((v.co.x, v.co.y, v.co.z * 0.72)) + P(cx, cy, zb)
    ob = mesh_obj(name, bm, [M['pendente_oliva'], M['branco_fosco']], 'moveis'); ob.data.shade_smooth()
    sl = ob.modifiers.new('esp', 'SOLIDIFY'); sl.thickness = 0.004; sl.material_offset = 1; sl.offset = -1
    cyl(name + '_CABO', cx, cy, zb + r * 0.72, drop_to, 0.003, mat=M['preto'], seg=8, smooth=False)
    cyl(name + '_CANOPLA', cx, cy, drop_to - 0.02, drop_to, 0.05, mat=M['preto'], seg=32)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=24, v_segments=12, radius=0.045, matrix=Matrix.Translation(P(cx, cy, zb + 0.06)))
    mesh_obj(name + '_LAMPADA', bm, M['lampada'], 'luz').data.shade_smooth()
    point_light(name + '_LUZ', cx, cy, zb + 0.06, 18)

def build_living():
    it = ITEMS
    # ---- parede da TV (norte, y = 0): pintura opcional, ripado, rack suspenso, TV 65" e nichos com LED
    if PAREDE == 'B':
        bm = bmesh.new(); vs = [bm.verts.new((x, -0.0012, z)) for x, z in ((2.165, 0.0), (5.59, 0.0), (5.59, H), (2.165, H))]
        bm.faces.new(vs); bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        for f in bm.faces:
            if f.normal.y > 0: f.normal_flip()
        mesh_obj('PAREDE_TV_VERDE_OLIVA', bm, M['verde_oliva'], 'arquitetura')
    def ripado(name, x0, x1):
        bm = bmesh.new(); x = x0
        while x + 0.02 <= x1 + 1e-6: bm_box(bm, x, x + 0.02, 0.003, 0.038, 0.0, H - 0.002); x += 0.035
        mesh_obj(name, bm, M['freijo'], 'moveis')
    if PAREDE == 'A': ripado('PAINEL_RIPADO_TV', 3.22, 4.86)     # A: painel ripado atrás da TV, parede neutra
    ripado('COLUNA_RIPADA', 5.58, 5.87)                             # B: TV direto na parede verde, só a coluna ripada
    rx0, rx1, ry0, ry1, rz0, rz1 = 2.56, 5.50, 0.04, 0.44, 0.32, 0.62
    box('RACK', rx0, rx1, ry0, ry1 - 0.02, rz0, rz1, M['freijo'], 'moveis', bevel=0.003)
    nf = 4; wf = (rx1 - rx0) / nf
    for i in range(nf):
        box('RACK_FRENTE', rx0 + i * wf + 0.0015, rx0 + (i + 1) * wf - 0.0015, ry1 - 0.02, ry1, rz0 + 0.004, rz1 - 0.004, M['freijo'], 'moveis', bevel=0.002, uvrot=math.pi / 2)
    box('RACK_LED', rx0 + 0.05, rx1 - 0.05, ry1 - 0.10, ry1 - 0.08, rz0 - 0.004, rz0, M['led'], 'luz')
    tvx = 4.04; box('TV65', tvx - 0.73, tvx + 0.73, 0.045, 0.072, 0.98, 1.82, M['preto'], 'moveis', bevel=0.004)
    box('TV65_TELA', tvx - 0.722, tvx + 0.722, 0.0725, 0.0735, 0.988, 1.812, M['tv'], 'moveis')
    for z in (1.08, 1.46, 1.84):
        box('NICHO_PRATELEIRA', 4.91, 5.54, 0.038, 0.30, z - 0.03, z, M['freijo'], 'moveis', bevel=0.002)
        box('NICHO_LED', 4.94, 5.51, 0.20, 0.22, z - 0.034, z - 0.03, M['led'], 'luz')
    # decoração do rack e dos nichos (Poly Haven)
    ph('ceramic_vase_01', 2.85, 0.24, rz1, scale=0.9, name='vaso_rack_1'); ph('ceramic_vase_03', 3.02, 0.22, rz1, scale=0.8, name='vaso_rack_2')
    ph('potted_plant_04', 5.25, 0.24, rz1, scale=1.25, name='planta_rack')
    ph('book_encyclopedia_set_01', 5.22, 0.16, 1.08, scale=0.55, name='livros_nicho')
    ph('ceramic_vase_02', 5.05, 0.17, 1.46, scale=0.65, name='vaso_nicho_1'); ph('wooden_bowl_01', 5.34, 0.17, 1.46, scale=0.7, name='tigela_nicho')
    ph('potted_plant_04', 5.12, 0.17, 1.84, scale=0.9, name='planta_nicho'); ph('lambis_shell', 5.38, 0.16, 1.84, rot=30, scale=1.2, name='concha_nicho')
    # ---- sofá retrátil, almofadas, manta, tapete de juta
    sx0, sx1, sb = 2.62, 5.48, 2.97
    yf = build_sofa_retratil(sx0, sx1, sb, 1.05)
    for (px, mat, w, yaw) in ((2.98, 'almof_terracota', 0.50, 6), (3.40, 'almof_oliva', 0.46, -4), (3.80, 'almof_creme', 0.45, 3),
                              (4.72, 'almof_oliva', 0.46, 5), (5.10, 'almof_terracota', 0.50, -6)):
        pillow('ALMOFADA', px, sb - 0.56, 0.71, w, w, 0.16, M[mat], yaw=yaw, tilt=17)
    throw_blanket('MANTA_TRICO', 4.42, 5.06, sb - 0.50, yf + 0.012, 0.50, 0.14, M['manta_trico'])
    box('TAPETE_JUTA', 2.58, 5.52, 0.68, 2.62, 0.012, 0.026, M['juta'], 'moveis', bevel=0.007)
    # ---- arte sobre o sofá (molduras Poly Haven, artes próprias)
    for i, x in enumerate((3.66, 4.42)):
        k = ph_art('hanging_picture_frame_01', f'quadro{i + 1}', f'arte_{i + 1}.png')
        ph('hanging_picture_frame_01', x, 2.97 - 0.015, 1.24, rot=180, scale=0.98, key=k, name='quadro_sofa')
    # ---- iluminação de apoio: luminária de piso, mesa lateral com abajur, trilho com spots
    cx, cy = 2.66, 0.78
    for k in range(3):
        t = math.radians(90 + k * 120); fx, fy = cx + 0.22 * math.cos(t), cy + 0.22 * math.sin(t)
        cu = bpy.data.curves.new('tripe', 'CURVE'); cu.dimensions = '3D'; sp = cu.splines.new('POLY'); sp.points.add(1)
        sp.points[0].co = (*P(fx, fy, 0.012), 1); sp.points[1].co = (*P(cx, cy, 1.20), 1); cu.bevel_depth = 0.013; cu.materials.append(M['madeira_pe'])
        ob = bpy.data.objects.new('LUMINARIA_PISO_PERNA', cu); coll('moveis').objects.link(ob)
    sh = cyl('LUMINARIA_PISO_CUPULA', cx, cy, 1.24, 1.56, 0.235, 0.20, M['cupula'], 64); bm = bmesh.new(); bm.from_mesh(sh.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.normal.z) > 0.9], context='FACES'); bm.to_mesh(sh.data); bm.free()
    sh.modifiers.new('esp', 'SOLIDIFY').thickness = 0.003
    point_light('LUMINARIA_PISO_LUZ', cx, cy, 1.40, 14)
    tx, ty = 5.72, 2.62
    cyl('MESA_LATERAL_TAMPO', tx, ty, 0.52, 0.55, 0.24, mat=M['freijo'], seg=48, bevel=0.004)
    cyl('MESA_LATERAL_PE', tx, ty, 0.02, 0.52, 0.05, 0.07, M['freijo'], 32); cyl('MESA_LATERAL_BASE', tx, ty, 0.0, 0.02, 0.18, mat=M['freijo'], seg=48)
    build_table_lamp('ABAJUR', tx, ty, 0.55); point_light('ABAJUR_LUZ', tx, ty, 0.88, 9)
    l1 = next(l for l in PROP['luminarias'] if l['cod'] == 'L-01'); (ax, ay), (bx, by) = l1['a'], l1['b']
    box('TRILHO', ax, bx, ay - 0.018, ay + 0.018, H - 0.035, H, M['preto'], 'moveis')
    for i, sx in enumerate((ax + 0.25, ax + 0.75, bx - 0.75, bx - 0.25)):
        s = cyl('SPOT', sx, ay, H - 0.20, H - 0.05, 0.035, mat=M['preto'], seg=24)
        s.matrix_world = Matrix.Translation(P(sx, ay, H - 0.05)) @ Matrix.Rotation(math.radians(25 if i < 2 else -25), 4, 'X') @ Matrix.Translation(-P(sx, ay, H - 0.05))
    # ---- cortinas de voal até o teto, recolhidas nas laterais da porta-janela
    build_curtains(2.32, [(0.02, 0.80), (2.10, 2.95)], 0.02, 2.37)
    box('CORTINA_TRILHO', 2.30, 2.34, 0.02, 2.95, 2.37, 2.385, M['aluminio'], 'moveis')
    # ---- plantas (Poly Haven)
    ph('potted_plant_01', 2.47, 2.55, rot=30, scale=1.22, name='planta_janela')
    ph('potted_plant_02', it['D-11']['cx'], it['D-11']['cy'] - 0.03, rot=150, scale=1.05, name='planta_jantar')
    # ---- jantar: mesa de 6 lugares, cadeiras estofadas, pendente(s) verde-oliva
    jx, jy = 7.50, 1.95
    if MESA == 'redonda':
        R = 0.70
        cyl('MESA_TAMPO', jx, jy, 0.735, 0.77, R, mat=M['freijo'], seg=128, bevel=0.008)
        cyl('MESA_COLUNA', jx, jy, 0.04, 0.735, 0.15, 0.19, M['freijo'], 64)
        cyl('MESA_BASE', jx, jy, 0.0, 0.04, 0.40, 0.42, M['freijo'], 96)
        for ang in (0, 60, 120, 180, 240, 300):
            t = math.radians(ang); px, py = jx + 0.88 * math.cos(t), jy + 0.88 * math.sin(t)
            build_dining_chair(px, py, math.degrees(math.atan2(jy - py, jx - px)))
        pendant_dome('PENDENTE', jx, jy, 1.57, 0.26)
        ph('wooden_bowl_01', jx - 0.10, jy + 0.05, 0.77, scale=1.1, name='fruteira'); ph('ceramic_vase_02', jx + 0.16, jy - 0.08, 0.77, scale=0.8, name='vaso_mesa')
    else:
        L_, W_ = 1.80, 0.95; x0, x1, y0, y1 = jx - L_ / 2, jx + L_ / 2, jy - W_ / 2, jy + W_ / 2
        box('MESA_TAMPO', x0, x1, y0, y1, 0.735, 0.775, M['freijo'], 'moveis', bevel=0.006)
        for lx in (x0 + 0.28, x1 - 0.34):
            box('MESA_PE', lx, lx + 0.06, y0 + 0.12, y1 - 0.12, 0.0, 0.735, M['freijo'], 'moveis', bevel=0.004)
        box('MESA_TRAVESSA', x0 + 0.34, x1 - 0.34, jy - 0.03, jy + 0.03, 0.62, 0.70, M['freijo'], 'moveis', bevel=0.003)
        for px in (jx - 0.58, jx, jx + 0.58):
            build_dining_chair(px, y0 - 0.17, 90); build_dining_chair(px, y1 + 0.17, -90)
        for px in (jx - 0.45, jx + 0.45): pendant_dome('PENDENTE', px, jy, 1.58, 0.19)
        ph('wooden_bowl_01', jx - 0.25, jy, 0.775, scale=1.1, name='fruteira'); ph('ceramic_vase_02', jx + 0.10, jy - 0.05, 0.775, scale=0.8, name='vaso_mesa')
        ph('potted_plant_04', jx + 0.35, jy + 0.05, 0.775, scale=1.0, name='planta_mesa')
    # ---- parede do jantar: só arte na parede (nada no chão no caminho da entrada)
    for i, x in enumerate((7.10, 7.90)):
        k = ph_art('hanging_picture_frame_01', f'quadro{4 + i}', f'arte_{4 + i}.png')
        ph('hanging_picture_frame_01', x, 0.012, 1.22, rot=0, scale=0.98, key=k, name='quadro_jantar')
    # ---- varanda: bistrô e planta (Poly Haven)
    ph('outdoor_table_chair_set_01', it['D-12']['cx'] - 0.05, it['D-12']['cy'] + 0.25, rot=90, scale=0.95, name='D12_bistro')
    ph('potted_plant_01', it['D-13']['cx'] + 0.02, it['D-13']['cy'] + 0.05, rot=80, scale=1.0, name='D13_planta')

def build_curtain(name, x, a, b, opened, z0, z1, depth=0.07):
    """cortina wave recolhida no trecho 'opened' (y0..y1) junto à parede, na linha x."""
    y0, y1 = opened; n = 34; bm = bmesh.new(); rows = []
    for i in range(n + 1):
        t = i / n; y = y0 + (y1 - y0) * t
        xx = x + depth / 2 * math.sin(t * math.pi * 14)
        rows.append((bm.verts.new(P(xx, y, z0)), bm.verts.new(P(xx, y, z1))))
    for i in range(n): bm.faces.new([rows[i][0], rows[i + 1][0], rows[i + 1][1], rows[i][1]])
    ob = mesh_obj(name, bm, M['linho_cortina'], 'moveis', uvrot=math.pi / 2); ob.data.shade_smooth()
    ob.modifiers.new('esp', 'SOLIDIFY').thickness = 0.004
    sub = ob.modifiers.new('sub', 'SUBSURF'); sub.levels = 1; sub.render_levels = 2
    box(name + '_TRILHO', x - 0.02, x + 0.02, a, b, z1, z1 + 0.02, M['aluminio'], 'moveis')

def build_table_lamp(cod, cx, cy, z):
    s = cyl(cod + '_BASE', cx, cy, z, z + 0.22, 0.10, mat=M['ceramica'], seg=48)
    bm = bmesh.new(); bmesh.ops.create_uvsphere(bm, u_segments=48, v_segments=24, radius=0.105, matrix=Matrix.Translation(P(cx, cy, z + 0.12)))
    for v in bm.verts: v.co.z = z + 0.12 + (v.co.z - (z + 0.12)) * 1.05
    ob = mesh_obj(cod + '_BOJO', bm, M['ceramica']); ob.data.shade_smooth()
    bpy.data.objects.remove(s)
    cyl(cod + '_HASTE', cx, cy, z + 0.22, z + 0.32, 0.008, mat=M['inox'], seg=12)
    sh = cyl(cod + '_CUPULA', cx, cy, z + 0.27, z + 0.47, 0.15, 0.12, M['cupula'], 64); bm = bmesh.new(); bm.from_mesh(sh.data)
    bmesh.ops.delete(bm, geom=[f for f in bm.faces if abs(f.normal.z) > 0.9], context='FACES'); bm.to_mesh(sh.data); bm.free()
    sh.modifiers.new('esp', 'SOLIDIFY').thickness = 0.003

# ======================================================================== cozinha
def kbox(name, wall, a, b, dep, z0, z1, mat, inset=0.001, bevel=0.0, front_off=0.0):
    """caixa de marcenaria encostada na parede N (y=1.02, ao longo de x) ou E (x=14.10, ao longo de y)."""
    a, b = a + 0.0004, b - 0.0004
    if wall == 'N': return box(name, a, b, 1.02 + inset, 1.02 + dep + front_off, z0, z1, mat, 'cozinha', bevel=bevel)
    return box(name, 14.10 - dep - front_off, 14.10 - inset, a, b, z0, z1, mat, 'cozinha', bevel=bevel)

def kfront(name, wall, a, b, dep, z0, z1, mat, t=0.018, bevel=0.0015):
    if wall == 'N': return box(name, a, b, 1.02 + dep, 1.02 + dep + t, z0, z1, mat, 'cozinha', bevel=bevel)
    return box(name, 14.10 - dep - t, 14.10 - dep, a, b, z0, z1, mat, 'cozinha', bevel=bevel)

def doors_row(name, wall, a, b, dep, z0, z1, n, mat=None, cava='top'):
    mat = mat or M['branco_mdf']; g = 0.003; wd = (b - a) / n
    for i in range(n):
        u0, u1 = a + i * wd + g / 2, a + (i + 1) * wd - g / 2
        if cava == 'top': kfront(name, wall, u0, u1, dep, z0 + g, z1 - 0.035, mat); kfront(name + '_cava', wall, u0, u1, dep - 0.02, z1 - 0.035, z1 - 0.004, M['grafite'], t=0.02)
        elif cava == 'bottom': kfront(name, wall, u0, u1, dep, z0 + 0.03, z1 - g, mat); kfront(name + '_cava', wall, u0, u1, dep - 0.02, z0 + 0.004, z0 + 0.03, M['grafite'], t=0.02)
        else: kfront(name, wall, u0, u1, dep, z0 + g, z1 - g, mat)

def build_kitchen():
    paineis = [(m['wall'], m['a'], m['b']) for m in PROP['cozinha'] if m['tipo'] == 'painel']
    for m in PROP['cozinha']:
        w, a, b, dep, (z0, z1), t = m['wall'], m['a'], m['b'], m['dep'], m['z'], m['tipo']; nm = m['id']
        for pw, pa, pb in paineis:   # módulo que invade o painel lateral termina na face do painel
            if t != 'painel' and pw == w and a < pa < b: b = pa
            if t != 'painel' and pw == w and a < pb < b: a = pb
        if t in ('base', 'canto', 'gaveteiro'):
            kbox(nm + '_rodape', w, a, b, dep - 0.06, 0.0, z0, M['grafite'])
            kbox(nm + '_caixa', w, a, b, dep - 0.002, z0, z1, M['branco_mdf'])
            if t == 'gaveteiro':
                hh = (z1 - z0) / m['gavetas']
                for i in range(m['gavetas']):
                    za = z0 + i * hh
                    kfront(nm + '_gav', w, a + 0.0015, b - 0.0015, dep - 0.002, za + 0.002, za + hh - 0.035, M['branco_mdf'])
                    kfront(nm + '_cava', w, a + 0.0015, b - 0.0015, dep - 0.02, za + hh - 0.035, za + hh - 0.004, M['grafite'], t=0.02)
            else: doors_row(nm, w, a, b, dep - 0.002, z0, z1, m.get('portas', 1))
        elif t == 'aereo':
            kbox(nm + '_caixa', w, a, b, dep - 0.018, z0, z1, M['branco_mdf'])
            doors_row(nm, w, a, b, dep - 0.018, z0, z1, m.get('portas', 1), cava='bottom')
            kbox(nm + '_led', w, a + 0.02, b - 0.02, dep - 0.06, z0 - 0.004, z0, M['led_coz'], inset=dep - 0.08)
        elif t == 'painel':
            kbox(nm, w, a, b, dep, 0.0, z1, M['branco_mdf'])
        elif t == 'nicho':
            for u0, u1 in ((a, a + 0.018), (b - 0.018, b)): kbox(nm + '_lat', w, u0, u1, dep, z0, z1, M['freijo'])
            for zz in ((z0, z0 + 0.018), (z1 - 0.018, z1)) + tuple((p - 0.009, p + 0.009) for p in m.get('prat', [])):
                kbox(nm + '_prat', w, a + 0.018, b - 0.018, dep, *zz, M['freijo'])
            u = a + 0.02
            while u + 0.02 <= b - 0.02:
                kbox(nm + '_ripa', w, u, u + 0.02, 0.03, z0 + 0.018, z1 - 0.018, M['freijo']); u += 0.035
            kbox(nm + '_led', w, a + 0.03, b - 0.03, dep - 0.06, z0 - 0.004, z0, M['led_coz'], inset=dep - 0.08)
        elif t == 'torre':
            n0, n1 = m['nicho']
            kbox(nm + '_rodape', w, a, b, dep - 0.06, 0.0, z0, M['grafite'])
            kbox(nm + '_caixa', w, a, b, dep - 0.002, z0, n0, M['branco_mdf'])
            kbox(nm + '_caixa', w, a, b, dep - 0.002, n1, z1, M['branco_mdf'])
            for u0, u1 in ((a, a + 0.018), (b - 0.018, b)): kbox(nm + '_lat', w, u0, u1, dep - 0.002, n0, n1, M['branco_mdf'])
            kbox(nm + '_fundo', w, a + 0.018, b - 0.018, 0.02, n0, n1, M['grafite'])
            kfront(nm + '_porta', w, a + 0.0015, b - 0.0015, dep - 0.002, z0 + 0.002, n0 - 0.035, M['branco_mdf'])
            kfront(nm + '_cava', w, a + 0.0015, b - 0.0015, dep - 0.02, n0 - 0.035, n0 - 0.004, M['grafite'], t=0.02)
            kfront(nm + '_porta', w, a + 0.0015, b - 0.0015, dep - 0.002, n1 + 0.03, z1 - 0.002, M['branco_mdf'])
            kfront(nm + '_cava', w, a + 0.0015, b - 0.0015, dep - 0.02, n1 + 0.004, n1 + 0.03, M['grafite'], t=0.02)
        elif t == 'geladeira':
            kbox(nm + '_corpo', w, a, b, dep - 0.03, 0.02, z1, M['inox'], bevel=0.01)
            kfront(nm + '_porta', w, a + 0.004, b - 0.004, dep - 0.03, 0.72, z1 - 0.004, M['inox'], t=0.03, bevel=0.006)
            kfront(nm + '_gaveta', w, a + 0.004, b - 0.004, dep - 0.03, 0.03, 0.70, M['inox'], t=0.03, bevel=0.006)
            hx = b - 0.06
            box(nm + '_puxador', hx - 0.012, hx + 0.012, 1.02 + dep + 0.0, 1.02 + dep + 0.035, 0.95, 1.65, M['inox_escuro'], 'cozinha', bevel=0.004)
            box(nm + '_puxador', a + 0.10, b - 0.10, 1.02 + dep + 0.0, 1.02 + dep + 0.035, 0.62, 0.645, M['inox_escuro'], 'cozinha', bevel=0.004)
        elif t == 'lavalouca':
            kbox(nm + '_corpo', w, a, b, dep - 0.02, 0.0, z1, M['grafite'])
            kfront(nm + '_porta', w, a + 0.002, b - 0.002, dep - 0.02, 0.08, z1 - 0.004, M['inox'], t=0.02, bevel=0.003)
            box(nm + '_painel', a + 0.002, b - 0.002, 1.02 + dep, 1.02 + dep + 0.002, z1 - 0.07, z1 - 0.01, M['preto_vidro'], 'cozinha')
            box(nm + '_puxador', a + 0.08, b - 0.08, 1.02 + dep + 0.0, 1.02 + dep + 0.03, z1 - 0.12, z1 - 0.095, M['inox_escuro'], 'cozinha', bevel=0.004)
        elif t == 'fogao':
            build_stove(a, b, dep, z1)
        elif t == 'depurador':
            kbox(nm, w, a, b, dep, z0, z1, M['inox'], bevel=0.004)
            kbox(nm + '_filtro', w, a + 0.02, b - 0.02, dep - 0.02, z0 - 0.002, z0, M['inox_escuro'])
            kbox(nm + '_duto', w, (a + b) / 2 - 0.12, (a + b) / 2 + 0.12, 0.22, z1, 2.30, M['inox'], bevel=0.003)
        elif t == 'micro':
            yf = 1.02 + 0.58
            box(nm + '_corpo', a, b, yf - dep, yf, z0, z1, M['inox'], 'cozinha', bevel=0.004)
            box(nm + '_porta', a + 0.01, b - 0.13, yf, yf + 0.003, z0 + 0.02, z1 - 0.02, M['preto_vidro'], 'cozinha')
            box(nm + '_painel', b - 0.12, b - 0.01, yf, yf + 0.003, z0 + 0.02, z1 - 0.02, M['inox_escuro'], 'cozinha')
    # bancadas com recorte da cuba e frontão em porcelanato
    for bc in PROP['bancadasCozinha']:
        x0, y0, x1, y1 = bc['r']; ob = box('BANCADA_' + bc['nome'], x0, x1, y0, y1, 0.88, 0.92, M['marmore'], 'cozinha', bevel=0.002)
        if bc['nome'] == 'Bancada da pia':
            cb = PROP['cubaCozinha']; cut = box('corte', cb['cx'] - cb['d'] / 2, cb['cx'] + cb['d'] / 2, cb['cy'] - cb['w'] / 2, cb['cy'] + cb['w'] / 2, 0.80, 1.0, M['inox'])
            md = ob.modifiers.new('cuba', 'BOOLEAN'); md.object = cut; md.operation = 'DIFFERENCE'; md.solver = 'EXACT'
            bpy.context.view_layer.objects.active = ob; bpy.ops.object.modifier_apply(modifier='cuba'); bpy.data.objects.remove(cut)
            build_sink(cb)
    for f in PROP['frontao']:
        z0, z1 = f['z']
        if f['ax'] == 'x': box('FRONTAO', f['a'], f['b'], f['c'], f['c'] + 0.01, z0, z1, M['marmore'], 'cozinha')
        else: box('FRONTAO', f['c'] - 0.01, f['c'], f['a'], f['b'], z0, z1, M['marmore'], 'cozinha')
    # luminária linear L-09 (desligada de dia)
    l9 = next(l for l in PROP['luminarias'] if l['cod'] == 'L-09'); (ax, ay), (bx, by) = l9['a'], l9['b']
    box('L09_LINEAR', ax, bx, ay - 0.04, ay + 0.04, H - 0.05, H, M['aluminio'], 'cozinha', bevel=0.004)
    box('L09_DIFUSOR', ax + 0.01, bx - 0.01, ay - 0.03, ay + 0.03, H - 0.051, H - 0.05, M['led_coz'], 'luz')
    # decoração (Poly Haven) e utensílios
    ph('potted_plant_04', 9.55, 1.32, 0.92, rot=20, scale=1.0, name='suculenta_cafe')
    ph('jug_01', 9.98, 1.28, 0.92, rot=-30, scale=0.9, name='jarra_cafe')
    ph('ceramic_vase_02', 9.55, 1.20, 1.888, scale=0.55, name='vaso_nicho')
    ph('ceramic_vase_04', 9.90, 1.18, 1.888, scale=0.6, name='vaso_nicho2')
    ph('wooden_bowl_01', 9.80, 1.18, 1.468, scale=0.75, name='tigela_nicho')
    ph('tea_set_01', 13.00, 1.30, 0.92, rot=0, scale=0.55, name='bule_bancada')
    for i, (hh, ww) in enumerate(((0.42, 0.28), (0.34, 0.24))):
        b0 = box('TABUA', 13.55 + i * 0.10, 13.55 + i * 0.10 + ww, 1.035 + i * 0.02, 1.053 + i * 0.02, 0.92, 0.92 + hh, M['teca'], 'cozinha', bevel=0.004)
    ph('ceramic_vase_01', 13.96, 2.52, 0.92, scale=0.45, name='saleiro') if False else None

def build_stove(a, b, dep, z1):
    x0, x1 = 14.10 - dep, 14.10; y0, y1 = a, b
    box('E03_CORPO', x0 + 0.02, x1, y0, y1, 0.02, 0.86, M['inox'], 'cozinha', bevel=0.004)
    box('E03_PES', x0 + 0.06, x1 - 0.04, y0 + 0.04, y1 - 0.04, 0.0, 0.02, M['grafite'], 'cozinha')
    box('E03_PAINEL', x0, x0 + 0.02, y0 + 0.004, y1 - 0.004, 0.74, 0.86, M['inox'], 'cozinha', bevel=0.003)
    box('E03_PORTA', x0 - 0.002, x0 + 0.02, y0 + 0.01, y1 - 0.01, 0.10, 0.72, M['inox'], 'cozinha', bevel=0.004)
    box('E03_VISOR', x0 - 0.003, x0 - 0.002, y0 + 0.08, y1 - 0.08, 0.24, 0.58, M['preto_vidro'], 'cozinha')
    box('E03_PUXADOR', x0 - 0.04, x0 - 0.025, y0 + 0.08, y1 - 0.08, 0.66, 0.68, M['inox_escuro'], 'cozinha', bevel=0.005)
    for i in range(6):
        yy = y0 + 0.09 + i * (y1 - y0 - 0.18) / 5
        k = cyl('E03_BOTAO', x0 - 0.02, yy, 0.79, 0.81, 0.018, mat=M['inox_escuro'], seg=24)
        k.data.transform(Matrix.Translation(-P(x0 - 0.02, yy, 0.80))); k.rotation_euler = (0, math.radians(90), 0); k.location = P(x0 - 0.012, yy, 0.80)
    box('E03_MESA', x0 + 0.02, x1, y0, y1, 0.86, 0.875, M['inox'], 'cozinha', bevel=0.002)
    # grelhas de ferro fundido e queimadores
    for gy0, gy1 in ((y0 + 0.02, (y0 + y1) / 2 - 0.005), ((y0 + y1) / 2 + 0.005, y1 - 0.02)):
        for xx in (x0 + 0.06, x1 - 0.06, (x0 + x1) / 2):
            box('E03_GRELHA', xx - 0.006, xx + 0.006, gy0, gy1, 0.875, 0.905, M['preto'], 'cozinha')
        for yy in (gy0, gy1 - 0.012, (gy0 + gy1) / 2):
            box('E03_GRELHA', x0 + 0.05, x1 - 0.05, yy, yy + 0.012, 0.875, 0.905, M['preto'], 'cozinha')
    for (bx, by, r) in ((x0 + 0.17, y0 + 0.17, 0.045), (x1 - 0.17, y0 + 0.17, 0.035), ((x0 + x1) / 2, (y0 + y1) / 2, 0.06), (x0 + 0.17, y1 - 0.17, 0.035), (x1 - 0.17, y1 - 0.17, 0.045)):
        cyl('E03_QUEIM', bx, by, 0.875, 0.892, r, mat=M['grafite'], seg=32)

def build_sink(cb):
    x0, x1 = cb['cx'] - cb['d'] / 2, cb['cx'] + cb['d'] / 2; y0, y1 = cb['cy'] - cb['w'] / 2, cb['cy'] + cb['w'] / 2
    bm = bmesh.new(); fs = bm_box(bm, x0, x1, y0, y1, 0.70, 0.905)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    top = [f for f in bm.faces if f.normal.z > 0.9]; bmesh.ops.delete(bm, geom=top, context='FACES')
    ob = mesh_obj('CUBA_INOX', bm, M['inox'], 'cozinha'); md = ob.modifiers.new('esp', 'SOLIDIFY'); md.thickness = 0.008; md.offset = 1
    ob.modifiers.new('bev', 'BEVEL').width = 0.012; ob.modifiers['bev'].segments = 3
    cyl('RALO', cb['cx'], cb['cy'], 0.701, 0.704, 0.04, mat=M['inox_escuro'], seg=24)
    # misturador bica alta (gourmet)
    fx, fy = 14.10 - 0.06, cb['cy']
    cyl('TORNEIRA_BASE', fx, fy, 0.92, 0.98, 0.025, mat=M['inox'], seg=32)
    cu = bpy.data.curves.new('bica', 'CURVE'); cu.dimensions = '3D'; sp = cu.splines.new('BEZIER'); sp.bezier_points.add(2)
    pts = [P(fx, fy, 0.98), P(fx, fy, 1.32), P(fx - 0.20, fy, 1.15)]
    for i, p in enumerate(pts): sp.bezier_points[i].co = p; sp.bezier_points[i].handle_left_type = sp.bezier_points[i].handle_right_type = 'AUTO'
    cu.bevel_depth = 0.012; cu.bevel_resolution = 6; cu.resolution_u = 24; cu.materials.append(M['inox'])
    ob = bpy.data.objects.new('TORNEIRA_BICA', cu); coll('cozinha').objects.link(ob)
    box('TORNEIRA_ALAV', fx - 0.005, fx + 0.005, fy + 0.025, fy + 0.10, 1.02, 1.035, M['inox'], 'cozinha', bevel=0.003)

# ======================================================================== suíte
def build_bedroom():
    cx = (3.87 + 7.72) / 2; wall = 7.89; bw, bl = 1.58, 1.98
    x0, x1 = cx - bw / 2, cx + bw / 2; yh = wall - 0.09; y0 = yh - bl
    # painel de cabeceira em freijó de parede a parede entre criados e cabeceira estofada em linho
    box('CABECEIRA_PAINEL', cx - 1.55, cx + 1.55, wall - 0.03, wall, 0.0, 1.20, M['freijo'], 'quarto', bevel=0.003)
    soft_box('CABECEIRA_ESTOFADA', x0 - 0.10, x1 + 0.10, wall - 0.09, wall - 0.03, 0.42, 1.12, M['cabeceira'], 0.03, 'quarto')
    box('CAMA_RODAPE', x0 + 0.08, x1 - 0.08, y0 + 0.08, yh - 0.05, 0.0, 0.10, M['grafite'], 'quarto')
    soft_box('CAMA_BOX', x0, x1, y0, yh, 0.10, 0.38, M['cabeceira'], 0.02, 'quarto')
    soft_box('COLCHAO', x0 + 0.01, x1 - 0.01, y0 + 0.01, yh - 0.01, 0.38, 0.60, M['lencol'], 0.05, 'quarto')
    # edredom caindo nas laterais + dobra
    soft_box('EDREDOM', x0 - 0.035, x1 + 0.035, y0 - 0.035, yh - 0.55, 0.36, 0.635, M['lencol'], 0.06, 'quarto')
    soft_box('EDREDOM_DOBRA', x0 - 0.03, x1 + 0.03, yh - 0.66, yh - 0.50, 0.60, 0.665, M['lencol'], 0.05, 'quarto')
    soft_box('MANTA', x0 - 0.05, x1 + 0.05, y0 - 0.045, y0 + 0.45, 0.30, 0.648, M['manta'], 0.05, 'quarto')
    for px in (cx - 0.39, cx + 0.39):
        ob = soft_box('TRAVESSEIRO', px - 0.36, px + 0.36, yh - 0.42, yh - 0.06, 0.60, 0.76, M['lencol'], 0.07, 'quarto')
        ob.matrix_world = Matrix.Translation(P(px, yh - 0.24, 0.68)) @ Matrix.Rotation(math.radians(-14), 4, 'X') @ Matrix.Translation(-P(px, yh - 0.24, 0.68))
    ph('throw_pillows_01', cx, yh - 0.48, 0.60, rot=180, scale=0.85, name='almofadas_cama')
    # criados-mudos (Poly Haven) com pendentes de vidro (Poly Haven) e decoração
    for sx in (x0 - 0.36, x1 + 0.36):
        ph('side_table_01', sx, wall - 0.27, rot=180, name='criado_mudo')
        ph('modern_ceiling_lamp_01', sx, wall - 0.30, H - ph_dims('modern_ceiling_lamp_01').z * 1.0 - 0.0, name='pendente_quarto')
    ph('book_encyclopedia_set_01', x0 - 0.42, wall - 0.25, 0.552, rot=90, scale=0.35, name='livros_criado')
    ph('ceramic_vase_02', x0 - 0.26, wall - 0.30, 0.552, scale=0.7, name='vaso_criado')
    ph('potted_plant_04', x1 + 0.32, wall - 0.26, 0.552, scale=0.9, name='suculenta_criado')
    k = ph_art('hanging_picture_frame_02', 'quadro3', 'arte_3.png')
    ph('hanging_picture_frame_02', cx, wall - 0.03, 1.45, rot=180, scale=1.15, key=k, name='quadro_cama')
    box('TAPETE_QUARTO', cx - 1.40, cx + 1.40, y0 - 0.70, yh - 0.55, 0.012, 0.024, M['tapete_q'], 'quarto', bevel=0.006)
    # recanto de leitura junto à porta-janela
    ph('mid_century_lounge_chair', 3.30, 7.30, rot=120, scale=0.9, name='poltrona_leitura')
    ph('potted_plant_01', 3.55, 6.62, rot=10, scale=1.1, name='planta_recanto')
    build_curtain('CORTINA_SUITE', 2.86, 6.39, 7.89, (7.20, 7.87), 0.02, H - 0.02, depth=0.08)
    cyl('PLAFON_SUITE', cx, 6.35, H - 0.04, H, 0.20, mat=M['aluminio'], seg=48)

# ======================================================================== mundo, sol e câmeras
def build_world():
    w = bpy.data.worlds.new('CEU'); sc.world = w; w.use_nodes = True; nt = w.node_tree; N = nt.nodes; N.clear(); L = nt.links
    o = N.new('ShaderNodeOutputWorld'); bg = N.new('ShaderNodeBackground'); env = N.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(os.path.join(PH, 'hdri', 'kloofendal_48d_partly_cloudy_puresky_4k.hdr'))
    tc = N.new('ShaderNodeTexCoord'); mp = N.new('ShaderNodeMapping'); mp.inputs['Rotation'].default_value = (0, 0, math.radians(SKY_ROT))
    L.new(tc.outputs['Generated'], mp.inputs['Vector']); L.new(mp.outputs[0], env.inputs['Vector'])
    cl = N.new('ShaderNodeVectorMath'); cl.operation = 'MINIMUM'; cl.inputs[1].default_value = (SKY_CLAMP,) * 3   # tira o sol do HDRI (o sol vem da lâmpada)
    L.new(env.outputs['Color'], cl.inputs[0]); L.new(cl.outputs[0], bg.inputs['Color']); bg.inputs['Strength'].default_value = SKY_STRENGTH
    L.new(bg.outputs[0], o.inputs['Surface'])
    sd = bpy.data.lights.new('SOL', 'SUN'); sd.energy = SUN_STRENGTH; sd.color = SUN_COLOR; sd.angle = math.radians(0.6)
    so = bpy.data.objects.new('SOL', sd); coll('luz').objects.link(so)
    az, el = math.radians(SUN_AZ), math.radians(SUN_EL)
    d = Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))   # direção até o sol (Blender)
    so.rotation_euler = (-d).to_track_quat('-Z', 'Y').to_euler()
    # portais de luz nas aberturas (ajudam o Cycles a amostrar o céu)
    for nm, c, sx, sy, normal in (('portal_sala', P(2.10, 1.485, 1.25), 2.97, 2.50, (1, 0, 0)), ('portal_suite', P(2.66, 7.14, 1.21), 1.50, 2.42, (1, 0, 0)),
                                  ('portal_area', P(13.40, 6.30, 1.65), 1.10, 1.10, (0, 1, 0)), ('portal_q1', P(1.22, 5.52, 1.6), 1.15, 1.2, (1, 0, 0))):
        ld = bpy.data.lights.new(nm, 'AREA'); ld.shape = 'RECTANGLE'; ld.size = sx; ld.size_y = sy; ld.cycles.is_portal = True
        ob = bpy.data.objects.new(nm, ld); coll('luz').objects.link(ob); ob.location = c
        ob.rotation_euler = Vector(normal).to_track_quat('-Z', 'Y').to_euler()

SKY_ROT, SKY_CLAMP, SKY_STRENGTH = 123.0, 25.0, 1.0
SUN_AZ, SUN_EL, SUN_STRENGTH, SUN_COLOR = 200.0, 21.0, 4.2, (1.0, 0.90, 0.76)

CAMS = {   # (posição na planta, alvo na planta, lente mm, shift_y)
    'sala':         ((9.05, 2.85), (2.40, 1.25), 18, -0.05),
    'estar':        ((6.25, 2.62), (2.45, 1.30), 18, -0.06),
    'cozinha-pia':  ((13.75, 4.05), (13.45, 1.00), 16, -0.05),
    'cozinha-cafe': ((9.85, 3.14), (10.75, 1.00), 16, -0.05),
    'quarto':       ((7.50, 5.00), (4.30, 7.70), 16, -0.05),
}
EXPO = {'estar': 2.4, 'sala': 2.4, 'cozinha-pia': 2.9, 'cozinha-cafe': 2.9, 'quarto': 3.4, 'planta': 1.0}
EYE = 1.60
LED_SALA, LUZ_SALA = 1.2, 1.0

def add_camera(name):
    if name == 'planta':
        cd = bpy.data.cameras.new('cam_planta'); cd.type = 'ORTHO'; cd.ortho_scale = 17.2
        cam = bpy.data.objects.new('cam_planta', cd); coll('cameras').objects.link(cam); cam.location = P(8.26, 3.95, 12.0)
        for o in bpy.data.objects:
            if o.name.startswith(('LAJE_TETO', 'SANCA', 'L01_', 'L03_', 'L09_', 'pendente', 'PLAFON')) or o.type == 'LIGHT' and o.data.type == 'AREA': o.hide_render = True
        return cam
    (px, py), (tx, ty), lens, shy = CAMS[name]
    cd = bpy.data.cameras.new('cam_' + name); cd.lens = lens; cd.sensor_width = 36; cd.sensor_fit = 'HORIZONTAL'; cd.clip_start = 0.05; cd.shift_y = shy
    cam = bpy.data.objects.new('cam_' + name, cd); coll('cameras').objects.link(cam)
    eye, look = P(px, py, EYE), P(tx, ty, EYE)
    cam.location = eye; cam.rotation_euler = (look - eye).to_track_quat('-Z', 'Y').to_euler(); return cam

# ======================================================================== montagem
t0 = __import__('time').time()
walls = build_walls(); build_openings(); build_floors(); build_baseboards(walls); build_rail()
build_living(); build_kitchen(); build_bedroom(); build_world()
print(f'cena montada em {__import__("time").time() - t0:.0f}s', flush=True)

sc.render.engine = 'CYCLES'; cy = sc.cycles; cy.device = 'CPU'; cy.samples = SAMPLES
cy.use_adaptive_sampling = True; cy.adaptive_threshold = 0.012; cy.use_denoising = True; cy.denoiser = 'OPENIMAGEDENOISE'
cy.max_bounces = 10; cy.diffuse_bounces = 5; cy.glossy_bounces = 4; cy.transmission_bounces = 8; cy.transparent_max_bounces = 16
cy.sample_clamp_indirect = 6.0; cy.caustics_reflective = False; cy.caustics_refractive = False
try: cy.use_light_tree = True
except Exception: pass
sc.render.use_persistent_data = True
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = RW, RH, 100
sc.render.image_settings.file_format = 'PNG'
vs = sc.view_settings; vs.view_transform = 'AgX'
try: vs.look = 'AgX - Base Contrast'
except Exception: pass
if SAVE: bpy.ops.wm.save_as_mainfile(filepath=SAVE)
os.makedirs(OUT, exist_ok=True)
for v in VIEWS:
    cam = add_camera(v); sc.camera = cam; vs.exposure = EXPO.get(v, 0.0)
    kitchen = v.startswith('cozinha')
    M['led_coz'].node_tree.nodes['Emission'].inputs['Strength'].default_value = 6.0 if kitchen else 0.0
    sala = v in ('sala', 'estar')
    M['led'].node_tree.nodes['Emission'].inputs['Strength'].default_value = LED_SALA if sala else 0.0
    M['lampada'].node_tree.nodes['Emission'].inputs['Strength'].default_value = 40.0 if sala else 0.0
    for ld, wts in LIGHTS_ON: ld.energy = wts * LUZ_SALA if sala else 0.0
    if os.environ.get('PIX'):
        dg = bpy.context.evaluated_depsgraph_get(); cd = cam.data
        fr = [cam.matrix_world @ q for q in cd.view_frame(scene=sc)]
        for pp in os.environ['PIX'].split(';'):
            u, w_ = map(float, pp.split(',')); top = fr[3].lerp(fr[0], u); bot = fr[2].lerp(fr[1], u); pt = top.lerp(bot, w_)
            d = (pt - cam.location).normalized(); org = cam.location.copy(); hits = []
            for _ in range(3):
                ok, loc, nor, idx, ob, mx = sc.ray_cast(dg, org, d)
                if not ok: hits.append('none'); break
                mn = ob.material_slots[ob.data.polygons[idx].material_index].material.name if ob.type == 'MESH' and ob.material_slots and idx < len(ob.data.polygons) else '?'
                hits.append(f'{ob.name}/{mn} ({loc.x:.2f},{-loc.y:.2f},{loc.z:.2f}) n=({nor.x:.1f},{-nor.y:.1f},{nor.z:.1f})'); org = loc + d * 0.002
            print('PIX', v, pp, ' | '.join(hits), flush=True)
        continue
    sc.render.filepath = os.path.join(OUT, f'{v}_{OPCAO}.png' if '--opcao' in ARGS else f'{v}.png'); t1 = __import__('time').time()
    bpy.ops.render.render(write_still=True)
    print(f'{v}: {__import__("time").time() - t1:.0f}s', flush=True)
