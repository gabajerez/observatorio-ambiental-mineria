"""Distancias por ID_POLIGONO, índice de cercanía y comparación exploratoria de etapas."""
from pathlib import Path
from itertools import combinations
import argparse
import json
import logging
import unicodedata
import numpy as np
import pandas as pd
import geopandas as gpd
import pyogrio
from pyproj import CRS
from shapely import make_valid, STRtree
from scipy import stats

ROOT = Path(r'C:\Users\Gabriela_Jerez\Desktop\distancias_mineria')
PROJECTS = 'proyectos_mineros_poligonos_validados.shp'
# Cada componente agrupado lleva su peso UNA sola vez.
COMPONENTS = {
 'areas_protegidas': ([1,5,10,25],16.5,['areas_protegidas']),
 'sitios_biosfera': ([1,5,10,25],9.9,['sitios_prioritarios','reservas_biosfera']),
 'glaciares': ([.5,2,10,25],13.3,['glaciares']),
 'humedales': ([1,5,10,25],12.0,['humedales']),
 'planes_atmosfericos': ([.5,5,25,50],17.0,['planes_atmosfericos']),
 'comunidades_indigenas': ([2,10,25,50],13.1,['comunidades_indigenas']),
 'areas_desarrollo_indigena': ([2,10,25,50],6.5,['areas_desarrollo_indigena']),
 'areas_pobladas': ([2,5,15,30],7.0,['areas_pobladas']),
 'turismo': ([.5,2,5,10],4.7,['atractivos_turisticos','zonas_interes_turistico']),
}
ALIASES = {
 'areas_protegidas':['areas protegidas'], 'sitios_prioritarios':['sitios prioritarios'],
 'reservas_biosfera':['reservas de la biosfera','reservas biosfera'],
 'glaciares':['glaciares'], 'humedales':['humedales'],
 'planes_atmosfericos':['planes de prevencion','descontaminacion'],
 'comunidades_indigenas':['comunidades indigenas'],
 'areas_desarrollo_indigena':['areas de desarrollo indigena'],
 'areas_pobladas':['areas pobladas'], 'atractivos_turisticos':['atractivos turisticos'],
 'zonas_interes_turistico':['zonas de interes turistico'],
}


def norm(x):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(x).lower())
                   if not unicodedata.combining(c)).strip()


def csv(df, path):
    df.to_csv(path,index=False,encoding='utf-8-sig')


def folders(root):
    return sorted(p for p in root.iterdir() if p.is_dir() and
                  p.name not in {'resultados','distancias_mineria_proyecto','__pycache__','.venv'})


def sources(folder, projects):
    """Todos los archivos vectoriales y todas las subcapas espaciales de contenedores."""
    found=[]
    paths=sorted(folder.rglob('*'))
    gdbs=[p for p in paths if p.is_dir() and p.suffix.lower()=='.gdb']
    if folder.suffix.lower()=='.gdb': gdbs.insert(0,folder)
    for p in paths + gdbs:
        if any(g in p.parents for g in gdbs): continue
        if p.resolve()==projects.resolve(): continue
        if p.suffix.lower() not in {'.shp','.gpkg','.geojson','.json','.gdb'}: continue
        if p.suffix.lower()=='.json':
            # JSON de configuración no es una capa.
            try:
                if json.loads(p.read_text(encoding='utf-8')).get('type') not in {'FeatureCollection','Feature'}:
                    continue
            except (ValueError,AttributeError): continue
        if p.suffix.lower() in {'.gpkg','.gdb'}:
            for layer, geom_type in pyogrio.list_layers(p):
                if geom_type: found.append((p,str(layer)))
        elif p.is_file(): found.append((p,None))
    return list(dict.fromkeys(found))


def read_layer(path, layer=None):
    return gpd.read_file(path,layer=layer,engine='pyogrio')


