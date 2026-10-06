# Validación de la entrega

Archivos revisados: `resultados_observatorio.xlsx`, `distancias_por_carpeta_km.csv`
e `indice_por_poligono.csv`, recibidos el 06-10-2026.

## Comprobaciones realizadas

- 869 filas y 869 IDs de polígono únicos en ambos CSV, con los mismos identificadores.
- 81 ID OA nulos conservados; 615 IDs OA distintos no nulos.
- Las 9559 distancias (869 × 11) son finitas y no negativas.
- Los nueve componentes están completos en los 869 registros.
- Las distancias agrupadas coinciden con el mínimo de las carpetas correspondientes.
- Los puntajes coinciden con los umbrales; cada aporte coincide con peso × puntaje.
- El índice ponderado y la media sin pesos se recalcularon desde las distancias.
  Error máximo de redondeo numérico: aproximadamente 7,1 × 10⁻¹⁵ puntos.
- Las hojas Distancias_km e Indice coinciden con sus CSV dentro de tolerancia numérica.
- 869 etapas están sin_clasificar. No existe hoja de comparaciones por pares;
  la hoja Etapas está vacía de observaciones válidas, como corresponde.
- El control del Excel registra 14 reparaciones en proyectos y 112 en capas ambientales,
  sin geometrías vacías registradas. No se inspeccionaron las geometrías reparadas.
- La prueba sintética del código pasó, incluido el control de dependencia por proyecto.

## Descriptivos del índice

| Medida | Valor |
|---|---:|
| n | 869 |
| Media | 29,4457422325 |
| Desviación estándar muestral | 16,645275 aprox. |
| Mínimo | 0 |
| Q25 | 17,475 |
| Mediana | 27,15 |
| Q75 | 40,20 |
| Máximo | 83,675 |
| n con índice cero | 17 |

Mayor cercanía ponderada observada: POL_371, División Andina (83,675);
POL_372, Los Bronces (77,25). Esto no demuestra daño ni incumplimiento.

Las medianas descriptivas por región difieren: Metropolitana 59,5375 y
Antofagasta 9,525. No se hizo una prueba entre regiones ni entre etapas.

## Alcance

Esta revisión verifica la consistencia tabular del cálculo y la metodología implementada.
No acredita exactitud espacial de las distancias, cobertura de las fuentes ni precisión
posicional de los polígonos. Para esa revisión se requieren las capas originales y
validación cartográfica independiente, especialmente cerca de los umbrales.
