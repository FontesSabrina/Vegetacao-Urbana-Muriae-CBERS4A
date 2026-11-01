"""
Avaliação da acurácia e estimativa de áreas (Seção 3.6; Eq. 3.2 a 3.5)

Estimador estratificado de Olofsson et al. (2014) + Kappa (Congalton, 1991),
com intervalos de confiança de 95 %.

Entradas
  - CSV dos pontos (separador ';' ou ','), com duas colunas de códigos inteiros:
        mapa : classe do mapa no ponto (define o estrato i)
        ref  : classe de referência rotulada por fotointerpretação (j)
  - mapa final de 8 m (GeoTIFF) para contar os pixels de cada estrato (-> W_i e A_tot)
Esquemas de agrupamento (opcional): dicionário {classe_original: grupo}. O agrupamento
é aplicado ao mapa e à referência, mas os estratos originais do sorteio são preservados.
Requer: Python 3, NumPy, pandas, GDAL (apenas para contar pixels)
"""
import numpy as np
import pandas as pd

# ======================== CONFIGURAÇÃO ========================
CSV_PONTOS = r"C:\Users\Sabrina\Desktop\06_10_2026\pontos_validacao.csv"
MAPA_FINAL = r"C:\Users\Sabrina\Desktop\06_10_2026\mapa_final_5classes.tif"
CLASSES = {1: "Vegetação", 2: "Área Urbana", 3: "Solo Exposto", 4: "Pastagem"}  # a água (5) fica fora
# Esquemas de agrupamento (None = 4 classes originais)
ESQUEMAS = {
    "4 classes": None,
    "2 classes (Vegetação | Adensamento Urbano/Solo Exposto)": {1: 1, 2: 2, 3: 2, 4: 2},
}
Z = 1.96   # 95 %
# ==============================================================


def contar_pixels(caminho, classes):
    from osgeo import gdal
    ds = gdal.Open(caminho)
    arr = ds.GetRasterBand(1).ReadAsArray()
    gt = ds.GetGeoTransform()
    return {c: int((arr == c).sum()) for c in classes}, abs(gt[1] * gt[5])


def _razao(y, x, estrato, W, n):
    """Estimativa e erro-padrão da razão R = sum_i W_i*ybar_i / sum_i W_i*xbar_i
    (estimador estratificado de razão; reduz às fórmulas de Olofsson et al. 2014)."""
    Y = sum(W[i] * y[estrato == i].mean() for i in W)
    X = sum(W[i] * x[estrato == i].mean() for i in W)
    if X == 0:
        return np.nan, np.nan
    R = Y / X
    var = 0.0
    for i in W:
        yi, xi = y[estrato == i], x[estrato == i]
        ni = n[i]
        if ni < 2:
            continue
        syy, sxx = yi.var(ddof=1), xi.var(ddof=1)
        sxy = np.cov(yi, xi, ddof=1)[0, 1] if (syy > 0 and sxx > 0) else 0.0
        var += W[i] ** 2 * (syy + R ** 2 * sxx - 2 * R * sxy) / ni
    return R, np.sqrt(var) / X


def avaliar(pontos, W, A_tot, grupo=None, nomes=None):
    """pontos: DataFrame com colunas mapa/ref. W: {estrato: proporção de área}. A_tot em km²."""
    p = pontos.copy()
    if grupo:
        p["gm"], p["gr"] = p["mapa"].map(grupo), p["ref"].map(grupo)
    else:
        p["gm"], p["gr"] = p["mapa"], p["ref"]
    estrato = p["mapa"].to_numpy()
    n = {i: int((estrato == i).sum()) for i in W}
    gm, gr = p["gm"].to_numpy(), p["gr"].to_numpy()
    grupos = sorted(set(gm) | set(gr))

    # Eq. 3.2: p_ij = W_i * n_ij / n_i+   (linhas = grupo do mapa, colunas = referência)
    P = pd.DataFrame(0.0, index=grupos, columns=grupos)
    for i in W:
        sel = estrato == i
        for g_m, g_r in zip(gm[sel], gr[sel]):
            P.loc[g_m, g_r] += W[i] / n[i]

    # Eq. 3.3: acurácia global (indicador de acerto, estratificado por i)
    acerto = (gm == gr).astype(float)
    O, se_O = _razao(acerto, np.ones_like(acerto), estrato, W, n)

    linhas = []
    for g in grupos:
        y = ((gm == g) & (gr == g)).astype(float)
        U, se_U = _razao(y, (gm == g).astype(float), estrato, W, n)      # acurácia do usuário
        Pj, se_P = _razao(y, (gr == g).astype(float), estrato, W, n)     # acurácia do produtor
        # Eq. 3.4: área ajustada = A_tot * p_+j
        pj, se_pj = _razao((gr == g).astype(float), np.ones_like(acerto), estrato, W, n)
        linhas.append({
            "classe": (nomes or {}).get(g, g),
            "área mapa (km²)": A_tot * P.loc[g].sum(),
            "área ajustada (km²)": A_tot * pj, "IC95 ± (km²)": Z * A_tot * se_pj,
            "usuário (%)": 100 * U, "±U": 100 * Z * se_U,
            "produtor (%)": 100 * Pj, "±P": 100 * Z * se_P,
        })

    # Eq. 3.5: Kappa a partir da matriz de proporções de área
    pe = float((P.sum(axis=1) * P.sum(axis=0)).sum())     # soma de p_j+ * p_+j
    kappa = (O - pe) / (1 - pe)
    return O, se_O, kappa, pd.DataFrame(linhas), P


def main():
    pontos = pd.read_csv(CSV_PONTOS, sep=None, engine="python")
    pontos = pontos[pontos["mapa"].isin(CLASSES) & pontos["ref"].isin(CLASSES)]   # descarta pontos sobre a água
    print(f"Pontos válidos: {len(pontos)}")
    pix, area_pixel = contar_pixels(MAPA_FINAL, list(CLASSES))
    total = sum(pix.values())
    W = {c: pix[c] / total for c in CLASSES}
    A_tot = total * area_pixel / 1e6
    print(f"Área total mapeada (sem água): {A_tot:.3f} km²")

    for nome, grupo in ESQUEMAS.items():
        nomes = CLASSES if grupo is None else None
        O, se, k, tab, P = avaliar(pontos, W, A_tot, grupo, nomes)
        print(f"\n=== {nome} ===")
        print(f"Acurácia global: {100 * O:.2f} % (IC95 ± {100 * Z * se:.2f})   Kappa: {k:.4f}")
        print(tab.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