def inventory(root):
    out=root/'resultados'; out.mkdir(exist_ok=True)
    project=read_layer(root/PROJECTS)
    rows=[]
    for col in project.columns:
        if col==project.geometry.name: continue
        counts=project[col].fillna('<NULO>').astype(str).value_counts(dropna=False)
        for val,n in counts.items():
            rows.append({'campo':col,'valor':val,'n':n})
    csv(pd.DataFrame(rows),out/'campos_y_valores.csv')
    layers=[]
    dirs=folders(root)
    for folder in dirs:
        items=sources(folder,root/PROJECTS)
        if not items:
            layers.append({'carpeta':folder.name,'estado':'SIN_VECTOR_COMPATIBLE'})
        for path,layer in items:
            try:
                info=pyogrio.read_info(path,layer=layer)
                layers.append({'carpeta':folder.name,'archivo':str(path),'subcapa':layer,
                    'crs':info['crs'],'n_geometrias':info['features'],
                    'tipo':info['geometry_type'],'estado':'OK'})
            except Exception as e:
                layers.append({'carpeta':folder.name,'archivo':str(path),'estado':str(e)})
    csv(pd.DataFrame(layers),out/'inventario_capas.csv')
    proposal={key:[f.name for f in dirs if any(a in norm(f.name) for a in aliases)]
              for key,aliases in ALIASES.items()}
    cfg={'campo_id':'ID_POLIGONO','campo_origen_id_poligono':'OBJECTID','campo_etapa':None,
         'mapa_etapas':{'prospeccion':'prospeccion','operacion':'operacion','cierre':'cierre'},
         'carpetas_por_variable':proposal,
         'nota':'Revisar cada asignación. No se infiere el campo etapa. Claves de mapa_etapas son valores reales del SHP; valores son grupos canónicos.'}
    config=root/'config.json'
    if not config.exists(): config.write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
    logging.info('Inventario listo: %s. Revisar config.json antes de ejecutar.',out)


def clean(gdf, label, audit, polygon=False):
    if gdf.crs is None: raise ValueError(f'{label}: falta CRS; definirlo con antecedentes, no adivinarlo.')
    absent=gdf.geometry.isna() | gdf.geometry.is_empty
    invalid=~gdf.loc[~absent].geometry.is_valid
    audit.append({'fuente':label,'n_original':len(gdf),'n_vacias':int(absent.sum()),
                  'n_reparadas':int(invalid.sum()),'crs_original':str(gdf.crs)})
    # No excluir silenciosamente objetos: una geometría ausente puede cambiar el mínimo.
    if absent.any(): raise ValueError(f'{label}: {absent.sum()} geometrías vacías/nulas. Corregir antes de calcular.')
    gdf=gdf.copy()
    gdf.geometry=gdf.geometry.map(lambda g: make_valid(g) if not g.is_valid else g)
    if polygon and not gdf.geom_type.isin(['Polygon','MultiPolygon']).all():
        raise ValueError(f'{label}: se requieren polígonos; la reparación produjo otro tipo.')
    if gdf.geometry.is_empty.any() or not gdf.geometry.is_valid.all():
        raise ValueError(f'{label}: reparación de geometría incompleta.')
    gdf=gdf.to_crs(4326)
    if len(gdf) and (not np.isfinite(gdf.total_bounds).all()):
        raise ValueError(f'{label}: coordenadas no finitas tras reproyección.')
    # Densificación previa: reduce diferencias al transformar segmentos largos.
    # 0.01 grados son hasta ~1.1 km en WGS84; no es una interpolación geodésica.
    gdf.geometry=gdf.geometry.segmentize(.01)
    return gdf


def score(values, thresholds):
    a=np.asarray(values,dtype=float)
    if np.any(a[np.isfinite(a)]<0): raise ValueError('Distancias negativas.')
    result=np.select([a<=x for x in thresholds],[1,.75,.5,.25],default=0.).astype(float)
    result[~np.isfinite(a)]=np.nan
    return result


