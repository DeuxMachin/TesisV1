import os
from flask import Blueprint, render_template, request
from application.services.foldseek_data_fetch import FoldSeekDataFetch
from application.services.uniprot_data_fetch import UniProtDataFetch
from application.services.alignment_processor import procesar_estructura_foldseek

foldseek_bp = Blueprint('foldseek', __name__, template_folder="../templates")

db_path = os.path.join("database", "proteins_discovery.db")
foldseek_fetcher = FoldSeekDataFetch(db_path)
uniprot_fetcher = UniProtDataFetch(db_path)

def procesar_estructura_uniprot(alignment_id, db_path):
    """
    Procesa una estructura de UniProt para visualización.
    
    Args:
        alignment_id (int): ID del alineamiento en UniProt
        db_path (str): Ruta de la base de datos
    
    Returns:
        dict: Datos procesados de la estructura
    """
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
    alineamiento_principal = {
        "similarity": float(details.get("similarity", 0)),
        "reference": details.get("seq_ref", ""),
        "match": details.get("alignment_match", ""),
        "target": details.get("seq", "")
    }
    
    # Procesar zonas alineadas
    zonas_alineadas = []
    aligned_sequences = details.get("aligned_sequences", [])
    zone_matches = details.get("zone_matches", [])
    for i in range(len(aligned_sequences)):
        if i < len(zone_matches):
            zonas_alineadas.append({
                "ref": "", # Zona de referencia no disponible directamente
                "match": zone_matches[i] if i < len(zone_matches) else "",
                "target": aligned_sequences[i] if i < len(aligned_sequences) else ""
            })
    
    return {
        "ref_pdb": details.get("reference_pdb"),
        "aligned_pdb": details.get("aligned_pdb"),
        "alineamiento_principal": alineamiento_principal,
        "zonas_alineadas": zonas_alineadas
    }

@foldseek_bp.route("/", methods=["GET", "POST"])
def index():
    selected_source = request.form.get("source", "")
    selected_id = request.form.get("structure_id")
    ref_pdb, aligned_pdb = None, None
    alignment_main = None
    aligned_zones = []

    foldseek_structures = foldseek_fetcher.get_foldseek_structures()
    uniprot_structures = uniprot_fetcher.get_uniprot_structures()

    show_structures = False

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
                elif selected_source == "uniprot":
                    # Usar el procesador para UniProt
                    resultado = procesar_estructura_uniprot(int(selected_id), db_path)
                    ref_pdb = resultado["ref_pdb"]
                    aligned_pdb = resultado["aligned_pdb"]
                    alignment_main = resultado["alineamiento_principal"]
                    aligned_zones = resultado["zonas_alineadas"]
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
        aligned_zones=aligned_zones
    )