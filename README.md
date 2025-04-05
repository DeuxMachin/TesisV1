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
│   │   ├── structure_processor.py   # Procesamiento de estructuras
│   │   ├── uniprot_data_fetch.py    # Obtención de datos de UniProt
│   │   └── vsd_protein_processor.py # Procesamiento específico de VSD
│   ├── static/                  # Archivos estáticos
│   │   └── css/                 # Hojas de estilo
│   │       └── styles.css       # Estilo principal
│   └── templates/               # Plantillas HTML
│       ├── foldseek_list.html   # Lista de estructuras FoldSeek
│       ├── foldseek_selector.html # Selector de visualización
│       └── foldseek_viewer.html # Visualizador 3D
├── database/                    # Manejo de base de datos
│   ├── create_db.py            # Script para crear la BD
│   └── proteins_discovery.db   # Base de datos SQLite (gitignored)
├── config.py                    # Configuración global
├── requirements.txt             # Dependencias del proyecto
└── run.py                       # Punto de entrada
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
- **Visualización 3D**: 3Dmol.js
- **Procesamiento PDB**: BioPython, MDAnalysis, PyMOL
- **Análisis de secuencias**: Alineamiento de secuencias y análisis de similitud

## 🛠️ Herramientas principales

- **Flask**: Framework web ligero para Python
- **SQLite**: Base de datos relacional incorporada
- **3Dmol.js**: Biblioteca de visualización molecular JavaScript
- **MDAnalysis**: Herramienta de análisis de dinámica molecular
- **PyMOL**: Sistema de visualización molecular

## 📝 Detalles de implementación

- Diseño modular siguiendo los principios SOLID
- Implementación de patrones de diseño como Repositorio y Servicio
- Uso de blueprints de Flask para una mejor organización del código
- Consultas SQL optimizadas para un rendimiento eficiente
- Interfaz de usuario intuitiva con retroalimentación visual clara

## 🔄 Migración desde Streamlit

Este proyecto es una migración de una aplicación Streamlit a Flask, ofreciendo la ventaja de un mayor control sobre la interfaz de usuario y mejor rendimiento para visualizaciones complejas de proteínas.

## 📎 Notas

- La base de datos contiene estructuras proteicas previamente procesadas y alineadas
- Los archivos PDB se cargan dinámicamente según sea necesario
- El análisis VSD (Voltage Sensing Domain) es específico para proteínas con dominios sensores de voltaje

---

Desarrollado con ❤️ para el análisis y visualización de estructuras proteicas.