"""
IDVU e população por unidade de análise (Seção 3.7; Eq. 3.6 e 3.7)

  IDVU = A_v / N_h                      (Eq. 3.6)  [m²/hab]
  N_h  = soma_s  P_s * U_sd / U_s       (Eq. 3.7)  método dasimétrico (Mennis, 2003)

Unidades: (i) perímetro urbano -> população dos setores ponderada pela fração de área
          do setor dentro do perímetro; (ii) área urbanizada densa -> Eq. 3.7.
ATENÇÃO: U_s é contado sobre o mapa classificado. Se o mapa estiver recortado no perímetro,
setores que ultrapassam o perímetro só têm pixels dentro dele (confira na etapa de revisão).
Entradas : mapa final de 8 m; setores censitários (GPKG/SHP) com V0001; perímetro; área densa
Requer   : Python 3, NumPy, GDAL/OGR
"""
import numpy as np
from osgeo import gdal, ogr

# ======================== CONFIGURAÇÃO ========================
MAPA_FINAL = r"C:\Users\Sabrina\Desktop\06_10_2026\mapa_final_5classes.tif"
SETORES = r"C:\Users\Sabrina\Desktop\06_10_2026\setores_censitarios_31983.gpkg"
CAMPO_POP = "V0001"                 # total de pessoas residentes (Censo 2022)
PERIMETRO = r"C:\Users\Sabrina\Desktop\06_10_2026\perimetro_urbano.gpkg"
AREA_DENSA = r"C:\Users\Sabrina\Desktop\06_10_2026\area_urbanizada_densa.gpkg"
VEGETACAO, AREA_URBANA = 1, 2       # códigos no mapa
# Área de vegetação ajustada pela validação (km², do script 03); None = só a medida no mapa
AV_AJUSTADA_KM2 = {"perimetro": None, "densa": None}
LIMIARES = {"OMS mínimo": 12, "OMS ideal": 36, "Russo e Cirella": 9}
# ==============================================================


def rasterizar(caminho, ds_ref, campo=None):
    """Rasteriza uma camada na grade do mapa. Sem campo -> máscara 0/1; com campo -> índice do setor (1..n)."""
    src = ogr.Open(caminho)
    lyr = src.GetLayer(0)
    mem = gdal.GetDriverByName("MEM").Create("", ds_ref.RasterXSize, ds_ref.RasterYSize, 1,
                                             gdal.GDT_Int32 if campo else gdal.GDT_Byte)
    mem.SetGeoTransform(ds_ref.GetGeoTransform())
    mem.SetProjection(ds_ref.GetProjection())
    if campo:
        gdal.RasterizeLayer(mem, [1], lyr, options=[f"ATTRIBUTE={campo}"])
    else:
        gdal.RasterizeLayer(mem, [1], lyr, burn_values=[1])
    return mem.GetRasterBand(1).ReadAsArray()


def preparar_setores(caminho, campo_pop):
    """Copia os setores para memória, com um índice inteiro (idx) e a população numérica."""
    src = ogr.Open(caminho)
    lyr = src.GetLayer(0)
    mem = ogr.GetDriverByName("Memory").CreateDataSource("s")
    out = mem.CreateLayer("setores", lyr.GetSpatialRef(), lyr.GetGeomType())
    out.CreateField(ogr.FieldDefn("idx", ogr.OFTInteger))
    pop = {}
    for k, f in enumerate(lyr, start=1):
        novo = ogr.Feature(out.GetLayerDefn())
        novo.SetGeometry(f.GetGeometryRef().Clone())
        novo.SetField("idx", k)
        out.CreateFeature(novo)
        v = f.GetField(campo_pop)
        try:
            pop[k] = float(str(v).replace(",", ".")) if v not in (None, "", "X") else 0.0
        except ValueError:
            pop[k] = 0.0
    return mem, pop


def main():
    ds = gdal.Open(MAPA_FINAL)
    mapa = ds.GetRasterBand(1).ReadAsArray()
    gt = ds.GetGeoTransform()
    area_pixel = abs(gt[1] * gt[5])                         # m²

    mem, pop = preparar_setores(SETORES, CAMPO_POP)
    tmp = r"/vsimem/setores.gpkg"
    ogr.GetDriverByName("GPKG").CopyDataSource(mem, tmp)
    idx = rasterizar(tmp, ds, "idx")                        # setor de cada pixel
    gdal.Unlink(tmp)
    valido = mapa > 0
    n_setores = max(pop)

    unidades = {"perimetro": rasterizar(PERIMETRO, ds).astype(bool) & valido,
                "densa": rasterizar(AREA_DENSA, ds).astype(bool) & valido}
    urbano = (mapa == AREA_URBANA)

    for nome, mask in unidades.items():
        Nh = 0.0
        for s in range(1, n_setores + 1):
            no_setor = (idx == s) & valido
            Us = int((no_setor & urbano).sum())
            if nome == "densa":                              # Eq. 3.7
                Usd = int((no_setor & urbano & mask).sum())
                if Us > 0:
                    Nh += pop[s] * Usd / Us
                elif no_setor.sum() > 0:                     # setor sem Área Urbana: usa fração de área
                    Nh += pop[s] * (no_setor & mask).sum() / no_setor.sum()
            else:                                            # perímetro: fração de área do setor dentro
                tot = int(no_setor.sum())
                if tot > 0:
                    Nh += pop[s] * (no_setor & mask).sum() / tot
        Av_mapa = int(((mapa == VEGETACAO) & mask).sum()) * area_pixel          # m²
        print(f"\n=== {nome} ===")
        print(f"Área da unidade: {mask.sum() * area_pixel / 1e6:.3f} km²   População estimada: {Nh:,.0f}".replace(",", "."))
        print(f"A_v (mapa): {Av_mapa / 1e6:.3f} km²   IDVU (mapa): {Av_mapa / Nh:.2f} m²/hab")
        aj = AV_AJUSTADA_KM2.get(nome)
        if aj:
            print(f"A_v (ajustada): {aj:.3f} km²   IDVU (ajustado): {aj * 1e6 / Nh:.2f} m²/hab")
        for k, v in LIMIARES.items():
            print(f"  {k}: {v} m²/hab -> {'atende' if Av_mapa / Nh >= v else 'não atende'}")


if __name__ == "__main__":
    main()
