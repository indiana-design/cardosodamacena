# Apartamento 02 em Blender (script Python)

O apartamento é modelado do zero no Blender por `apto_build.py`, com as mesmas medidas de `../dados.js` (paredes, aberturas, cômodos, marcenaria e mobiliário da proposta). As imagens saem do Cycles com luz natural: céu HDRI e sol entrando pelas janelas.

## Imagens (`renders/`)

| Arquivo | Vista (câmera a 1,60 m do piso) |
|---|---|
| `sala.png` | Jantar em primeiro plano, estar e varanda ao fundo |
| `cozinha-pia.png` | Cozinha vista da área de serviço: pia, fogão, lava-louças e geladeira |
| `cozinha-cafe.png` | Canto do café: nicho ripado em freijó, torre do micro-ondas e geladeira |
| `quarto.png` | Suíte: cama, cabeceira, criados-mudos e recanto de leitura junto à porta de correr |

1920 × 1080, Cycles, 128 amostras adaptativas, redução de ruído OpenImageDenoise, AgX.

## Como gerar de novo

Testado com o Blender 5.3.0 (Linux). Precisa também de Node.js e de Python 3 com Pillow.

```bash
python3 baixar_polyhaven.py                 # baixa os assets CC0 para ./polyhaven (~200 MB)
python3 artes.py artes                      # gera as 3 artes abstratas dos quadros
node dados_para_json.js ../dados.js dados.json
blender -b --python apto_build.py -- sala,cozinha-pia,cozinha-cafe,quarto 128 1920 1080 renders --save apartamento02.blend
```

Para testar rápido, use poucas amostras e resolução baixa (por exemplo `32 960 540`). A vista extra `planta` faz uma vista de cima sem o teto, útil para conferir o layout. O `.blend` salvo abre no Blender com a cena inteira e as quatro câmeras.

## O que vem do Poly Haven (CC0)

- Céu: HDRI `kloofendal_48d_partly_cloudy_puresky`, com céu, nuvens e um horizonte que lembra o mar.
- Texturas: laminado (`laminate_floor_02`), freijó (`oak_veneer_01`), madeira da mesa (`teak_veneer`), portas em mogno (`sapele_veneer`), linho (`rough_linen`), tapete, manta e bouclé (`poly_wool_herringbone`), travertino (`marble_01`) e o relevo da pintura (`painted_plaster_wall`).
- Móveis e objetos:
  - Poltrona da sala, com assento retexturizado em bouclé caramelo (`modern_arm_chair_01`)
  - Mesa de centro de mármore (`coffee_table_round_01`)
  - Mesa lateral e criados-mudos (`side_table_01`)
  - Poltrona de leitura da suíte (`mid_century_lounge_chair`)
  - Pendentes de vidro da suíte (`modern_ceiling_lamp_01`)
  - Conjunto bistrô da varanda (`outdoor_table_chair_set_01`)
  - Plantas (`potted_plant_01/02/04`)
  - Almofadas (`throw_pillows_01`)
  - Molduras dos quadros (`hanging_picture_frame_01/02`)
  - Vasos, livros, concha, fruteira, cesto, jarra e bule

## O que é modelado no script

- **Arquitetura:** paredes com portas, janelas e portas de correr, unidas numa malha só. As cores de pintura vão por face, conforme o cômodo (PT-01 a PT-06), e o arco pintado é o PT-04. Também entram pisos, lajes, sanca, rodapés, peitoris, guarda-corpo curvo e corrimão.
- **Sala:** painel ripado, rack, TV e sofá de 2,30 m em linho. Também a mesa de jantar Ø 120 e as cadeiras com palhinha, o aparador com palhinha, o espelho redondo, o pendente de fibra, o trilho com spots, a luminária de piso, o abajur e a cortina wave.
- **Cozinha:** todos os módulos C1 a C12 com as medidas do projeto, puxador cava, bancadas e frontão em porcelanato marmorizado, cuba com recorte e misturador. Os eletros são em inox escovado: geladeira, fogão, lava-louças, depurador e micro-ondas. Há fita LED sob os aéreos.
- **Suíte:** cama queen com cabeceira estofada e painel em freijó, roupa de cama, manta, tapete e cortina.

Os modelos do Poly Haven só têm sofá, cadeiras e cama em estilo clássico/chesterfield. Por isso esses móveis seguem a especificação do projeto e são modelados aqui, com tecidos e madeiras do Poly Haven.

## Luz

- O céu vem do HDRI. O disco do sol do HDRI é recortado e substituído por uma lâmpada solar de 4,2 W/m², valor medido no próprio HDRI. O sol está a oeste-sudoeste, a 21° de altura: luz de fim de tarde entrando pela porta-janela da sala e pela porta de correr da suíte.
- Portais de luz nas aberturas ajudam o Cycles a amostrar o céu.
- Na cozinha, a fita LED sob os aéreos e a luminária linear ficam acesas. Nos outros ambientes só entra a luz natural.
