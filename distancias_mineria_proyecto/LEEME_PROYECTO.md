# Observatorio ambiental de minería — cálculo por polígono

Versión actualizada el 06-10-2026: **cada registro poligonal es una unidad de cálculo**.
Se conservan todos los registros, tengan o no ID OA. No se disuelven geometrías.
Un registro MultiPolygon conserva un solo ID_POLIGONO: no se separan sus partes.

El archivo inventariado tiene 869 registros, 81 sin ID OA y 615 IDs OA no nulos distintos.
Estas cantidades provienen del inventario; no se han ejecutado las capas reales aquí.

## Ejecutar en tu Windows

Descomprime el ZIP en `C:\Users\Gabriela_Jerez\Desktop\distancias_mineria`,
reemplazando la carpeta anterior `distancias_mineria_proyecto`.
El entorno Conda `distancias_mineria` ya tiene las dependencias necesarias.

```powershell
cd "C:\Users\Gabriela_Jerez\Desktop\distancias_mineria"
conda activate distancias_mineria
Copy-Item ".\distancias_mineria_proyecto\config_revisada.json" ".\config.json" -Force
python ".\distancias_mineria_proyecto\observatorio.py" ejecutar
```

La configuración revisada utiliza las 11 carpetas del inventario y mantiene
`campo_etapa: null`: los campos exportados no incluyen prospección/operación/cierre.
Los resultados de distancias e índice se generan igualmente. La estadística queda
pendiente hasta obtener esa variable desde una fuente verificable.

Para volver a inventariar: `python .\distancias_mineria_proyecto\observatorio.py inventario`.
Para otra ruta, agrega `--root "D:\otra\carpeta"`.

## Identidad de los polígonos

- Si existe `ID_POLIGONO`, se conserva y se exige que sea único y no nulo.
- Si no existe, se genera `POL_<OBJECTID>`, por ejemplo `POL_433`.
- OBJECTID debe ser único y no nulo. No se usa el orden de filas para asignar identidad.
- Se conserva `ID_OA` con sus valores originales y sus nulos, como atributo de vinculación.
- Dos registros con el mismo ID OA obtienen dos IDs de polígono y resultados propios.
- Los 81 registros sin ID OA reciben un ID de polígono y se calculan normalmente.

Los IDs son reproducibles mientras el identificador original OBJECTID se conserve.
Si otro programa regenera OBJECTID al exportar, conserva previamente ID_POLIGONO o
utiliza el GeoPackage generado como referencia de correspondencia. No es una identidad
universal derivada de la geometría ni un ID nuevo de proyecto.

Se genera `resultados\poligonos_identificados.gpkg`, capa `poligonos`, con la geometría
leída del archivo original y el ID nuevo, antes de reparación/densificación. Puedes
abrirlo en QGIS y unir los resultados CSV mediante ID_POLIGONO. El shapefile original
no se modifica. La autocorrección de orientación de anillos al leer puede reflejarse
en el GeoPackage; no cambia la unidad de cálculo.

La carpeta `resultados` se excluye de la búsqueda de capas, evitando calcular distancias
contra archivos generados por el propio proyecto.

## Distancias y controles

La tabla tiene ID_POLIGONO, ID_OA y una columna por carpeta, en kilómetros.
Se calcula el mínimo entre geometrías completas: contacto, intersección y contención
producen 0 km. No se reemplaza el polígono por su centroide. No se recortan las capas
por región administrativa ni se limita la búsqueda a un buffer.

Incluye todos los archivos SHP, GPKG, GeoJSON/JSON geográfico y FileGDB de cada carpeta
y sus subcarpetas, con todas las subcapas espaciales de los contenedores. No lee ráster,
KML, ZIP ni servicios web. Carpetas sin vectores compatibles producen NaN, no cero.
Los errores de lectura, falta de CRS o geometrías vacías/nulas detienen el cálculo.
No se adivina el CRS. Las geometrías inválidas se reparan y se registra su cantidad;
revisa las reparaciones antes de utilizar resultados publicados.

Se usa WGS84 como CRS común y una proyección AEQD local centrada en un punto interior
de cada polígono. El punto define la proyección y no reemplaza el polígono. Los segmentos
se densifican a 0,01° antes de proyectar (hasta aproximadamente 1,1 km).
La distancia euclidiana en esa proyección es una aproximación métrica local: AEQD
preserva distancias radiales desde el centro, no todas las distancias entre bordes.
No hay una cota universal de error para polígonos extensos o dispersos. Se advierten
mínimos >500 km; valida polígonos extensos, territorios insulares y casos próximos a
los umbrales antes de publicar. Si se exige precisión geodésica, debe implementarse
una búsqueda de bordes sobre el elipsoide con tolerancia explícita. La densificación
actual no interpola segmentos geodésicos exactos.

La carpeta `Atractivo Turístico (Nuevo)` contiene 4853 puntos originales, 2942 puntos
en `Zonas a usar` y 7 polígonos turísticos. Esta versión incorpora las tres capas,
conforme al mínimo por carpeta solicitado. Confirma si `Zonas a usar` debía reemplazar
la capa original antes de publicación. La carpeta separada ZOIT contiene 24 polígonos.

El cálculo puede tardar con capas grandes, porque transforma las capas para cada
polígono. Reporta avance cada diez registros. No cierres la consola durante la ejecución.
Las salidas conocidas de una ejecución anterior se limpian al comenzar; utiliza las
salidas solo cuando termine con `Resultados listos`.

