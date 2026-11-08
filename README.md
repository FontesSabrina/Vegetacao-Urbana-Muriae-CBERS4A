[README.md](https://github.com/user-attachments/files/34554343/README.md)
# Vegetação urbana de Muriaé-MG com CBERS-4A

Trabalho de Conclusão de Curso (TCC) em **Gestão da Tecnologia da Informação** (IF Sudeste MG – Campus Muriaé)
sobre a **classificação da cobertura vegetal do perímetro urbano de Muriaé-MG** e o cálculo do
**Índice de Distribuição de Vegetação Urbana (IDVU)**, que mede a área verde por habitante (m²/hab).

Texto completo do TCC: [`documento/TCC_Muriae_CBERS4A.pdf`](documento/TCC_Muriae_CBERS4A.pdf)

## Visão geral

- Imagem **CBERS-4A / WPM** de 27/10/2025, resolução de 8 m (bandas 1–4), em **SIRGAS 2000 / UTM 23S** (EPSG:31983).
- Classificação supervisionada por **Máxima Verossimilhança** (Python/NumPy) em quatro classes:
  Vegetação, Área Urbana, Solo Exposto e Pastagem. Os corpos d'água entram como quinta classe, por máscara vetorial.
- **Validação independente** com 200 pontos estratificados (AcATaMa) e estimador de **Olofsson et al. (2014)**:
  acurácias, áreas ajustadas e intervalos de confiança de 95%.
- **IDVU** do perímetro urbano e da área urbanizada densa (IBGE), com população por setor censitário
  (Censo 2022) distribuída pelo **método dasimétrico**.

## Resultados principais

| Indicador | Valor |
|---|---|
| Acurácia global (4 classes) | 80,61% (±5,25%) |
| Kappa | 0,727 |
| Acurácia global (2 classes, comparável à etapa anterior) | 89,78% (±4,2%) |
| IDVU do perímetro (mapa / área ajustada) | 59,62 / 89,90 m²/hab |
| IDVU da área urbanizada densa (mapa / ajustado) | 14,84 / 24,82 m²/hab |

Referência: a Organização Mundial da Saúde (OMS) indica 12 m²/hab como mínimo e 36 m²/hab como ideal. Os detalhes, as tabelas e as
limitações estão no texto do TCC.

## Estrutura do repositório

```
tcc-vegetacao-muriae/
├── README.md
├── documento/
│   ├── TCC_Muriae_CBERS4A.pdf            TCC completo
│   └── 3_Metodologia.docx                Capítulo 3 (versão preliminar)
└── projeto_qgis/                         Projeto do QGIS e dados
    ├── Nova_Classificação_06-10-2026.qgz Projeto do QGIS
    ├── codigos_TCC/                      Scripts Python de cada etapa
    │   ├── 01_classificacao_maxver.py
    │   ├── 02_mascara_agua.py
    │   ├── 03_acuracia_olofsson.py
    │   └── 04_idvu.py
    ├── 2025-10-27/recorte/               Bandas da cena CBERS-4A recortadas
    ├── cbers_20251027_B1234_31983.tif    Imagem CBERS-4A (bandas 1–4)
    ├── treino_cbers_20251027_corrigido.scpx   Amostras de treinamento (SCP/QGIS)
    ├── pontos_validacao_4classes.gpkg    Pontos de validação
    ├── perimetro_urbano_limpo_corrigido.gpkg  Perímetro urbano
    ├── muriae_areas_densas.*             Área urbanizada densa (IBGE)
    ├── MG_setores_CD2022.gpkg            Setores censitários de MG (IBGE)
    ├── Agregados_por_setores_basico_BR_…/ Dados do Censo 2022 (IBGE)
    ├── mapas/                            Mapas gerados (PNG)
    └── csv/                              Tabelas exportadas por classe
```

## Ferramentas utilizadas

- **QGIS** com os plugins **Semi-Automatic Classification Plugin (SCP)** e **AcATaMa**
- **Python 3** com **GDAL/OGR**, **NumPy** e **pandas**

## Fontes dos dados

- Imagem **CBERS-4A / WPM**: Catálogo de Imagens do **INPE**
- Perímetro urbano: **IEDE-MG** (Infraestrutura Estadual de Dados Espaciais de Minas Gerais)
- Setores censitários, agregados por setor e Áreas Urbanizadas: **IBGE**, Censo Demográfico 2022

## Obtenção dos arquivos

Os arquivos grandes (`.tif`, `.gpkg` e o CSV do IBGE) ficam no **Git LFS**. Para baixar tudo:

```bash
git lfs install
git clone https://github.com/FontesSabrina/tcc-vegetacao-muriae.git
```

O botão **Code → Download ZIP** **não** traz os arquivos do LFS (só "ponteiros"); use o `git clone`.
Depois, abra `projeto_qgis/Nova_Classificação_06-10-2026.qgz` no QGIS.

## Autoria e vínculo institucional

- **Sabrina Caetano Fontes**
- **Lucas Faria Schuenck de Souza**
- Orientador: **Prof. Marcus Vinícius Souza Costa**

Instituto Federal do Sudeste de Minas Gerais – Campus Muriaé · Gestão da Tecnologia da Informação · 2026.
