# Apartamento 02 em Blender (script Python)

O apartamento é modelado do zero no Blender por `apto_build.py`, com as mesmas medidas de `../dados.js` (paredes, aberturas, cômodos, marcenaria e mobiliário da proposta). As imagens saem do Cycles com luz natural: céu HDRI e sol entrando pelas janelas.

## Imagens (`renders/`)

| Arquivo | Vista (câmera a 1,60 m do piso) |
|---|---|
| `sala.png` | Primeira proposta (substituída pelas opções de `sala-opcoes/`) |
| `cozinha-pia.png` | Cozinha vista da área de serviço: pia, fogão, lava-louças e geladeira |
| `cozinha-cafe.png` | Canto do café: nicho ripado em freijó, torre do micro-ondas e geladeira |
| `quarto.png` | Suíte: cama, cabeceira, criados-mudos e recanto de leitura junto à porta de correr |

1920 × 1080, Cycles, 128 amostras adaptativas, redução de ruído OpenImageDenoise, AgX.

## Sala: 4 opções (ajuste de 18/11)

Em `renders/sala-opcoes/`. Nas quatro: sofá retrátil de 2,86 m sem mesa de centro, tapete de juta, manta de tricô terracota, rack suspenso de 2,94 m com LED, nichos com LED, TV 65", cortinas de voal até o teto, mesa lateral com abajur e luminária de piso. Não há móvel no caminho da entrada; na parede do jantar ficam só dois quadros. Rodapés e batentes estão em mogno escuro/imbuia avermelhada, como os existentes.

| Opção | Parede da TV | Mesa (6 lugares) |
|---|---|---|
| `sala_A-redonda.png` | Neutra (off-white PT-01) com painel ripado de freijó atrás da TV | Redonda Ø 140 cm |
| `sala_A-retangular.png` | Neutra (off-white PT-01) com painel ripado de freijó atrás da TV | Retangular 180 × 95 cm |
| `sala_B-redonda.png` | Verde-oliva acinzentado (#767B65), TV direto na parede | Redonda Ø 140 cm |
| `sala_B-retangular.png` | Verde-oliva acinzentado (#767B65), TV direto na parede | Retangular 180 × 95 cm |

`estar_A-redonda.png` e `estar_B-redonda.png` mostram o estar de perto nas duas cores de parede; a mesa não aparece nessa vista. Para gerar uma opção: `blender -b --python apto_build.py -- sala,estar 128 1920 1080 renders/sala-opcoes --opcao B-retangular`.

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
- Texturas: laminado (`laminate_floor_02`), freijó (`oak_veneer_01`), madeira da mesa (`teak_veneer`), portas em mogno (`sapele_veneer`), linho (`rough_linen`), tapete, manta e bouclé (`poly_wool_herringbone`), travertino (`marble_01`), relevo da pintura (`painted_plaster_wall`), juta do tapete da sala (`hessian_230`), tricô da manta (`knitted_fleece`), bouclé das cadeiras e almofadas (`curly_teddy_natural`) e veludo cotelê oliva (`ribbed_corduroy`).
- Móveis e objetos:
  - Criados-mudos da suíte (`side_table_01`)
  - Na primeira versão da sala: poltrona (`modern_arm_chair_01`) e mesa de centro (`coffee_table_round_01`), retiradas no ajuste
  - Poltrona de leitura da suíte (`mid_century_lounge_chair`)
  - Pendentes de vidro da suíte (`modern_ceiling_lamp_01`)
  - Conjunto bistrô da varanda (`outdoor_table_chair_set_01`)
  - Plantas (`potted_plant_01/02/04`)
  - Almofadas (`throw_pillows_01`)
  - Molduras dos quadros (`hanging_picture_frame_01/02`)
  - Vasos, livros, concha, fruteira, cesto, jarra e bule

## O que é modelado no script

- **Arquitetura:** paredes com portas, janelas e portas de correr, unidas numa malha só. As cores de pintura vão por face, conforme o cômodo; na opção B, a parede da TV recebe o verde-oliva. Também entram pisos, lajes, sanca, rodapés, peitoris, guarda-corpo curvo e corrimão.
- **Sala (versão de 18/11):** sofá retrátil e reclinável de 3 módulos em linho, almofadas, manta de tricô, tapete de juta, rack suspenso, painel e coluna ripados, nichos com LED, TV 65", mesa de 6 lugares (redonda ou retangular), cadeiras estofadas em bouclé, pendentes em cúpula verde-oliva, trilho com spots, luminária de piso, mesa lateral com abajur e cortinas de voal.
- **Cozinha:** todos os módulos C1 a C12 com as medidas do projeto, puxador cava, bancadas e frontão em porcelanato marmorizado, cuba com recorte e misturador. Os eletros são em inox escovado: geladeira, fogão, lava-louças, depurador e micro-ondas. Há fita LED sob os aéreos.
- **Suíte:** cama queen com cabeceira estofada e painel em freijó, roupa de cama, manta, tapete e cortina.

Os modelos do Poly Haven só têm sofá, cadeiras e cama em estilo clássico/chesterfield. Por isso esses móveis seguem a especificação do projeto e são modelados aqui, com tecidos e madeiras do Poly Haven.

## Luz

- O céu vem do HDRI. O disco do sol do HDRI é recortado e substituído por uma lâmpada solar de 4,2 W/m², valor medido no próprio HDRI. O sol está a oeste-sudoeste, a 21° de altura: luz de fim de tarde entrando pela porta-janela da sala e pela porta de correr da suíte.
- Portais de luz nas aberturas ajudam o Cycles a amostrar o céu.
- Na cozinha, a fita LED sob os aéreos e a luminária linear ficam acesas. Na sala, as luzes de apoio (LED do rack, nichos e sanca, abajur, luminária de piso e pendentes) ficam acesas baixas, para o clima aconchegante das referências. Na suíte, só entra a luz natural.
