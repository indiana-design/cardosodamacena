/* Apartamento 02 — dados compartilhados entre o modelo 3D (index.html) e as pranchas (projeto.html).
   Coordenadas em metros, na orientação da planta: x → direita (hall), y → baixo (fachada). */
function arcPts(cx,cy,r,a0,a1,n){ const out=[]; for(let i=0;i<=n;i++){ const t=a0+(a1-a0)*i/n; out.push([cx+r*Math.cos(t), cy+r*Math.sin(t)]); } return out; }
function rect(x0,y0,x1,y1){ return [[x0,y0],[x1,y0],[x1,y1],[x0,y1]]; }
const PE_DIREITO = 2.60;
/* Planta: medidas das anotações (cômodos, m²)
   Sala 3,65×3,00 + 3,40×3,75 + 1,35×0,90 = 24,91 · Cozinha 4,80×2,25 = 10,80
   Circulação 4,35×0,90 (+ passagem) = 4,33 · WC social 2,15×1,35 = 2,90
   Área 1,45×2,95 = 4,27 · Qto. serviço 2,10×2,20 = 4,62 · WC serviço 2,10×0,90 = 1,89
   Suíte 3,85×3,00 + 1,22×1,50 = 13,38 · WC suíte 1,25×3,00 = 3,75 · Quarto 2 3,20×3,00 = 9,60
   Quarto 1 4,45×1,65 + 2,45×1,50 ≈ 11,01 · Varanda ≈ 12,11 */
const Q1 = {cx:2.40, cy:4.22, r:1.10};               // canto curvo do quarto 1
const RAIL = {cx:3.97, cy:4.40, R:3.97, a0:1.946};    // guarda-corpo curvo da varanda
// Paredes: [x0,x1,y0,y1] + aberturas ao longo do eixo maior (usadas pela planta baixa e pelo 3D)
const WALLS=[
  {r:[0,10.65,-0.20,0]},                                                                  // divisa com o apto 01
  {r:[10.50,10.65,-0.20,1.02], ops:[{a:0.06,b:0.88,t:'main',hinge:'start',swing:-1,ang:0}]}, // porta social (hall)
  {r:[9.15,14.22,0.87,1.02], ops:[{a:11.70,b:12.50,t:'door',hinge:'start',swing:1,ang:0,groove:true}]},  // porta de serviço (hall)
  {r:[14.10,14.22,0.87,6.42], ops:[{a:3.05,b:3.60,t:'win',sill:1.40,head:2.15,mid:1.75,panels:1,frost:true},{a:4.05,b:4.75,t:'door',hinge:'end',swing:1},{a:4.98,b:5.60,t:'door',hinge:'start',swing:1}]},
  {r:[14.10,16.52,2.45,2.60]},
  {r:[16.32,16.52,2.45,5.97]},
  {r:[14.22,16.32,4.80,4.92]},
  {r:[14.22,16.52,5.82,5.97], ops:[{a:15.75,b:16.20,t:'win',sill:1.15,head:2.15,mid:1.75,panels:1,frost:true}]}, // janela do WC de serviço
  {r:[12.49,14.22,6.22,6.42], ops:[{a:12.85,b:13.95,t:'win',sill:1.10,head:2.20,mid:1.80}]},     // janela da área (H=1,10)
  {r:[12.49,12.65,3.27,6.22], ops:[{a:3.80,b:4.40,t:'win',sill:1.45,head:2.15,mid:1.80,panels:1,frost:true}]}, // janela do box do WC social (para a área)
  {r:[12.49,12.69,6.22,8.09]},
  {r:[2.55,12.69,7.89,8.09], ops:[{a:8.25,b:8.85,t:'win',sill:1.30,head:2.20,mid:1.75,panels:1,frost:true},{a:9.60,b:11.00,t:'win',sill:1.0,head:2.2,mid:1.85}]}, // fachada
  {r:[7.72,7.84,4.89,7.89], ops:[{a:4.97,b:5.62,t:'door',hinge:'start',swing:1}]},        // porta WC suíte (junto ao canto, como nas fotos)
  {r:[9.09,9.29,4.89,7.89]},
  {r:[3.75,10.34,4.77,4.89], ops:[{a:6.95,b:7.65,t:'door',hinge:'start',swing:1},{a:9.38,b:10.08,t:'door',hinge:'start',swing:1}]}, // suíte, quarto 2
  {r:[10.22,12.65,4.74,4.89]},
  {r:[10.22,10.34,3.27,4.89], ops:[{a:3.95,b:4.60,t:'door',hinge:'end',swing:1}]},      // WC social
  {r:[9.15,12.65,3.27,3.39], ops:[{a:9.38,b:10.13,t:'door',hinge:'start',swing:-1}]},    // porta cozinha
  {r:[9.15,9.30,0.87,3.87]},
  {r:[5.87,9.30,3.75,3.87], ops:[{a:8.20,b:9.15,t:'open',head:2.10}]}, // passagem sala ↔ circulação
  {r:[5.75,5.87,2.97,4.89], ops:[{a:3.97,b:4.67,t:'door',hinge:'end',swing:-1}]},       // porta quarto 1
  {r:[2.40,5.87,2.97,3.12]},
  {r:[1.15,1.30,4.22,6.39], ops:[{a:4.95,b:6.10,t:'win',sill:1.0,head:2.2,mid:1.85}]},           // janela J4
  {r:[1.15,3.87,6.27,6.39]},
  {r:[3.75,3.87,4.77,6.39]},
  {r:[2.04,2.16,0,2.97], ops:[{a:0,b:2.97,t:'pj',panels:4,open:1/4,openAt:'end',transom:2.18,top:2.50}]},     // PJ3 sala ↔ varanda
  {r:[2.60,2.72,6.39,7.89], ops:[{a:6.39,b:7.89,t:'pj',panels:2,open:1/2,openAt:'start',transom:2.12,top:2.42}]}, // PJ1 suíte ↔ varanda
];
function railPts(){ const pts=[[0.06,0],[0.06,RAIL.cy]]; for(let i=1;i<=26;i++){ const t=Math.PI+(RAIL.a0-Math.PI)*i/26; pts.push([RAIL.cx+(RAIL.R-0.06)*Math.cos(t), RAIL.cy+(RAIL.R-0.06)*Math.sin(t)]); } return pts; }

