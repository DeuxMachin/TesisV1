import os
from flask import Blueprint, render_template, request
from application.services.foldseek_data_fetch import FoldSeekDataFetch
from application.services.uniprot_data_fetch import UniProtDataFetch
from application.services.alignment_processor import procesar_estructura_foldseek
from application.services.py3dmol_service import Py3DMolService  # Nuevo servicio
import tempfile

foldseek_bp = Blueprint('foldseek', __name__, template_folder="../templates")

# Crear directorio temporal si no existe
temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "temp")
os.makedirs(temp_dir, exist_ok=True)

db_path = os.path.join("database", "proteins_discovery.db")
foldseek_fetcher = FoldSeekDataFetch(db_path)
uniprot_fetcher = UniProtDataFetch(db_path)
py3dmol_service = Py3DMolService()  # Nuevo servicio

def procesar_estructura_uniprot(alignment_id, db_path):
    """
    Procesa una estructura de UniProt para visualización.
    
    Args:
        alignment_id (int): ID del alineamiento en UniProt
        db_path (str): Ruta de la base de datos
    
    Returns:
    
        dict: Datos procesados de la estructura
    """
    print(f"Procesando UniProt ID: {alignment_id}")
    # Obtener detalles del alineamiento
    details = uniprot_fetcher.get_uniprot_alignment_details(int(alignment_id))
    if not details:
        return {
            "ref_pdb": None, 
            "aligned_pdb": None,
            "alineamiento_principal": None,
            "zonas_alineadas": []
        }
    
    # Procesar alineamiento principal
    similarity_value = float(details.get("similarity", 0))
    if (similarity_value > 1):
        formatted_similarity = round(similarity_value, 2)
    else:
        formatted_similarity = round(similarity_value * 100, 2)
        
    alineamiento_principal = {
        "similarity": formatted_similarity,
        "reference": details.get("seq_ref", ""),
        "match": details.get("alignment_match", ""),
        "target": details.get("seq", "")
    }
    
    # Procesar zonas alineadas - limitando estrictamente a 4 zonas
    import sqlite3  # Asegurarnos de importar sqlite3 aquí
    
    # Tomar solo los primeros 4 elementos
    reference_zone_ids = details.get("reference_zone_ids", [])[:4]
    aligned_sequences = details.get("aligned_sequences", [])[:4]
    zone_matches = details.get("zone_matches", [])[:4]
    
    zonas_alineadas = []
    
    # Obtener las zonas de referencia
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        try:
            # Crear un diccionario que mapee IDs de zona a números de zona
            zone_numbers = {}
            for i, zone_id in enumerate(reference_zone_ids):
                if zone_id and zone_id.strip():
                    try:
                        cursor.execute("""
                            SELECT zone_number, sequence_fragment
                            FROM ReferenceZones
                            WHERE zone_id = ?
                        """, (int(zone_id),))
                        result = cursor.fetchone()
                        if result and i < len(aligned_sequences) and i < len(zone_matches):
                            zonas_alineadas.append({
                                "ref": result[1],
                                "match": zone_matches[i],
                                "target": aligned_sequences[i]
                            })
                    except (ValueError, TypeError):
                        continue
                
                # Salir temprano una vez que tenemos 4 zonas
                if len(zonas_alineadas) >= 4:
                    break
        except Exception as e:
            print(f"Error procesando zonas: {e}")
    
    # Si hay menos de 4 zonas, rellenar con datos vacíos
    while len(zonas_alineadas) < 4:
        zonas_alineadas.append({
            "ref": "",
            "match": "",
            "target": ""
        })
    
    print(f"UniProt: Se procesaron {len(zonas_alineadas)} zonas alineadas (limitadas a 4)")
    return {
        "ref_pdb": details.get("reference_pdb"),
        "aligned_pdb": details.get("aligned_pdb"),
        "alineamiento_principal": alineamiento_principal,
        "zonas_alineadas": zonas_alineadas[:4]  # Asegurarnos de limitar a exactamente 4 zonas
    }

