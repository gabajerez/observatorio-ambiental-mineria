"""Verificación artificial por polígono; no lee ni modifica datos reales."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import box, Point
from observatorio import COMPONENTS, PROJECTS, inventory, run, score, index_table, holm, polygon_ids, analysis


def main():
    assert abs(sum(c[1] for c in COMPONENTS.values())-100)<1e-10
    np.testing.assert_allclose(score([0,1,1.01,5,5.01,10,10.01,25,25.01,np.nan],[1,5,10,25]),
                               [1,1,.75,.75,.5,.5,.25,.25,0,np.nan],equal_nan=True)
    np.testing.assert_allclose(holm([.01,.04,.03]),[.03,.06,.06])
    mapping={v:[v] for c in COMPONENTS.values() for v in c[2]}
    d=pd.DataFrame({'ID_POLIGONO':['A','B']})
    for var in mapping: d[var]=[0,100]
    assert index_table(d,mapping).indice_0_100.tolist()==[100.,0.]
    d.loc[0,'reservas_biosfera']=np.nan
    assert pd.isna(index_table(d,mapping).loc[0,'indice_0_100'])
    with TemporaryDirectory() as tmp:
        root=Path(tmp)
        geoms=[]; ids=[]; stages=[]
        for i in range(15):
            geoms.append(box(300000+i*3000,6300000,300100+i*3000,6300100))
            ids.append(f'OA{i:02}'); stages.append(['Prospección','Operación','Cierre'][i//5])
        # Dos polígonos del mismo proyecto deben conservar distancias distintas.
        geoms.append(box(301000,6300000,301100,6300100)); ids.append('OA00'); stages.append('Prospección')
        geoms.append(box(350000,6300000,350100,6300100)); ids.append(None); stages.append('Operación')
        projects=gpd.GeoDataFrame({'OBJECTID':range(1,18),'ID_OA':ids,'ETAPA':stages},geometry=geoms,crs=32719).to_crs(4326)
        generated=polygon_ids(projects)
        shuffled=polygon_ids(projects.sample(frac=1,random_state=42))
        assert generated.set_index('OBJECTID').ID_POLIGONO.to_dict()==shuffled.set_index('OBJECTID').ID_POLIGONO.to_dict()
        assert polygon_ids(generated).ID_POLIGONO.tolist()==generated.ID_POLIGONO.tolist()
        invalid=projects.copy(); invalid.loc[1,'OBJECTID']=1
        try: polygon_ids(invalid)
        except ValueError: pass
        else: raise AssertionError('Clave original repetida debe detenerse')
        projects.to_file(root/PROJECTS)
        target=gpd.GeoDataFrame({'nombre':['test']},geometry=[Point(301050,6300050)],crs=32719)
        for var in mapping:
            folder=root/var; folder.mkdir()
            target.to_file(folder/'capa.gpkg',layer='objetivos',driver='GPKG')
        inventory(root)
        cfg=json.loads((root/'config.json').read_text())
        cfg.update(campo_etapa='ETAPA',carpetas_por_variable=mapping)
        (root/'config.json').write_text(json.dumps(cfg),encoding='utf-8')
        run(root)
        distances=pd.read_csv(root/'resultados'/'distancias_por_carpeta_km.csv')
        assert len(distances)==17 and distances.ID_POLIGONO.is_unique
        first=distances.set_index('ID_POLIGONO')
        assert abs(first.loc['POL_1','glaciares']-.95)<.005
        assert first.loc['POL_16','glaciares']==0
        assert abs(first.loc['POL_2','glaciares']-1.95)<.005
        assert pd.isna(first.loc['POL_17','ID_OA'])
        assert np.isfinite(first.loc['POL_17','glaciares'])
        indexed=pd.read_csv(root/'resultados'/'indice_por_poligono.csv')
        assert len(indexed)==17 and indexed.indice_0_100.notna().all()
        assert len(pd.read_csv(root/'resultados'/'poligonos_sin_ID_OA.csv'))==1
        assert len(gpd.read_file(root/'resultados'/'poligonos_identificados.gpkg'))==17
        assert len(pd.read_csv(root/'resultados'/'plantilla_etapas_por_poligono.csv'))==17
        status=json.loads((root/'resultados'/'estadistica.json').read_text())
        assert status['estado'].startswith('NO_EJECUTADO_DEPENDENCIA')
        # Verificar la rutina de contraste con 15 observaciones artificiales independientes.
        analysis(indexed.iloc[:15].copy(),root/'resultados')
        assert json.loads((root/'resultados'/'estadistica.json').read_text())['estado']=='OK'
        assert len(pd.read_csv(root/'resultados'/'comparaciones_pares.csv'))==3
        cfg['campo_etapa']=None
        (root/'config.json').write_text(json.dumps(cfg),encoding='utf-8')
        run(root)
        assert not (root/'resultados'/'comparaciones_pares.csv').exists()
        assert json.loads((root/'resultados'/'estadistica.json').read_text())['estado'].startswith('NO_EJECUTADO')
    print('OK: cálculo por polígono; IDs estables; sin disolver; ID OA nulo conservado; índice y control estadístico.')


if __name__=='__main__': main()
