# Proyecto de Visualización y Análisis de Proteínas con Flask

Este proyecto implementa una aplicación web basada en Flask para la visualización y análisis de proteínas utilizando datos de UniProt y FoldSeek. El sistema permite visualizar estructuras proteicas en 3D, analizar alineamientos de secuencias y explorar diversas características moleculares.

## 🧬 Características principales

- **Visualización 3D interactiva** de estructuras proteicas con 3Dmol.js
- **Análisis de alineamientos** entre proteínas de referencia y objetivo
- **Integración con dos fuentes de datos**:
  - **FoldSeek**: para búsquedas estructurales
  - **UniProt**: para información de proteínas
- **Visualización de zonas alineadas** y detalles específicos de la estructura
- **Interfaz web responsive** con estilo oscuro moderno

## 🚀 Instalación

1. Clonar el repositorio:
```bash
git clone https://github.com/username/flask-protein-visualization.git
cd flask-protein-visualization
```

2. Crear un entorno virtual e instalar las dependencias:
```bash
conda create -n protein_viz python=3.9
conda activate protein_viz
pip install -r requirements.txt
```

3. Configurar la base de datos:
```bash
python database/create_db.py
```

## 📦 Estructura del proyecto

```
Flask/
├── application/                  # Código principal de la aplicación
│   ├── __init__.py              # Inicialización de la aplicación Flask
│   ├── routes/                  # Controladores de rutas
│   │   ├── foldseek_routes.py   # Rutas para FoldSeek
│   ├── services/                # Servicios de negocio
│   │   ├── alignment_processor.py    # Procesamiento de alineamientos
│   │   ├── cortar_pdb.py            # Manipulación de archivos PDB
│   │   ├── foldseek_data_fetch.py   # Obtención de datos de FoldSeek
│   │   ├── py3dmol_service.py       # Servicio para visualización de mutaciones
│   │   ├── structure_processor.py   # Procesamiento de estructuras
│   │   ├── uniprot_data_fetch.py    # Obtención de datos de UniProt
│   │   └── vsd_protein_processor.py # Procesamiento específico de VSD
│   ├── static/                  # Archivos estáticos
│   │   ├── css/                 # Hojas de estilo
│   │   │   └── styles.css       # Estilo principal
│   │   └── js/                  # Scripts JavaScript
│   │       └── molstar_viewer.js # Visualizador 3D con Mol*
│   └── templates/               # Plantillas HTML
│       ├── foldseek_list.html   # Lista de estructuras FoldSeek
│       ├── foldseek_selector.html # Selector de visualización
│       └── foldseek_viewer.html # Visualizador 3D
├── database/                    # Manejo de base de datos
│   ├── create_db.py            # Script para crear la BD
│   └── proteins_discovery.db   # Base de datos SQLite (gitignored)
├── [config.py](http://_vscodecontentref_/2)                    # Configuración global
├── [requirements.txt](http://_vscodecontentref_/3)             # Dependencias del proyecto
└── [run.py](http://_vscodecontentref_/4)                       # Punto de entrada                     # Punto de entrada
```

## 🔧 Uso

1. Ejecutar la aplicación:
```bash
python run.py
```

2. Abrir el navegador en http://127.0.0.1:5000/ 

3. Seleccionar la fuente de datos (FoldSeek o UniProt)

4. Elegir una estructura proteica para visualizar

5. Utilizar la casilla de verificación para alternar entre la visualización de alineamientos y estructuras 3D

## 🔍 Características técnicas

- **Backend**: Flask con SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Visualización 3D**: Mol* para estructuras completas y py3Dmol para mutaciones
- **Procesamiento PDB**: BioPython, MDAnalysis, PyMOL
- **Análisis de secuencias**: Alineamiento de secuencias y análisis de similitud

## 🛠️ Herramientas principales

- **Flask**: Framework web ligero para Python
- **SQLite**: Base de datos relacional incorporada
- **Mol***: Biblioteca moderna de visualización molecular
- **py3Dmol**: Biblioteca especializada para visualización de mutaciones
- **MDAnalysis**: Herramienta de análisis de dinámica molecular
- **PyMOL**: Sistema de visualización molecular

## 📝 Detalles de implementación y desafíos superados

- **Visualizadores independientes**: Se implementaron dos visualizadores separados para diferentes propósitos:
  - Mol* para visualización general de estructuras proteicas
  - py3Dmol para análisis específico de mutaciones

- **Compatibilidad de APIs**: Se resolvieron problemas de compatibilidad con diferentes versiones de Mol*
  - Implementación de múltiples métodos para manejar cambios en la API
  - Código defensivo para detectar y utilizar los métodos disponibles

- **Renderizado confiable**: Se solucionaron problemas de renderización en el visualizador 3D
  - Mejora en la inicialización del visualizador
  - Manejo adecuado de promesas y secuencia de carga

- **Mapeo secuencia-estructura**: Se implementó un sistema preciso para mapear alineamientos de secuencias a estructuras 3D
  - Identificación correcta de residuos en el espacio 3D
  - Vinculación entre posiciones de secuencia y coordenadas estructurales

## 🔄 Mejoras recientes

1. **Visualización dual**: Implementación de dos visualizadores complementarios:
   - Visualizador de estructuras completas con Mol*
   - Visualizador específico de mutaciones con py3Dmol

2. **Mejora en la gestión de carga**: Sistema robusto de carga y visualización de estructuras proteicas
   - Indicadores de carga durante el procesamiento
   - Manejo de errores con retroalimentación visual

3. **Optimización de rendimiento**: Mejoras en la carga y visualización de estructuras complejas
   - Carga secuencial para evitar problemas de memoria
   - Códigos de colores intuitivos para diferenciar estructuras

4. **Experiencia de usuario mejorada**: Interfaz más intuitiva y reactiva
   - Control granular sobre los elementos visualizados
   - Retroalimentación clara durante la interacción

## 🔄 Migración desde Streamlit

Este proyecto es una migración de una aplicación Streamlit a Flask, ofreciendo la ventaja de un mayor control sobre la interfaz de usuario y mejor rendimiento para visualizaciones complejas de proteínas.

## 📎 Notas

- La base de datos contiene estructuras proteicas previamente procesadas y alineadas
- Los archivos PDB se cargan dinámicamente según sea necesario
- El análisis VSD (Voltage Sensing Domain) es específico para proteínas con dominios sensores de voltaje

---