@foldseek_bp.route("/", methods=["GET", "POST"])
def index():
    selected_source = request.form.get("source", "")
    selected_id = request.form.get("structure_id")
    ref_pdb, aligned_pdb = None, None
    alignment_main = None
    aligned_zones = []
    viewer_html = None  # Nuevo para almacenar el HTML del visualizador
    mutation_viewer_html = None  # Nuevo para el visualizador de mutaciones

    foldseek_structures = foldseek_fetcher.get_foldseek_structures()
    uniprot_structures = uniprot_fetcher.get_uniprot_structures()

    show_structures = False
    res_seq = {}
    zones_matches = []

    if request.method == "POST":
        selected_source = request.form.get("source", "")
        selected_id = request.form.get("structure_id")
        show_structures = request.form.get("show_structures") == "yes"

        if selected_source and selected_id:
            try:
                if selected_source == "foldseek":
                    # Usar el procesador para FoldSeek
                    resultado = procesar_estructura_foldseek(int(selected_id), db_path)
                    ref_pdb = resultado["ref_pdb"]
                    aligned_pdb = resultado["aligned_pdb"]
                    alignment_main = resultado["alineamiento_principal"]
                    aligned_zones = resultado["zonas_alineadas"]
                    
                    # Si se solicita mostrar estructuras, crear el visualizador
                    if show_structures:
                        viewer_html = py3dmol_service.create_protein_viewer(ref_pdb, aligned_pdb)
                        
                        # También crear un visualizador de mutaciones si hay datos disponibles
                        # (Esto se puede adaptar según sea necesario)
                        mutation_viewer_html = py3dmol_service.create_mutation_visualization(
                            aligned_pdb,
                            res_seq=res_seq,
                            res_zone_seq=zones_matches
                        )
                        
                elif selected_source == "uniprot":
                    # Usar el procesador para UniProt
                    resultado = procesar_estructura_uniprot(int(selected_id), db_path)
                    ref_pdb = resultado["ref_pdb"]
                    aligned_pdb = resultado["aligned_pdb"]
                    alignment_main = resultado["alineamiento_principal"]
                    aligned_zones = resultado["zonas_alineadas"]
                    
                    # Si se solicita mostrar estructuras, crear el visualizador
                    if show_structures:
                        viewer_html = py3dmol_service.create_protein_viewer(ref_pdb, aligned_pdb)
                        
                        # También crear un visualizador de mutaciones si hay datos disponibles
                        mutation_viewer_html = py3dmol_service.create_mutation_visualization(
                            aligned_pdb,
                            res_seq=res_seq,
                            res_zone_seq=zones_matches
                        )
            except Exception as e:
                print(f"Error retrieving structure: {e}")
                ref_pdb, aligned_pdb = None, None
                alignment_main = None
                aligned_zones = []

    # Construir visualizadores con datos de secuencia y zona
    if request.method == "POST" and selected_source and selected_id and show_structures:
        try:
            # Si se solicita mostrar estructuras, construir visualizador principal
            if show_structures:
                # Obtener datos de residuos para FoldSeek
                if selected_source == "foldseek" and aligned_pdb:
                    # Procesar datos de residuos y zonas
                    residue_info, count, resids = py3dmol_service.get_residue_info(aligned_pdb)
                    
                    # Construir mapeo de residuos a secuencia
                    res_seq = {}
                    if resultado and "alineamiento_principal" in resultado:
                        alignment_match = resultado["alineamiento_principal"].get("match", "")
                        target_aligned = resultado["alineamiento_principal"].get("target", "")
                        
                        for i in range(min(len(resids), len(target_aligned), len(alignment_match))):
                            if i < len(resids) and resids[i]:
                                res_seq[resids[i][0]] = (target_aligned[i], alignment_match[i])
                    
                    # Construir información de zonas
                    zones_matches = []
                    for i, zona in enumerate(aligned_zones):
                        if zona["ref"] and zona["match"] and zona["target"]:
                            zone_residues = py3dmol_service.get_zone_residues(
                                aligned_pdb, 
                                zona["target"], 
                                resultado["alineamiento_principal"].get("target", "")
                            )
                            if zone_residues:
                                zone_matches = [(zone_residues[j], zona["match"][j]) 
                                               for j in range(min(len(zone_residues), len(zona["match"])))]
                                zones_matches.append({
                                    'zone_number': i+1,
                                    'residues': zone_residues,
                                    'matches': zone_matches,
                                    'sequence': zona["target"],
                                    'match_pattern': zona["match"]
                                })
                
                # Crear visualizador principal
                viewer_html = py3dmol_service.create_protein_viewer(ref_pdb, aligned_pdb)
                
                # Crear visualizador de mutaciones
                mutation_viewer_html = py3dmol_service.create_mutation_visualization(
                    aligned_pdb,
                    res_seq=res_seq,
                    res_zone_seq=zones_matches
                )
                
        except Exception as e:
            print(f"Error retrieving structure: {e}")
            ref_pdb, aligned_pdb = None, None
            alignment_main = None
            aligned_zones = []

    return render_template(
        "foldseek_selector.html", 
        foldseek_structures=foldseek_structures,
        uniprot_structures=uniprot_structures,
        selected_source=selected_source,
        selected_id=selected_id,
        ref_pdb=ref_pdb,
        aligned_pdb=aligned_pdb,
        show_structures=show_structures,
        alignment_main=alignment_main,
        aligned_zones=aligned_zones,
        viewer_html=viewer_html,  # Nuevo - HTML del visualizador
        mutation_viewer_html=mutation_viewer_html  # Nuevo - HTML del visualizador de mutaciones
    )