def index_table(distances, mapping):
    data=pd.DataFrame({'ID_POLIGONO':distances['ID_POLIGONO']})
    scores=[]; contributions=[]
    for component,(thresholds,weight,variables) in COMPONENTS.items():
        required=[]; missing=False
        for variable in variables:
            assigned=mapping.get(variable,[])
            if not assigned: missing=True
            required.extend(assigned)
        for name in required:
            if name not in distances: raise ValueError(f'Carpeta configurada inexistente: {name}')
        if missing:
            d=pd.Series(np.nan,index=distances.index)
        else:
            # Unión temática = mínimo entre carpetas, exigiendo todas las fuentes.
            d=distances[required].min(axis=1,skipna=False)
        data[component+'__km']=d
        data[component+'__score']=score(d,thresholds)
        data[component+'__aporte']=data[component+'__score']*weight
        scores.append(component+'__score'); contributions.append(component+'__aporte')
    data['componentes_disponibles']=data[scores].notna().sum(axis=1)
    data['indice_0_100']=data[contributions].sum(axis=1,skipna=False)
    data['cercania_media_0_100']=100*data[scores].mean(axis=1,skipna=False)
    return data


def holm(p):
    p=np.asarray(p); order=np.argsort(p); adjusted=np.empty(len(p))
    adjusted[order]=np.minimum(1,np.maximum.accumulate(p[order]*(len(p)-np.arange(len(p)))))
    return adjusted


def analysis(table,out):
    groups=['prospeccion','operacion','cierre']
    eligible=table[table['etapa'].isin(groups) & table['indice_0_100'].notna()].copy()
    csv(table[[c for c in ['ID_POLIGONO','ID_OA','etapa','indice_0_100'] if c in table]].assign(
        incluido=table.index.isin(eligible.index)),out/'inclusion_estadistica.csv')
    summary=eligible.groupby('etapa')['indice_0_100'].agg(
        n='size',media='mean',mediana='median',desv_std='std',minimo='min',maximo='max',
        q25=lambda x:x.quantile(.25),q75=lambda x:x.quantile(.75)).reindex(groups)
    csv(summary.reset_index(),out/'resumen_etapas.csv')
    arrays=[eligible.loc[eligible.etapa==g,'indice_0_100'].to_numpy() for g in groups]
    status={'n_total':len(table),'n_incluidos':len(eligible),'n_excluidos':len(table)-len(eligible),
            'alcance':'Exploratorio: independencia no verificada; región, tamaño y autocorrelación espacial pueden confundir la asociación.'}
    if any(len(x)<5 for x in arrays):
        status['estado']='NO_EJECUTADO: se requieren al menos 5 índices completos por cada una de las tres etapas.'
    elif 'ID_OA' not in eligible or eligible['ID_OA'].isna().any() or eligible['ID_OA'].duplicated().any():
        status['estado']='NO_EJECUTADO_DEPENDENCIA: faltan IDs de proyecto o varios polígonos pertenecen al mismo ID OA. Definir agrupación/modelo por proyecto antes de pruebas independientes.'
    else:
        if len(np.unique(np.concatenate(arrays)))==1: H,p=0.,1.
        else: H,p=stats.kruskal(*arrays)
        status.update(estado='OK',H=float(H),p=float(p),alpha=.05,
                      epsilon_cuadrado=float(max(0,(H-3+1)/(len(eligible)-3))))
        comparisons=[]
        for i,j in combinations(range(3),2):
            x,y=arrays[i],arrays[j]
            r=stats.mannwhitneyu(x,y,alternative='two-sided',method='asymptotic')
            comparisons.append({'etapa_A':groups[i],'etapa_B':groups[j],
                                'n_A':len(x),'n_B':len(y),'U':r.statistic,'p':r.pvalue,
                                'delta_cliff':2*r.statistic/(len(x)*len(y))-1})
        post=pd.DataFrame(comparisons)
        post['p_holm']=holm(post.p.to_numpy())
        post['significativo_005']=post.p_holm<.05
        csv(post,out/'comparaciones_pares.csv')
    (out/'estadistica.json').write_text(json.dumps(status,ensure_ascii=False,indent=2),encoding='utf-8')