const OUTLINE = (()=>{ const o=[[0,-0.20],[10.65,-0.20],[10.65,0.87],[14.22,0.87],[14.22,2.45],[16.52,2.45],[16.52,5.97],[14.22,5.97],[14.22,6.42],[12.69,6.42],[12.69,8.09],[2.52,8.09]];
  arcPts(RAIL.cx,RAIL.cy,RAIL.R,RAIL.a0,Math.PI,28).slice(1).forEach(p=>o.push(p)); return o; })();
const ROOMS = [
  {id:'sala', name:'Sala', m2:'24,91', mat:'porcBeige', lbl:[5.7,1.55],
    floor:[[[2.10,0],[10.50,0],[10.50,0.87],[9.15,0.87],[9.15,3.75],[5.87,3.75],[5.87,2.97],[2.10,2.97]]],
    walk:{p:[8.85,0.80], look:[2.4,2.35]}, focus:[5.8,1.7]},
  {id:'varanda', name:'Varanda', m2:'12,11', mat:'deck', lbl:[1.05,2.0],
    floor:[(()=>{ const p=[[0,0],[2.10,0],[2.10,2.97]]; arcPts(Q1.cx,Q1.cy,Q1.r+0.15,Math.atan2(2.97-Q1.cy,2.10-Q1.cx)+Math.PI*2,Math.PI,10).forEach(q=>p.push(q)); p.push([1.15,6.39],[2.66,6.39],[2.66,8.09],[2.52,8.09]); arcPts(RAIL.cx,RAIL.cy,RAIL.R,RAIL.a0,Math.PI,28).slice(1).forEach(q=>p.push(q)); return p; })()],
    walk:{p:[0.72,4.05], look:[1.5,0.2]}, focus:[1.2,3.6]},
  {id:'suite', name:'Suíte', m2:'13,38', mat:'porcBeige', lbl:[5.75,6.45],
    floor:[[[3.87,4.89],[7.72,4.89],[7.72,7.89],[2.66,7.89],[2.66,6.39],[3.87,6.39]]],
    walk:{p:[7.25,7.45], look:[2.7,7.05]}, focus:[5.4,6.4]},
  {id:'wcsuite', name:'WC suíte', m2:'3,75', mat:'floorB', lbl:[8.46,6.35],
    floor:[rect(7.84,4.89,9.09,7.89)], walk:{p:[8.05,5.30], look:[8.75,7.70]}, focus:[8.46,6.4]},
  {id:'quarto1', name:'Quarto 1', m2:'11,01', mat:'porcBeige', lbl:[3.3,4.35],
    floor:[(()=>{ const p=[[Q1.cx,3.12],[5.75,3.12],[5.75,4.77],[3.75,4.77],[3.75,6.27],[1.30,6.27]]; arcPts(Q1.cx,Q1.cy,Q1.r,Math.PI,Math.PI*1.5,12).forEach(q=>p.push(q)); return p; })()],
    walk:{p:[3.10,6.08], look:[2.3,3.2]}, focus:[3.3,4.6]},
  {id:'quarto2', name:'Quarto 2', m2:'9,60', mat:'porcBeige', lbl:[10.9,6.4],
    floor:[rect(9.29,4.89,12.49,7.89)], walk:{p:[9.75,5.15], look:[10.9,7.89]}, focus:[10.9,6.4]},
  {id:'circ', name:'Circulação', m2:'4,33', mat:'porcBeige', lbl:[8.0,4.32],
    floor:[[[5.87,3.87],[8.20,3.87],[8.20,3.75],[9.15,3.75],[9.15,3.87],[9.30,3.87],[9.30,3.39],[10.22,3.39],[10.22,4.77],[5.87,4.77]]],
    walk:{p:[9.0,4.30], look:[5.6,4.32]}, focus:[8.0,4.3]},
  {id:'wcsocial', name:'WC social', m2:'2,90', mat:'floorB', lbl:[11.4,4.05],
    floor:[rect(10.34,3.39,12.49,4.74)], walk:{p:[10.62,4.25], look:[12.4,3.7]}, focus:[11.4,4.05]},
  {id:'cozinha', name:'Cozinha', m2:'10,80', mat:'floorK', lbl:[11.9,2.25],
    floor:[rect(9.30,1.02,14.10,3.27)], walk:{p:[9.95,2.42], look:[14.0,2.05]}, focus:[11.7,2.15]},
  {id:'area', name:'Área de serviço', m2:'4,27', mat:'floorK', lbl:[13.38,4.4],
    floor:[rect(12.65,3.27,14.10,6.22)], walk:{p:[13.40,3.50], look:[13.25,6.22]}, focus:[13.4,4.7]},
  {id:'qemp', name:'Quarto de serviço', m2:'4,62', mat:'floorS', lbl:[15.27,3.55],
    floor:[rect(14.22,2.60,16.32,4.80)], walk:{p:[14.60,4.40], look:[16.3,2.9]}, focus:[15.3,3.7]},
  {id:'wcserv', name:'WC de serviço', m2:'1,89', mat:'floorS', lbl:[15.27,5.37],
    floor:[rect(14.22,4.92,16.32,5.82)], walk:{p:[14.50,5.30], look:[16.3,5.4]}, focus:[15.3,5.37]},
];

