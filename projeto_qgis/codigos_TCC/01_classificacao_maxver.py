"""
Apêndice A - Classificação supervisionada por Máxima Verossimilhança (Eq. 3.1)

Entradas : imagem multibanda CBERS-4A (B1-B4) em SIRGAS 2000 / UTM 23S (EPSG:31983)
           ROIs (GPKG) com o campo do código da classe (1 a 4)
Saída    : GeoTIFF (LZW) com o mapa temático; 0 = sem dado
Equação  : g_i(x) = -ln|S_i| - (x - m_i)^T S_i^-1 (x - m_i), prioris iguais, sem limiar de rejeição
Requer   : Python 3, NumPy, GDAL (osgeo)
"""
import numpy as np
from osgeo import gdal, ogr, osr

# ======================== CONFIGURAÇÃO ========================
IMAGEM = r"C:\Users\Sabrina\Desktop\06_10_2026\cbers_20251027_B1234_31983.tif"
ROIS = r"C:\Users\Sabrina\Desktop\06_10_2026\rois_copia.gpkg"
CAMPO_CLASSE = "macroclass_id"   # campo das ROIs com o código da classe (1 a 4)
SAIDA = r"C:\Users\Sabrina\Desktop\06_10_2026\classificacao_maxver_cbers_20251027.tif"
NODATA = 0
NOMES = {1: "Vegetação", 2: "Área Urbana", 3: "Solo Exposto", 4: "Pastagem"}
# ==============================================================


def estatisticas_das_classes(img, rotulos, classes):
    """Vetor de médias, inversa da covariância e ln|covariância| de cada classe."""
    estat = {}
    for c in classes:
        amostras = img[:, rotulos == c].T            # (n_pixels, n_bandas)
        media = amostras.mean(axis=0)
        cov = np.cov(amostras, rowvar=False)
        sinal, logdet = np.linalg.slogdet(cov)
        if sinal <= 0:
            raise ValueError(f"Covariância inválida na classe {c}: amostras insuficientes ou repetidas.")
        estat[c] = (media, np.linalg.inv(cov), logdet, amostras.shape[0])
    return estat


def classificar_maxver(img, estat, valido):
    """Aplica a função discriminante (Eq. 3.1) a todos os pixels válidos e devolve o mapa."""
    pixels = img[:, valido].T                         # (n_pixels, n_bandas)
    classes = sorted(estat)
    g = np.empty((pixels.shape[0], len(classes)))
    for k, c in enumerate(classes):
        media, cov_inv, logdet, _ = estat[c]
        d = pixels - media
        mahalanobis = np.einsum("ij,jk,ik->i", d, cov_inv, d)
        g[:, k] = -logdet - mahalanobis
    mapa = np.zeros(valido.shape, dtype=np.uint8)     # 0 = sem dado
    mapa[valido] = np.array(classes, dtype=np.uint8)[np.argmax(g, axis=1)]
    return mapa


def main():
    # ---- 1. imagem ----
    ds = gdal.Open(IMAGEM)
    if ds is None:
        raise FileNotFoundError(f"Não foi possível abrir a imagem: {IMAGEM}")
    img = ds.ReadAsArray().astype(np.float64)         # (bandas, linhas, colunas)
    if img.ndim != 3 or img.shape[0] != 4:
        raise ValueError("A imagem deve ter exatamente 4 bandas (B1, B2, B3, B4).")
    valido = ~np.all(img == NODATA, axis=0)           # pixels dentro do perímetro
    gt, proj = ds.GetGeoTransform(), ds.GetProjection()
    linhas, colunas = ds.RasterYSize, ds.RasterXSize
    print(f"Imagem: {colunas} x {linhas} pixels, {valido.sum():,} pixels válidos".replace(",", "."))

    # ---- 2. ROIs -> grade da imagem ----
    vs = ogr.Open(ROIS)
    if vs is None:
        raise FileNotFoundError(f"Não foi possível abrir as ROIs: {ROIS}")
    camada = vs.GetLayer(0)
    campos = [camada.GetLayerDefn().GetFieldDefn(i).GetName() for i in range(camada.GetLayerDefn().GetFieldCount())]
    if CAMPO_CLASSE not in campos:
        raise KeyError(f"Campo '{CAMPO_CLASSE}' não encontrado nas ROIs. Campos disponíveis: {campos}")
    srs_img = osr.SpatialReference(wkt=proj)
    srs_roi = camada.GetSpatialRef()
    if srs_roi is not None and not srs_img.IsSame(srs_roi):
        print("ATENÇÃO: as ROIs e a imagem estão em sistemas de coordenadas diferentes. "
              "Reprojete as ROIs para EPSG:31983 antes de rodar.")
    mem = gdal.GetDriverByName("MEM").Create("", colunas, linhas, 1, gdal.GDT_Byte)
    mem.SetGeoTransform(gt)
    mem.SetProjection(proj)
    gdal.RasterizeLayer(mem, [1], camada, options=[f"ATTRIBUTE={CAMPO_CLASSE}"])
    rotulos = mem.ReadAsArray()
    rotulos[~valido] = 0

    classes = [c for c in sorted(NOMES) if np.any(rotulos == c)]
    print("\nPixels de treinamento por classe:")
    for c in classes:
        print(f"  {c} {NOMES[c]:<13} {int((rotulos == c).sum()):>7} pixels")
    print(f"  Total              {int((rotulos > 0).sum()):>7} pixels")

    # ---- 3 e 4. estatísticas e classificação ----
    estat = estatisticas_das_classes(img, rotulos, classes)
    mapa = classificar_maxver(img, estat, valido)

    # ---- 5. salvar e resumir ----
    out = gdal.GetDriverByName("GTiff").Create(SAIDA, colunas, linhas, 1, gdal.GDT_Byte, options=["COMPRESS=LZW"])
    out.SetGeoTransform(gt)
    out.SetProjection(proj)
    banda = out.GetRasterBand(1)
    banda.WriteArray(mapa)
    banda.SetNoDataValue(NODATA)
    banda.FlushCache()
    out = None

    area_pixel = abs(gt[1] * gt[5])                   # 8 m x 8 m = 64 m²
    total = int((mapa > 0).sum())
    print(f"\nMapa salvo em: {SAIDA}\n")
    print(f"{'Classe':<16}{'Pixels':>10}{'Área (km²)':>12}{'%':>8}")
    for c in classes:
        n = int((mapa == c).sum())
        print(f"{c} {NOMES[c]:<14}{n:>10}{n * area_pixel / 1e6:>12.3f}{100 * n / total:>8.1f}")
    print(f"{'Total':<16}{total:>10}{total * area_pixel / 1e6:>12.3f}{100.0:>8.1f}")


if __name__ == "__main__":
    main()