## Índice de cercanía territorial

| Componente | Umbrales km (D1, D2, D3, D4) | Peso % |
|---|---|---:|
| Áreas protegidas | 1; 5; 10; 25 | 16,5 |
| Sitios prioritarios + reservas de la biosfera | 1; 5; 10; 25 | 9,9 |
| Glaciares | 0,5; 2; 10; 25 | 13,3 |
| Humedales | 1; 5; 10; 25 | 12,0 |
| Planes atmosféricos | 0,5; 5; 25; 50 | 17,0 |
| Comunidades indígenas | 2; 10; 25; 50 | 13,1 |
| Áreas de desarrollo indígena | 2; 10; 25; 50 | 6,5 |
| Áreas pobladas | 2; 5; 15; 30 | 7,0 |
| Atractivos turísticos + ZOIT | 0,5; 2; 5; 10 | 4,7 |

Los pesos suman 100 %. Se interpreta que 9,9 % corresponde al componente agrupado
sitios/biosfera, una única vez. Contarlo dos veces daría 109,9 %. Turismo se agrupa con
peso 4,7 %. Confirma esta interpretación con quienes elaboraron la metodología antes
de publicar.

Puntaje: d <= D1 → 1; D1 < d <= D2 → 0,75; D2 < d <= D3 → 0,5;
D3 < d <= D4 → 0,25; d > D4 → 0. Se incluye el límite superior, sin redondear antes.

`indice_0_100 = Σ (peso_porcentual × puntaje)`.
`cercania_media_0_100` también entrega una media sin pesos de los nueve puntajes.
El documento adjunto señala que los pesos no eran necesarios aún; se conservan ambas
versiones para hacer explícita la elección.

La distancia al grupo fusionado es el mínimo entre sus carpetas. Si falta una fuente
requerida, el componente queda NaN. El índice exige nueve componentes completos;
no se renormalizan pesos ni se confunde falta de datos con una distancia mayor a D4.
Un ID OA ausente no afecta la disponibilidad del índice.

**Mayor índice = mayor cercanía ponderada.** No demuestra daño, incumplimiento ni
riesgo cuantificado. Fechas, cobertura y calidad de las capas condicionan el resultado.

## Etapas y estadística

Para completar las etapas se genera `plantilla_etapas_por_poligono.csv` con ID_POLIGONO,
ID_OA, OBJECTID y NOMBRE cuando existen, más ETAPA, FUENTE y FECHA_REFERENCIA vacías.
La plantilla reúne datos: esta versión no la incorpora automáticamente.
Alternativamente, agrega un campo de etapa verificable al archivo de entrada y configura
`campo_etapa` y `mapa_etapas` con los nombres/valores reales. No se infiere la etapa
por el nombre, TIPO o categoría de tamaño.

Con etapa disponible se generan descripciones por polígono (n, mediana, media, cuartiles).
Polígonos del mismo proyecto no se consideran automáticamente observaciones independientes:
esta versión suspende Kruskal–Wallis y Mann–Whitney si la muestra elegible contiene
ID OA repetidos o nulos. Si hay al menos cinco observaciones completas por cada etapa
y una sola observación por proyecto identificado, se ejecutan las pruebas independientes
con corrección Holm de los tres contrastes por pares y tamaños de efecto.

Para comparar las etapas utilizando todos los polígonos de cada proyecto se requiere
un análisis que respete esa dependencia (agrupación por proyecto o modelo con estructura
por proyecto). La unidad geométrica de cálculo sigue siendo el polígono. También deben
considerarse región, superficie y autocorrelación espacial. No se interpreta p>=0,05
como prueba de igualdad ni una asociación significativa como efecto causal de la etapa.

## Salidas

- `distancias_por_carpeta_km.csv`: un registro por ID_POLIGONO, ID_OA y distancias.
- `indice_por_poligono.csv`: índice, componentes y atributos originales, por polígono.
- `resultados_observatorio.xlsx`: distancias, índice, controles y resúmenes disponibles.
- `poligonos_identificados.gpkg`: geometría de referencia con identidad asignada.
- `atributos_originales.csv`: correspondencia entre IDs y atributos.
- `poligonos_sin_ID_OA.csv`: registros sin ID OA incluidos en el cálculo.
- `resumen_ID_repetidos.csv`: proyectos con varios polígonos y sus IDs.
- `plantilla_etapas_por_poligono.csv`: tabla para documentar etapas.
- `control_geometrias.csv`, `fuentes_utilizadas.csv`, `avisos_distancias.csv`: trazabilidad.
- `inclusion_estadistica.csv`, `resumen_etapas.csv`, `estadistica.json`: datos y diagnóstico.
- `comparaciones_pares.csv`: solo si se ejecutaron pruebas independientes.
- `config_utilizada.json`: configuración de la ejecución.

## Verificación y referencias

`python distancias_mineria_proyecto/prueba_sintetica.py` verifica límites, distancias al borde,
IDs estables ante reordenamiento, no disolución de IDs OA repetidos, inclusión de ID OA nulo,
GeoPackage de referencia, índice completo y control de dependencia estadística.
No sustituye la validación de las capas reales.

- GeoPandas: https://geopandas.org/en/stable/docs/reference/api/geopandas.GeoSeries.distance.html
- PROJ AEQD: https://proj.org/en/stable/operations/projections/aeqd.html
- SciPy Kruskal: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kruskal.html
- SciPy Mann–Whitney: https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.mannwhitneyu.html