const HALL=[[10.65,-1.45],[16.52,-1.45],[16.52,0.62],[14.22,0.62],[14.22,0.87],[10.65,0.87]];

/* =====================================================================
   PROPOSTA DE INTERIORES — repaginação pontual (sem quebra-quebra)
   Faces de parede: {ax:'x'|'y', c: coordenada do plano da face, a,b: trecho, n: +1/-1 (lado do cômodo)}
   ===================================================================== */
const PROP = {
  conceito: 'Contemporâneo leve, com clima de praia: base off-white, madeira clara no piso, freijó na marcenaria, pedra clara nas bancadas, inox escovado nos eletros e toques de verde-sálvia e argila.',
  laminado: { rooms:['sala','circ','suite','quarto1','quarto2'], cod:'LM-01',
    nome:'Piso laminado 8 mm, AC4, padrão carvalho natural (tom mel claro, sem fundo avermelhado)',
    regua:[1.357,0.212], hex:'#C9A57A', direcao:'x' },
  paleta: [
    {cod:'PT-01', nome:'Off-white quente', hex:'#EFEAE1', uso:'Paredes em geral (sala, circulação, quartos, quarto de serviço)', acab:'Tinta acrílica premium, fosca lavável, 2 demãos'},
    {cod:'PT-02', nome:'Branco neve', hex:'#F8F7F3', uso:'Tetos, sanca e requadros', acab:'Tinta acrílica premium fosca para teto, 2 demãos'},
    {cod:'PT-03', nome:'Verde-sálvia acinzentado', hex:'#A5AA94', uso:'Sala de estar: parede atrás do sofá', acab:'Tinta acrílica premium fosca aveludada, 2–3 demãos'},
    {cod:'PT-04', nome:'Argila (terracota clara)', hex:'#C39A7E', uso:'Jantar: arco pintado atrás do aparador', acab:'Tinta acrílica fosca; recorte com fita crepe e compasso de barbante'},
    {cod:'PT-05', nome:'Greige areia', hex:'#D3C7B7', uso:'Suíte: parede da cabeceira', acab:'Tinta acrílica premium fosca, 2 demãos'},
    {cod:'PT-06', nome:'Azul névoa', hex:'#AEBBC1', uso:'Quarto 2: parede da cabeceira', acab:'Tinta acrílica premium fosca, 2 demãos'},
  ],
  // faces pintadas com cor de destaque (o restante das paredes secas recebe PT-01)
  faces: [
    {cod:'PT-03', ax:'x', c:2.97, a:2.40, b:5.87, n:-1},
    {cod:'PT-05', ax:'x', c:7.89, a:3.87, b:7.72, n:-1},
    {cod:'PT-06', ax:'y', c:12.49, a:4.89, b:7.89, n:-1},
  ],
  arco: {cod:'PT-04', ax:'x', c:0, n:1, cx:7.40, w:1.90, h:2.25},
  materiais: [
    {cod:'LM-01', nome:'Laminado carvalho natural', hex:'#C9A57A', uso:'Piso da sala, circulação e quartos'},
    {cod:'RD-01', nome:'Rodapé branco 10 cm', hex:'#F6F5F2', uso:'Poliestireno ou MDF ultra, em todo o laminado'},
    {cod:'MD-01', nome:'Freijó (MDF amadeirado)', hex:'#B98A5C', uso:'Rack, painel ripado, aparador, nicho do café, gabinete do banheiro'},
    {cod:'MD-02', nome:'Branco fosco (MDF TX)', hex:'#F1F0EC', uso:'Armários da cozinha, puxador cava'},
    {cod:'PC-01', nome:'Porcelanato marmorizado claro', hex:'#E4DDD0', uso:'Bancadas e frontão da cozinha, bancada do banheiro'},
    {cod:'IN-01', nome:'Inox escovado', hex:'#B8BBBD', uso:'Geladeira, fogão, lava-louças, depurador, micro-ondas, cuba e torneira da cozinha'},
    {cod:'MT-01', nome:'Preto fosco', hex:'#202020', uso:'Metais do banheiro, trilho e spots, perfil do box, moldura do espelho'},
    {cod:'TX-01', nome:'Linho off-white', hex:'#E6DFD2', uso:'Sofá e cortina'},
    {cod:'PO-01', nome:'Portas existentes em mogno', hex:'#6B3520', uso:'Manter; revitalizar o verniz (lixar leve e aplicar verniz acetinado)'},
  ],
  // mobiliário, decoração e marcenaria pontual (2D + 3D)
  itens: [
    {cod:'MC-01', amb:'Sala de estar', nome:'Painel ripado em freijó', dim:'120 × 260 cm, ripas 2 × 4 cm a cada 1,5 cm', kind:'ripado', r:[3.30,0,4.50,0.035], z:[0,2.60]},
    {cod:'MC-02', amb:'Sala de estar', nome:'Rack suspenso em freijó, 2 basculantes + nicho central', dim:'180 × 40 × 30 cm, a 40 cm do piso', kind:'rack', r:[3.00,0.035,4.80,0.435], z:[0.40,0.70]},
    {cod:'E-01', amb:'Sala de estar', nome:'TV 55" no painel (suporte fixo)', dim:'123 × 71 cm, centro a 1,22 m', kind:'tv', cx:3.90, z:[0.86,1.57]},
    {cod:'M-01', amb:'Sala de estar', nome:'Sofá 3 lugares, linho off-white, braço reto e pés de madeira', dim:'230 × 95 × 80 cm', kind:'sofa', r:[2.75,2.02,5.05,2.97], back:'S'},
    {cod:'M-02', amb:'Sala de estar', nome:'Poltrona decorativa em bouclé caramelo', dim:'78 × 80 × 75 cm', kind:'armchair', cx:2.66, cy:1.15, ang:0.30},
    {cod:'M-03', amb:'Sala de estar', nome:'Mesa de centro redonda, tampo freijó', dim:'Ø 80 cm, h 38 cm', kind:'roundtable', cx:3.78, cy:1.32, rad:0.40, h:0.38, top:'freijo'},
    {cod:'M-04', amb:'Sala de estar', nome:'Mesa de centro redonda, tampo cerâmico cor travertino', dim:'Ø 55 cm, h 45 cm (conjunto ninho com M-03)', kind:'roundtable', cx:4.42, cy:1.12, rad:0.275, h:0.45, top:'travertino'},
    {cod:'M-05', amb:'Sala de estar', nome:'Mesa lateral metal preto e tampo freijó', dim:'Ø 45 cm, h 55 cm', kind:'roundtable', cx:2.47, cy:2.62, rad:0.225, h:0.55, top:'freijo', base:'metal'},
    {cod:'D-01', amb:'Sala de estar', nome:'Tapete texturizado bege (sisal sintético ou lã)', dim:'250 × 200 cm', kind:'rug', r:[2.65,0.72,5.15,2.72], color:'#D9CDBA'},
    {cod:'L-05', amb:'Sala de estar', nome:'Luminária de piso, tripé de madeira e cúpula de linho', dim:'h 155 cm, cúpula Ø 45', kind:'floorlamp', cx:5.38, cy:2.62},
    {cod:'D-02', amb:'Sala de estar', nome:'Planta grande (ave-do-paraíso ou ficus-lira) em vaso cerâmico', dim:'vaso Ø 45 cm, planta ~170 cm', kind:'plant', cx:5.45, cy:0.42, size:1.0, type:'tall'},
    {cod:'D-03', amb:'Sala de estar', nome:'Planta média (zamioculca) em vaso de fibra natural', dim:'vaso Ø 35 cm', kind:'plant', cx:2.52, cy:0.42, size:0.65, type:'bush'},
    {cod:'D-04', amb:'Sala de estar', nome:'Par de quadros abstratos em tons terrosos, moldura fina de madeira', dim:'60 × 80 cm cada, base a 1,30 m', kind:'frames', ax:'x', c:2.97, n:-1, list:[[3.18,3.78],[4.02,4.62]], z:[1.30,2.10]},
    {cod:'D-05', amb:'Sala de estar', nome:'Cortina em linho off-white, prega wave, trilho suíço embutido na sanca', dim:'largura 3,00 m × altura 2,36 m (franzido 2×)', kind:'curtain', x:2.32, a:0.02, b:2.95, open:[0.02,0.62]},
    {cod:'M-06', amb:'Jantar', nome:'Mesa de jantar redonda, tampo freijó e base central', dim:'Ø 120 cm, h 76 cm', kind:'dining', cx:7.40, cy:1.85, rad:0.60},
    {cod:'M-07', amb:'Jantar', nome:'Cadeiras em madeira com assento de palhinha (4 un.)', dim:'45 × 52 × 80 cm', kind:'chairs', cx:7.40, cy:1.85, dist:0.80, angs:[45,135,225,315]},
    {cod:'MC-03', amb:'Jantar', nome:'Aparador em freijó com pés palito', dim:'160 × 40 × 78 cm', kind:'sideboard', r:[6.60,0,8.20,0.40]},
    {cod:'D-07', amb:'Jantar', nome:'Espelho redondo com moldura fina preta', dim:'Ø 80 cm, centro a 1,55 m', kind:'roundmirror', ax:'x', c:0, n:1, cx:7.40, cz:1.55, rad:0.40},
    {cod:'L-06', amb:'Jantar', nome:'Abajur de cerâmica com cúpula de linho (sobre o aparador)', dim:'h 50 cm', kind:'tablelamp', cx:6.92, cy:0.20, z:0.78},
    {cod:'D-09', amb:'Jantar', nome:'Vaso de vidro com flores do campo (centro da mesa)', dim:'h 30 cm', kind:'flowers', cx:7.40, cy:1.85, z:0.76},
    {cod:'D-11', amb:'Jantar', nome:'Planta média (costela-de-adão) em vaso cerâmico', dim:'vaso Ø 40 cm', kind:'plant', cx:6.12, cy:3.42, size:0.85, type:'monstera'},
    {cod:'D-12', amb:'Varanda', nome:'Mesa bistrô Ø 60 + 2 cadeiras de área externa (opcional)', dim:'Ø 60 cm', kind:'bistro', cx:1.05, cy:1.45},
    {cod:'D-13', amb:'Varanda', nome:'Plantas em vasos de fibra (opcional)', dim:'Ø 35–45 cm', kind:'plant', cx:0.45, cy:0.40, size:0.8, type:'bush'},
  ],
  luminarias: [
    {cod:'L-01', nome:'Trilho eletrificado de sobrepor 2,0 m, preto, com 4 spots LED 7 W 3000 K 24°', amb:'Sala de estar', tipo:'trilho', a:[2.90,1.45], b:[4.90,1.45], qtd:1, cmd:'a', obs:'Ligado no ponto de luz existente; 2 spots voltados ao painel e 2 aos quadros'},
    {cod:'L-02', nome:'Fita LED 3000 K 9,6 W/m em perfil, na sanca existente', amb:'Sala de estar', tipo:'fita', path:[[2.62,0.05],[2.62,2.92]], qtd:'3,0 m', cmd:'b', obs:'Luz indireta sobre a cortina; driver no forro da sanca'},
    {cod:'L-03', nome:'Pendente em fibra natural Ø 50 cm, lâmpada LED 9 W 2700 K (E27)', amb:'Jantar', tipo:'pendente', x:7.40, y:1.85, qtd:1, cmd:'c', obs:'Base do pendente a 75 cm do tampo (h 1,51 m); deslocar o ponto existente até o centro da mesa'},
    {cod:'L-04', nome:'Fita LED 3000 K em perfil, sob o rack suspenso', amb:'Sala de estar', tipo:'fita', path:[[3.05,0.40],[4.75,0.40]], qtd:'1,8 m', cmd:'d', obs:'Driver atrás do rack, na tomada da TV'},
    {cod:'L-05', nome:'Luminária de piso (tomada)', amb:'Sala de estar', tipo:'piso', x:5.38, y:2.62, qtd:1, cmd:'tomada'},
    {cod:'L-06', nome:'Abajur sobre o aparador (tomada)', amb:'Jantar', tipo:'abajur', x:6.92, y:0.20, qtd:1, cmd:'tomada'},
    {cod:'L-07', nome:'Plafon LED de sobrepor Ø 20 cm, preto, 12 W 3000 K', amb:'Hall de entrada', tipo:'plafon', x:9.83, y:0.45, qtd:1, cmd:'e', obs:'Substitui o existente'},
    {cod:'L-08', nome:'Plafon LED slim de sobrepor Ø 30 cm, 24 W 3000 K', amb:'Circulação', tipo:'plafon', x:7.60, y:4.32, qtd:1, cmd:'f', obs:'Substitui o existente'},
    {cod:'L-09', nome:'Luminária linear LED de sobrepor 120 cm, branca, 36 W 3000 K', amb:'Cozinha', tipo:'linear', a:[11.10,2.15], b:[12.30,2.15], qtd:1, cmd:'g', obs:'No ponto da luminária fluorescente atual'},
    {cod:'L-10', nome:'Fita LED 3000 K em perfil de alumínio sob os aéreos e no nicho do café', amb:'Cozinha', tipo:'fita', path:[[12.60,1.40],[13.75,1.40],[13.75,2.38]], path2:[[9.36,1.32],[10.20,1.32]], qtd:'3,2 m', cmd:'h', obs:'Driver dentro do aéreo; interruptor ao lado da porta de serviço'},
    {cod:'L-11', nome:'Plafon LED de sobrepor 18 W 4000 K', amb:'Área de serviço', tipo:'plafon', x:13.38, y:4.40, qtd:1, cmd:'i', obs:'Substitui o bocal com lâmpada'},
    {cod:'L-12', nome:'Espelho com LED posterior (backlight) 3000 K', amb:'Banheiro social', tipo:'espelho', a:[10.38,3.41], b:[11.64,3.41], qtd:1, cmd:'j', obs:'Alimentação embutida atrás do espelho'},
    {cod:'L-13', nome:'Plafon LED slim de sobrepor Ø 22 cm, 18 W 3000 K', amb:'Banheiro social', tipo:'plafon', x:11.00, y:4.10, qtd:1, cmd:'k', obs:'Substitui o existente'},
  ],
  pontos: [
    {cod:'TO-01', tipo:'tomada', desc:'Geladeira — 2P+T 10 A', x:11.23, y:1.02, h:2.05},
    {cod:'TO-02', tipo:'tomada', desc:'Micro-ondas (dentro da torre) — 2P+T 10 A', x:10.53, y:1.02, h:1.75},
    {cod:'TO-03', tipo:'tomada', desc:'Lava-louças — 2P+T 10 A, circuito exclusivo', x:14.10, y:1.80, h:0.40},
    {cod:'TO-04', tipo:'tomada', desc:'Fogão (acendimento) — 2P+T 10 A (conferir existente)', x:14.10, y:2.55, h:0.30},
    {cod:'TO-05', tipo:'tomada', desc:'Depurador — 2P+T 10 A', x:14.10, y:2.80, h:2.15},
    {cod:'TO-06', tipo:'tomada', desc:'Bancada — 2× 2P+T 20 A (no frontão)', x:13.20, y:1.02, h:1.10},
    {cod:'TO-07', tipo:'tomada', desc:'Bancada da pia — 2P+T 20 A', x:14.10, y:2.25, h:1.10},
    {cod:'TO-08', tipo:'tomada', desc:'Cantinho do café — 2× 2P+T 10 A', x:9.78, y:1.02, h:1.10},
    {cod:'TO-09', tipo:'tomada', desc:'TV + HDMI/antena + driver da fita do rack (caixa 4×4)', x:3.90, y:0.00, h:0.55},
    {cod:'TO-10', tipo:'tomada', desc:'Luminária de piso — 2P+T 10 A', x:5.45, y:2.97, h:0.30},
    {cod:'TO-11', tipo:'tomada', desc:'Abajur do aparador — 2P+T 10 A', x:7.95, y:0.00, h:0.90},
    {cod:'TO-12', tipo:'tomada', desc:'Espelho com LED (alimentação embutida)', x:11.00, y:3.39, h:1.90},
    {cod:'IL-01', tipo:'luz', desc:'Ponto do pendente deslocado para o centro da mesa', x:7.40, y:1.85, h:2.60},
    {cod:'IN-01', tipo:'interruptor', desc:'Interruptor da fita dos aéreos (h 1,10)', x:12.62, y:1.02, h:1.10},
    {cod:'PH-01', tipo:'agua', desc:'Água fria p/ lava-louças: derivação com registro no gabinete da pia', x:14.10, y:1.95, h:0.40},
    {cod:'PH-02', tipo:'esgoto', desc:'Esgoto da lava-louças: sifão com entrada lateral (sem quebrar parede)', x:14.10, y:2.05, h:0.30},
    {cod:'GS-01', tipo:'gas', desc:'Gás do fogão — ponto existente, manter', x:14.10, y:2.65, h:0.45},
  ],
  // marcenaria da cozinha: wall 'N' = ao longo de x na parede y=1.02; 'E' = ao longo de y na parede x=14.10
  cozinha: [
    {id:'C1', nome:'Balcão do café, 2 portas', wall:'N', a:9.33, b:10.23, dep:0.55, z:[0.10,0.88], tipo:'base', portas:2},
    {id:'C2', nome:'Nicho em freijó com fundo ripado e 1 prateleira', wall:'N', a:9.33, b:10.23, dep:0.30, z:[1.45,2.30], tipo:'nicho', prat:[1.87]},
    {id:'C3', nome:'Torre: despensa + nicho do micro-ondas', wall:'N', a:10.23, b:10.83, dep:0.60, z:[0.10,2.40], tipo:'torre', nicho:[1.15,1.57]},
    {id:'E-02', nome:'Geladeira inox frost free inverse, ~70 cm', wall:'N', a:10.88, b:11.58, dep:0.72, z:[0,1.86], tipo:'geladeira'},
    {id:'C4', nome:'Aéreo sobre a geladeira, 2 portas', wall:'N', a:10.83, b:11.63, dep:0.60, z:[1.95,2.40], tipo:'aereo', portas:2},
    {id:'C5', nome:'Painel lateral 18 mm', wall:'N', a:11.61, b:11.63, dep:0.60, z:[0,2.40], tipo:'painel'},
    {id:'C6', nome:'Gaveteiro 3 gavetas', wall:'N', a:12.57, b:12.90, dep:0.60, z:[0.10,0.88], tipo:'gaveteiro', gavetas:3},
    {id:'E-04', nome:'Lava-louças 15 serviços inox, 60 cm (sob bancada)', wall:'N', a:12.90, b:13.50, dep:0.60, z:[0,0.85], tipo:'lavalouca'},
    {id:'C7', nome:'Canto cego com prateleira', wall:'N', a:13.50, b:14.10, dep:0.60, z:[0.10,0.88], tipo:'canto'},
    {id:'C8', nome:'Gabinete da pia, 2 portas', wall:'E', a:1.62, b:2.40, dep:0.60, z:[0.10,0.88], tipo:'base', portas:2},
    {id:'E-03', nome:'Fogão de piso 5 bocas inox, 76 cm', wall:'E', a:2.41, b:3.17, dep:0.62, z:[0,0.90], tipo:'fogao'},
    {id:'C9', nome:'Porta-temperos 10 cm', wall:'E', a:3.17, b:3.27, dep:0.60, z:[0.10,0.88], tipo:'base', portas:1},
    {id:'C10', nome:'Aéreo 2 portas', wall:'N', a:12.57, b:13.50, dep:0.35, z:[1.55,2.30], tipo:'aereo', portas:2},
    {id:'C11', nome:'Aéreo de canto, 1 porta', wall:'N', a:13.50, b:14.10, dep:0.35, z:[1.55,2.30], tipo:'aereo', portas:1},
    {id:'C12', nome:'Aéreo com escorredor embutido, 2 portas', wall:'E', a:1.37, b:2.40, dep:0.35, z:[1.55,2.30], tipo:'aereo', portas:2},
    {id:'E-05', nome:'Depurador de parede 60 cm inox', wall:'E', a:2.49, b:3.09, dep:0.48, z:[1.58,1.72], tipo:'depurador'},
    {id:'E-06', nome:'Micro-ondas 32 L inox (no nicho da torre)', wall:'N', a:10.27, b:10.79, dep:0.42, z:[1.17,1.48], tipo:'micro'},
  ],
  bancadasCozinha: [
    {nome:'Café', r:[9.33,1.02,10.23,1.59]},
    {nome:'Bancada norte', r:[12.57,1.02,14.10,1.64]},
    {nome:'Bancada da pia', r:[13.48,1.64,14.10,2.40]},
    {nome:'Arremate porta-temperos', r:[13.48,3.17,14.10,3.27]},
  ],
  frontao: [ // revestido em porcelanato sobre o azulejo existente
    {ax:'x', c:1.02, a:12.57, b:14.10, n:1, z:[0.92,1.55]},
    {ax:'y', c:14.10, a:1.02, b:3.17, n:-1, z:[0.92,1.55]},
    {ax:'x', c:1.02, a:9.33, b:10.23, n:1, z:[0.92,1.45]},
  ],
  cubaCozinha: {cx:13.79, cy:2.01, w:0.56, d:0.34},
  banheiro: {
    gabinete:{r:[10.40,3.39,11.60,3.84], z:[0.36,0.74], cod:'MC-05', nome:'Gabinete suspenso em freijó, 2 gavetas, puxador cava', dim:'120 × 45 × 38 cm'},
    bancada:{r:[10.34,3.39,11.64,3.86], z:[0.74,0.78], saia:0.10, cod:'B-04', nome:'Bancada em porcelanato marmorizado claro com saia de 10 cm', dim:'130 × 47 cm'},
    cuba:{cx:11.00, cy:3.63, w:0.50, d:0.35, h:0.13, cod:'B-05', nome:'Cuba de apoio oval, louça branca fosca', dim:'50 × 35 × 13 cm'},
    torneira:{cx:11.00, cy:3.43, cod:'B-06', nome:'Misturador monocomando de mesa, bica alta, preto fosco', dim:'h ~ 30 cm'},
    espelho:{a:10.36, b:11.66, z:[0.95,2.40], cod:'D-14', nome:'Espelho inteiro de parede a parede com LED posterior', dim:'130 × 145 cm, afastado 2 cm da parede'},
    box:{x:11.70, a:3.40, b:4.73, cod:'B-07', nome:'Box em vidro temperado 8 mm incolor, perfil preto fosco, porta de correr (opcional)', dim:'133 × 190 cm'},
    acessorios:{cod:'B-08', nome:'Kit de acessórios preto fosco: toalheiro de argola, porta-papel, cabide', dim:'—'},
  },
};
