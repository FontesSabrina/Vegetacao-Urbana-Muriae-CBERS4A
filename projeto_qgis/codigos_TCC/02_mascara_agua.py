"""
Incorporação dos corpos d'água ao mapa de 8 m (Seção 3.5)

Regra: cada pixel de 8 m com MAIS DE 50 % de área ocupada por água é rotulado
como Corpos d'água (código 5), sobrepondo-se ao resultado do classificador.

Entradas : mapa classificado de 8 m (saída do script 01)
           mapa de 2,9 m do estudo anterior (Classificacao_Final_ComAgua.tif), onde a classe 4 = água
Saída    : GeoTIFF de 8 m com 5 classes
Requer   : Python 3, NumPy, GDAL
"""
import numpy as np
from osgeo import gdal

# ======================== CONFIGURAÇÃO ========================
MAPA_8M = r"C:\Users\Sabrina\Desktop\06_10_2026\classificacao_maxver_cbers_20251027.tif"
MAPA_ANTIGO = r"C:\Users\Sabrina\Desktop\Classificacao_Final_ComAgua.tif"
CLASSE_AGUA_ANTIGO = 4          # código da água no mapa antigo
CLASSE_AGUA_NOVO = 5            # código da água no mapa final
LIMIAR = 0.5                    # fração mínima do pixel ocupada por água (> 50 %)
SAIDA = r"C:\Users\Sabrina\Desktop\06_10_2026\mapa_final_5classes.tif"
# ==============================================================


def fracao_de_agua(ds_antigo, ds_8m, codigo_agua):
    """Reamostra a máscara binária (0/1) de 2,9 m para a grade de 8 m pela MÉDIA:
    o valor de cada pixel de 8 m é a fração da sua área ocupada por água."""
    antigo = ds_antigo.GetRasterBand(1).ReadAsArray()
    binario = (antigo == codigo_agua).astype(np.float32)
    mem = gdal.GetDriverByName("MEM").Create("", ds_antigo.RasterXSize, ds_antigo.RasterYSize, 1, gdal.GDT_Float32)
    mem.SetGeoTransform(ds_antigo.GetGeoTransform())
    mem.SetProjection(ds_antigo.GetProjection())
    mem.GetRasterBand(1).WriteArray(binario)

    gt = ds_8m.GetGeoTransform()
    xmin, ymax = gt[0], gt[3]
    xmax = xmin + gt[1] * ds_8m.RasterXSize
    ymin = ymax + gt[5] * ds_8m.RasterYSize
    destino = gdal.Warp("", mem, format="MEM", outputBounds=(xmin, ymin, xmax, ymax),
                        width=ds_8m.RasterXSize, height=ds_8m.RasterYSize,
                        dstSRS=ds_8m.GetProjection(), resampleAlg="average",
                        outputType=gdal.GDT_Float32, dstNodata=0)
    return destino.GetRasterBand(1).ReadAsArray()


def main():
    ds8 = gdal.Open(MAPA_8M)
    dsa = gdal.Open(MAPA_ANTIGO)
    if ds8 is None or dsa is None:
        raise FileNotFoundError("Não foi possível abrir um dos mapas.")
    mapa = ds8.GetRasterBand(1).ReadAsArray()
    frac = fracao_de_agua(dsa, ds8, CLASSE_AGUA_ANTIGO)

    agua = (frac > LIMIAR) & (mapa > 0)              # só dentro da área classificada
    final = mapa.copy()
    final[agua] = CLASSE_AGUA_NOVO

    out = gdal.GetDriverByName("GTiff").Create(SAIDA, ds8.RasterXSize, ds8.RasterYSize, 1,
                                               gdal.GDT_Byte, options=["COMPRESS=LZW"])
    out.SetGeoTransform(ds8.GetGeoTransform())
    out.SetProjection(ds8.GetProjection())
    b = out.GetRasterBand(1)
    b.WriteArray(final)
    b.SetNoDataValue(0)
    b.FlushCache()
    out = None

    area_pixel = abs(ds8.GetGeoTransform()[1] * ds8.GetGeoTransform()[5])
    print(f"Pixels de água: {int(agua.sum())} ({agua.sum() * area_pixel / 1e6:.3f} km²)")
    print(f"Mapa final salvo em: {SAIDA}")


if __name__ == "__main__":
    main()
