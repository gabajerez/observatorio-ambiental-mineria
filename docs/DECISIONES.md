# Bitácora técnica — 6 de octubre de 2026

Síntesis de las decisiones de la conversación que originó el proyecto; no es una
transcripción literal del chat ni sustituye los archivos fuente.

1. **Objetivo:** medir la distancia mínima de las geometrías mineras a todas las
   capas contenidas en cada carpeta temática; una columna por carpeta, en km.
2. **Metodología:** utilizar los umbrales y pesos del documento de ponderación aportado.
   Se interpretan nueve componentes: sitios prioritarios y biosfera se agrupan con
   9,9 % una sola vez; atractivos turísticos y ZOIT se agrupan con 4,7 %.
3. **Identidad inicial:** se propuso agrupar por ID OA. El inventario reveló 869
   polígonos, 81 IDs OA nulos y 615 IDs OA no nulos distintos. Esa propuesta fue
   reemplazada por instrucción de Gabriela: cálculo individual por ID_POLIGONO.
4. **Identidad final:** usar ID_POLIGONO único, derivado de OBJECTID cuando no existe.
   Conservar ID OA como atributo. Incluir registros sin ID OA y no disolver geometrías.
5. **Entorno Windows:** el lanzador `py` no estaba disponible. Se creó el entorno
   Conda `distancias_mineria`, Python 3.11; las dependencias se instalaron correctamente.
6. **Inventario:** 11 carpetas y 13 capas vectoriales. CRS declarados EPSG:4326 y
   EPSG:32719. Se corrigieron asignaciones de biosfera y las dos variables turísticas.
7. **Turismo:** `Atractivo Turístico (Nuevo)` contiene 4853 puntos, otra capa de 2942
   puntos y una de 7 polígonos dentro de `Zonas a usar`. Se incorporan las tres conforme
   al mínimo por carpeta. La selección definitiva de versiones sigue pendiente de revisión.
8. **Geometrías:** reparación de invalidez y registro de cantidades. El shapefile
   original no se modifica. Se genera un GeoPackage separado con la correspondencia de IDs.
9. **Resultados:** se recibieron las distancias, el índice por polígono y un Excel.
   Incluyen los 869 registros, los 81 sin ID OA y nueve componentes completos.
10. **Revisión:** fórmula y agrupaciones recalculadas desde las tablas; concordancia
    CSV/Excel. No se recibieron las geometrías para volver a validar espacialmente.
11. **Etapas:** ninguna columna del archivo exportado contiene la clasificación
    prospección/operación/cierre. No se infiere desde TIPO ni los nombres. Toda etapa
    continúa `sin_clasificar` hasta disponer de una fuente verificable.
12. **Estadística:** identificar cada polígono no resuelve la dependencia entre
    registros del mismo proyecto. La comparación deberá respetarla y considerar
    región, tamaño de faena y autocorrelación espacial según los datos disponibles.
13. **Repositorio:** se solicitó organizar el código, metodología y resultados en GitHub.
    Este paquete conserva los archivos disponibles y documenta las fuentes locales faltantes.
