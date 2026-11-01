# 🌳 Vegetação urbana de Muriaé-MG com CBERS-4A

![Status](https://img.shields.io/badge/status-em%20andamento-orange)
![QGIS](https://img.shields.io/badge/QGIS-SCP%20%2B%20AcATaMa-589632?logo=qgis&logoColor=white)
![Python](https://img.shields.io/badge/Python-GDAL%20%2F%20NumPy-3776AB?logo=python&logoColor=white)

Trabalho de Conclusão de Curso (TCC) do curso de **Gestão da Tecnologia da Informação**.

Classificação supervisionada da cobertura do solo no perímetro urbano de **Muriaé-MG** a partir de uma
imagem do satélite **CBERS-4A (câmera WPM, 27/10/2025)**, com validação da acurácia e cálculo do
**Índice de Distribuição de Vegetação Urbana (IDVU)**, que mede a área verde por habitante.

> ⚠️ **Trabalho em andamento.** Por enquanto só a **Metodologia** está escrita. As outras partes do
> texto serão adicionadas aqui conforme forem ficando prontas.

---

## 📑 Metodologia (resumo)

O estudo segue sete etapas:

1. Delimitação e caracterização da área de estudo (perímetro urbano de 27,09 km², IEDE-MG)
2. Aquisição e pré-processamento da imagem CBERS-4A / WPM (órbita/ponto 198/140)
3. Definição das classes temáticas e coleta de amostras de treinamento
4. Classificação supervisionada por **Máxima Verossimilhança**
5. Incorporação dos corpos d'água a partir de base vetorial oficial
6. Validação da acurácia e estimativa de áreas (método de Olofsson)
7. Cálculo do **IDVU** com população estimada por método dasimétrico (setores censitários IBGE 2022)

Sistema de referência: **SIRGAS 2000 / UTM fuso 23S**.

O texto completo está em [`documento/3_Metodologia.docx`](documento/3_Metodologia.docx).

## 📂 Estrutura do repositório

```
tcc-vegetacao-muriae/
├── documento/
│   └── 3_Metodologia.docx                 Capítulo 3 do TCC
└── projeto_qgis/                          Projeto completo do QGIS (mesma estrutura do original)
    ├── Nova_Classificação_06-10-2026.qgz  Projeto do QGIS
    ├── codigos_TCC/                       Scripts Python de cada etapa
    │   ├── 01_classificacao_maxver.py
    │   ├── 02_mascara_agua.py
    │   ├── 03_acuracia_olofsson.py
    │   └── 04_idvu.py
    ├── 2025-10-27/recorte/                Bandas da cena CBERS-4A recortadas
    ├── mapas/                             Mapas gerados (PNG)
    ├── csv/                               Tabelas exportadas por classe
    ├── Agregados_por_setores_basico_BR_…/ Dados do Censo 2022 (IBGE)
    ├── MG_setores_CD2022.gpkg             Setores censitários de MG (IBGE)
    └── …                                  Amostras, validação, classificações e estilos (.qml)
```

## 🛠️ Ferramentas

- **QGIS** com os plugins **Semi-Automatic Classification Plugin (SCP)** e **AcATaMa**
- **Python 3** com **GDAL/OGR** e **NumPy** (scripts em `projeto_qgis/codigos_TCC`)

## 🗂️ Fontes dos dados

- Imagem **CBERS-4A / WPM**: Catálogo de Imagens do **INPE**
- Perímetro urbano: **IEDE-MG** (Infraestrutura Estadual de Dados Espaciais de Minas Gerais)
- Setores censitários e agregados por setor: **IBGE**, Censo Demográfico 2022

## 💾 Como baixar o projeto

Os arquivos grandes (imagens `.tif`, camadas `.gpkg` e o CSV do IBGE) ficam no **Git LFS**.
Para baixar tudo:

```bash
git lfs install
git clone https://github.com/FontesSabrina/tcc-vegetacao-muriae.git
```

Depois é só abrir `projeto_qgis/Nova_Classificação_06-10-2026.qgz` no QGIS.

> O botão **Code → Download ZIP** do GitHub **não** traz os arquivos do LFS (eles vêm só como
> "ponteiros"). Use o `git clone` acima.

## 👩‍💻 Autoria

**Sabrina Caetano Fontes**, Gestão da Tecnologia da Informação.