def polygon_ids(frame, origin='OBJECTID'):
    """ID estable basado en identificador original, nunca en ID OA ni orden de filas."""
    frame=frame.copy()
    if 'ID_POLIGONO' in frame:
        ids=frame['ID_POLIGONO'].astype('string').str.strip()
    else:
        if origin not in frame:
            raise ValueError(f'Falta {origin}: se requiere una clave original única para crear ID_POLIGONO estable.')
        def token(value):
            if pd.isna(value): return pd.NA
            if isinstance(value,(int,float,np.integer,np.floating)) and float(value).is_integer():
                return str(int(value))
            return str(value).strip()
        tokens=frame[origin].map(token).astype('string')
        if tokens.isna().any() or tokens.eq('').any() or tokens.duplicated().any():
            raise ValueError(f'{origin} contiene claves nulas/vacías/repetidas; no puede identificar polígonos.')
        ids='POL_'+tokens
    if ids.isna().any() or ids.eq('').any() or ids.duplicated().any():
        raise ValueError('ID_POLIGONO debe ser único y no nulo.')
    frame['ID_POLIGONO']=ids.astype(str)
    return frame


def run(root):
    cfg=json.loads((root/'config.json').read_text(encoding='utf-8-sig'))
    if cfg.get('campo_id')!='ID_POLIGONO':
        raise ValueError('Esta versión calcula por polígono. Copiar config_revisada.json a config.json.')
    out=root/'resultados'; out.mkdir(exist_ok=True)
    for name in ['comparaciones_pares.csv','resumen_etapas.csv','estadistica.json','inclusion_estadistica.csv',
                 'distancias_por_carpeta_km.csv','indice_por_proyecto.csv','indice_por_poligono.csv',
                 'control_geometrias.csv','fuentes_utilizadas.csv','avisos_distancias.csv',
                 'resultados_observatorio.xlsx','config_utilizada.json','atributos_originales.csv',
                 'registros_sin_ID_OA.csv','poligonos_sin_ID_OA.csv','resumen_ID_repetidos.csv',
                 'plantilla_etapas_por_ID.csv','plantilla_etapas_por_poligono.csv','poligonos_identificados.gpkg']:
        (out/name).unlink(missing_ok=True)
    audit=[]
    # Persistir correspondencia en geometrías originales (antes de densificar/reparar).
    original=polygon_ids(read_layer(root/PROJECTS),cfg.get('campo_origen_id_poligono','OBJECTID'))
    original.to_file(out/'poligonos_identificados.gpkg',layer='poligonos',driver='GPKG',engine='pyogrio')
    projects=clean(original,'PROYECTOS',audit,polygon=True)
    if projects.empty: raise ValueError('Capa de proyectos vacía.')
    if 'ID_OA' not in projects: projects['ID_OA']=pd.NA
    missing_oa=projects['ID_OA'].isna() | projects['ID_OA'].astype(str).str.strip().eq('')
    logging.info('Unidad: polígono. Total %d; sin ID OA %d; no se disuelve ni excluye por ID OA.',len(projects),missing_oa.sum())
    csv(projects.loc[missing_oa].drop(columns=projects.geometry.name),out/'poligonos_sin_ID_OA.csv')
    duplicate_rows=[]
    for ident,part in projects.loc[~missing_oa].groupby('ID_OA'):
        if len(part)>1:
            duplicate_rows.append({'ID_OA':ident,'n_poligonos':len(part),
                                   'ID_POLIGONO':' | '.join(part.ID_POLIGONO.astype(str))})
    csv(pd.DataFrame(duplicate_rows,columns=['ID_OA','n_poligonos','ID_POLIGONO']),out/'resumen_ID_repetidos.csv')
    template=projects[[c for c in ['ID_POLIGONO','ID_OA','OBJECTID','NOMBRE'] if c in projects]].copy()
    for col in ['ETAPA','FUENTE','FECHA_REFERENCIA']: template[col]=''
    csv(template,out/'plantilla_etapas_por_poligono.csv')
    phase=cfg.get('campo_etapa')
    if phase and phase not in projects: raise ValueError(f'Campo etapa ausente: {phase}')
    if phase:
        phase_map={norm(k):v for k,v in cfg['mapa_etapas'].items()}
        if not set(phase_map.values()) <= {'prospeccion','operacion','cierre'}:
            raise ValueError('Valores del mapa_etapas: prospeccion, operacion o cierre.')
        projects['etapa']=projects[phase].map(lambda x:phase_map.get(norm(x),'sin_clasificar'))
    else: projects['etapa']='sin_clasificar'
    metadata=projects.drop(columns=projects.geometry.name).copy()
    csv(metadata,out/'atributos_originales.csv')
    layers={}; source_metadata=[]
    for folder in folders(root):
        geometries=[]
        items=sources(folder,root/PROJECTS)
        for path,layer in items:
            label=f'{path}::{layer or ""}'
            logging.info('Leyendo %s',label)
            frame=clean(read_layer(path,layer),label,audit)
            geometries.extend(frame.geometry.tolist())
            source_metadata.append({'carpeta':folder.name,'archivo':str(path),'subcapa':layer,'n':len(frame)})
        layers[folder.name]=gpd.GeoSeries(geometries,crs=4326)
    mapping=cfg['carpetas_por_variable']
    for var in ALIASES:
        names=mapping.get(var,[])
        if not isinstance(names,list): raise ValueError(f'{var}: usar lista de carpetas.')
        for name in names:
            if name not in layers: raise ValueError(f'{var}: carpeta desconocida {name}')
    distance_rows=[]; trace=[]
    for number,row in enumerate(projects.itertuples(index=False),1):
        geom=row.geometry; center=geom.representative_point()
        local=CRS.from_proj4(f'+proj=aeqd +lat_0={center.y} +lon_0={center.x} +datum=WGS84 +units=m +no_defs')
        projected=gpd.GeoSeries([geom],crs=4326).to_crs(local).iloc[0]
        record={'ID_POLIGONO':row.ID_POLIGONO,'ID_OA':row.ID_OA}
        for name,series in layers.items():
            if series.empty: record[name]=np.nan; continue
            # Intersección en CRS común evita errores topológicos por reproyección.
            if series.intersects(geom).any(): distance=0.
            else:
                target=series.to_crs(local)
                bounds=target.total_bounds
                if not np.isfinite(bounds).all(): raise ValueError(f'{name}: proyección no finita.')
                nearest=STRtree(target.to_numpy()).nearest(projected)
                distance=projected.distance(target.iloc[int(nearest)])/1000
            if not np.isfinite(distance): raise ValueError(f'{name}: distancia no finita.')
            record[name]=distance
            if distance>500:
                trace.append({'ID_POLIGONO':row.ID_POLIGONO,'ID_OA':row.ID_OA,'carpeta':name,'distancia_km':distance,
                              'aviso':'Distancia proyectada >500 km: verificar con método geodésico si se requiere precisión a larga distancia.'})
        distance_rows.append(record)
        if number%10==0 or number==len(projects):
            logging.info('Polígonos %d/%d',number,len(projects))
    distances=pd.DataFrame(distance_rows)
    indexed=index_table(distances,mapping).merge(metadata,on='ID_POLIGONO',validate='one_to_one')
    csv(distances,out/'distancias_por_carpeta_km.csv')
    csv(indexed,out/'indice_por_poligono.csv')
    csv(pd.DataFrame(audit),out/'control_geometrias.csv')
    csv(pd.DataFrame(source_metadata),out/'fuentes_utilizadas.csv')
    csv(pd.DataFrame(trace,columns=['ID_POLIGONO','ID_OA','carpeta','distancia_km','aviso']),out/'avisos_distancias.csv')
    analysis(indexed,out)
    with pd.ExcelWriter(out/'resultados_observatorio.xlsx',engine='openpyxl') as writer:
        distances.to_excel(writer,sheet_name='Distancias_km',index=False)
        indexed.to_excel(writer,sheet_name='Indice',index=False)
        pd.DataFrame(audit).to_excel(writer,sheet_name='Control',index=False)
        for file,sheet in [('resumen_etapas.csv','Etapas'),('comparaciones_pares.csv','Comparaciones')]:
            if (out/file).exists(): pd.read_csv(out/file).to_excel(writer,sheet_name=sheet,index=False)
    (out/'config_utilizada.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2),encoding='utf-8')
    logging.info('Resultados listos: %s',out)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('accion',choices=['inventario','ejecutar'])
    p.add_argument('--root',type=Path,default=ROOT)
    args=p.parse_args()
    logging.basicConfig(level=logging.INFO,format='%(asctime)s %(message)s')
    if not args.root.is_dir(): p.error(f'Carpeta inexistente: {args.root}')
    if args.accion=='inventario': inventory(args.root)
    else: run(args.root)


if __name__=='__main__': main()
