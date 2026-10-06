# Observatorio ambiental de minería

Cálculo de distancias mínimas entre cada polígono minero y capas ambientales/territoriales,
con un índice de cercanía ponderada y preparación para comparar etapas de los proyectos.

## Estado de la entrega

La ejecución entregada el **6 de octubre de 2026** contiene:

| Elemento | Resultado |
|---|---:|
| Polígonos con identificador único | 869 |
| Polígonos sin ID OA, incluidos | 81 |
| Carpetas temáticas con distancia | 11 |
| Componentes completos del índice | 9 por polígono |
| Índice medio | 29,445742 |
| Índice mediano | 27,15 |
| Rango del índice | 0–83,675 |
| Polígonos con índice cero | 17 |

La identidad de cálculo es **ID_POLIGONO**, conservada si existe o creada como
`POL_<OBJECTID>`. ID OA permanece como atributo y puede estar vacío. No se disuelven
los registros con el mismo ID OA. Un registro MultiPolygon constituye una unidad.
El identificador es estable mientras se conserve el OBJECTID original.

El índice mide **cercanía ponderada**, no daño ambiental, incumplimiento ni un riesgo
cuantificado. Las etapas prospección/operación/cierre no están en el archivo exportado:
los 869 resultados están `sin_clasificar`. Esa comparación todavía no se ha realizado.

## Contenido

| Ruta | Contenido |
|---|---|
| `distancias_mineria_proyecto/observatorio.py` | Inventario, cálculo, índice y controles |
| `distancias_mineria_proyecto/requirements.txt` | Dependencias |
| `distancias_mineria_proyecto/prueba_sintetica.py` | Verificación con datos artificiales |
| `config.json` | Configuración revisada para las carpetas reales |
| `resultados/` | CSV de distancias e índice, Excel, inventarios |
| `docs/Ponderacion_articulo.docx` | Metodología de ponderación aportada |
| `docs/LEEME_poligonos_original.txt` | Campos del shapefile minero aportados |
| `docs/DECISIONES.md` | Bitácora técnica de esta conversación |
| `docs/VALIDACION.md` | Alcance de la revisión de resultados |
| `docs/SHA256SUMS.txt` | Huellas de código, configuración y archivos entregados |
| `datos_originales/README.md` | Fuentes necesarias para reproducir el cálculo |

Las capas originales no se adjuntaron a esta sesión y **no están incluidas**. Tampoco
se recibió `poligonos_identificados.gpkg` ni todos los CSV auxiliares de la ejecución.
El inventario conserva las rutas Windows de las fuentes; no son enlaces descargables.

## Ejecutar en Windows con Conda

El entorno `distancias_mineria` ya fue instalado en el equipo de trabajo. Para una
instalación nueva, desde PowerShell y con Conda disponible:

```powershell
conda create -n distancias_mineria python=3.11 pip -y
conda activate distancias_mineria
python -m pip install -r ".\distancias_mineria_proyecto\requirements.txt"
```

Para usar el conjunto de capas que permanece en la carpeta de trabajo original:

```powershell
conda activate distancias_mineria
Copy-Item ".\config.json" "C:\Users\Gabriela_Jerez\Desktop\distancias_mineria\config.json" -Force
python ".\distancias_mineria_proyecto\observatorio.py" inventario --root "C:\Users\Gabriela_Jerez\Desktop\distancias_mineria"
python ".\distancias_mineria_proyecto\observatorio.py" ejecutar --root "C:\Users\Gabriela_Jerez\Desktop\distancias_mineria"
```

Ejecuta estos comandos desde la raíz de este repositorio. Para otra ubicación,
reemplaza las rutas de destino y `--root`. La carpeta indicada debe contener el
shapefile minero y las carpetas temáticas con sus archivos auxiliares.

La ejecución escribe resultados dentro de `--root/resultados`, limpiando las salidas
conocidas anteriores. El repositorio mantiene el snapshot entregado en `resultados/`;
no se actualiza por ejecutar contra otra carpeta. Para actualizarlo, copiar después
los resultados nuevos, revisar diferencias y hacer un nuevo commit.

Mantén el clon fuera de la carpeta de capas originales: el lector recorre sus carpetas
hijas y no debe incorporar archivos del propio repositorio como fuentes ambientales.

## Verificación

```powershell
python ".\distancias_mineria_proyecto\prueba_sintetica.py"
```

Las pruebas comprueban IDs estables, distancia al borde, contacto, inclusión de ID OA
nulo, separación de polígonos del mismo proyecto, puntajes y dependencia estadística.
La fórmula del índice se recalculó sobre las tablas reales y coincide; Excel y CSV
coinciden. Esa revisión no vuelve a medir distancias contra las geometrías reales.

## Método y limitaciones

- Distancias entre geometrías completas; contacto/intersección/contención da 0 km.
- Todos los vectores y subcapas de una carpeta integran su mínimo.
- CRS común WGS84 y proyección AEQD local por polígono, con densificación previa.
  La distancia es una aproximación métrica local, no una solución geodésica exacta
  entre bordes. Validar casos próximos a umbrales y geometrías extensas/insulares.
- Nueve componentes con pesos que suman 100 %. Sitios prioritarios/biosfera y
  atractivos/ZOIT son componentes agrupados. Se requiere confirmar la interpretación
  del peso agrupado de 9,9 % antes de publicación científica.
- Ausencia de datos no equivale a cero; el índice exige los nueve componentes.
- La carpeta turística incluye todas sus tres capas. Confirmar si `Zonas a usar`
  debía sustituir a la capa original en lugar de agregarse.
- El control informa 14 geometrías mineras reparadas y 112 reparaciones en capas
  ambientales. Conviene inspeccionar las reparaciones y verificar casos relevantes.
- La inferencia por etapas debe respetar la dependencia entre polígonos de un mismo
  proyecto y considerar región y estructura espacial. Las pruebas independientes
  quedan suspendidas si hay IDs OA nulos/repetidos entre los registros elegibles.

Consulta `distancias_mineria_proyecto/LEEME_PROYECTO.md` para umbrales, pesos, formatos
admitidos, controles y salidas detalladas.

## Pendientes

1. Obtener una tabla verificable de etapa y vincularla a ID_POLIGONO/ID OA.
2. Revisar las fuentes turísticas y validar espacialmente los casos relevantes.
3. Definir la comparación entre etapas con agrupación por proyecto y ajuste territorial.
4. Incorporar las capas originales, su procedencia y fecha cuando estén disponibles.
