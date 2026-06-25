# JobHunter

Pipeline local de búsqueda de empleo que scrapeea ofertas de trabajo, las filtra con IA según tu CV, adapta tu CV para cada oferta y genera una carta de presentación — sin APIs externas ni costos.

---

## Requisitos previos

- **Python 3.10+** — [python.org/downloads](https://www.python.org/downloads/)
- **Ollama** — motor de LLM local. Descargar en [ollama.com](https://ollama.com/)

Verificar que están instalados:

```powershell
python --version
ollama --version
```

---

## Instalación

### 1. Clonar/descargar el proyecto

```powershell
cd C:\Users\TuUsuario\Downloads
# descomprimir o clonar el repo aquí
cd huntarr
```

### 2. Crear entorno virtual e instalar dependencias

```powershell
python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
pip install python-jobspy --no-deps
```

> **Nota:** `python-jobspy` se instala con `--no-deps` porque su dependencia `numpy==1.26.3` no tiene wheel para Python 3.12+. Las dependencias reales se instalan por separado.

### 3. Descargar los modelos de Ollama

```powershell
ollama pull deepseek-r1:8b
ollama pull phi3.5
```

- `deepseek-r1:8b` (~5 GB) — modelo de razonamiento, usado para puntuar las ofertas
- `phi3.5` (~2.2 GB) — modelo de escritura, usado para adaptar CV y generar cartas

> Ollama debe estar corriendo en segundo plano (`ollama serve`) o iniciarse automáticamente con el sistema.

### 4. Colocar tu CV

Copia tu CV en formato PDF a:

```
matcher/cv_base.pdf
```

El pipeline lo lee automáticamente en el primer run y extrae tu perfil (nombre, skills, experiencia, etc.) guardándolo en `profile.json`. Los runs siguientes usan el caché.

---

## Configuración

### Modelos (`config.yaml` en la raíz)

```yaml
modelos:
  filtro: "deepseek-r1:8b"   # scoring de ofertas
  escritura: "phi3.5"         # CV adaptado, cartas, extracción de perfil
```

### Búsqueda (`scraper/config.yaml`)

```yaml
ubicacion: "Chile"
horas_atras: 168              # ofertas de los últimos 7 días
resultados_por_termino: 25    # máx. resultados por término de búsqueda
fuentes:
  - indeed

terminos_busqueda:
  - "data engineer"
  - "data analyst"
  - "cloud engineer"
  - "ingeniero de datos"
  - "analista de datos"
  - "python developer"
  - "analista bi"
  - "cloud aws"
  - "data junior"
```

Puedes agregar o quitar términos de búsqueda según tu perfil.

### Filtro (`filter/config.yaml`)

```yaml
score_minimo: 55   # ofertas con score menor a este se descartan
```

---

## Uso

### Correr el pipeline completo

```powershell
.venv\Scripts\activate
python pipeline.py
```

El pipeline realiza 5 pasos:

1. **Carga tu perfil** desde `profile.json` (o lo extrae del PDF si no existe)
2. **Scrapeea ofertas** en Indeed Chile según los términos configurados
3. **Filtra con IA** — puntúa cada oferta del 0 al 100 según tu perfil
4. **Genera CV y carta** para cada oferta aprobada (score >= `score_minimo`)
5. **Genera un reporte** diario en `output/DIARIO_YYYY-MM-DD.md`

### Outputs generados

```
output/
  DIARIO_2025-05-05.md        ← reporte del día (ofertas aprobadas + descartadas)
  cvs/
    cv_abc123def456.md        ← CV adaptado en Markdown
    cv_abc123def456.html      ← CV adaptado en HTML (para imprimir como PDF)
  cartas/
    carta_abc123def456.md     ← carta de presentación
```

### Actualizar el estado de una postulación

Después de postular a una oferta, actualiza su estado para hacer seguimiento:

```powershell
python update_estado.py <id_oferta> <estado>
```

**Estados disponibles:** `pendiente` | `postulado` | `descartado` | `en_proceso` | `rechazado`

El `id_oferta` lo encuentras en el DIARIO o en `state.json`. Si no recuerdas el ID, corre el comando sin argumentos para ver la lista:

```powershell
python update_estado.py
```

### Resetear el estado (para re-procesar ofertas)

```powershell
Set-Content -Path state.json -Value '{"procesadas":[],"postuladas":[]}' -Encoding utf8
Set-Content -Path jobs.json -Value '[]' -Encoding utf8
```

---

## Re-extraer el perfil desde el CV

Si cambias el CV o quieres actualizar el perfil extraído:

```powershell
Remove-Item profile.json
python pipeline.py
```

---

## Solución de problemas

| Problema                           | Solución                                                                              |
| ---------------------------------- | -------------------------------------------------------------------------------------- |
| `ollama: command not found`      | Instalar Ollama desde ollama.com o asegurarse que esté en el PATH                     |
| `Error 404` al llamar modelo     | El nombre del modelo en `config.yaml` no coincide. Verificar con `ollama list`     |
| Pipeline muy lento                 | Normal —`deepseek-r1:8b` tarda ~30s por oferta. Con 10 ofertas filtradas son ~5 min |
| `FileNotFoundError: cv_base.pdf` | Copiar tu CV a `matcher/cv_base.pdf`                                                 |
| Scores todos iguales (~60)         | Usar `deepseek-r1:8b` como modelo de filtro, no `phi3.5`                           |
| `jobs.json` da error de JSON     | Correr el reset de estado descrito arriba                                              |
