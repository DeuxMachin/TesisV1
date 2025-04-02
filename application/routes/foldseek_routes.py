import os
from flask import Blueprint, render_template, request
from application.services.foldseek_data_fetch import FoldSeekDataFetch
from application.services.uniprot_data_fetch import UniProtDataFetch

foldseek_bp = Blueprint('foldseek', __name__, template_folder="../templates")

db_path = os.path.join("database", "proteins_discovery.db")
foldseek_fetcher = FoldSeekDataFetch(db_path)
uniprot_fetcher = UniProtDataFetch(db_path)

@foldseek_bp.route("/", methods=["GET", "POST"])
def index():
    selected_source = request.form.get("source")
    selected_id = request.form.get("structure_id")
    ref_pdb, aligned_pdb = None, None

    foldseek_structures = foldseek_fetcher.get_foldseek_structures()
    uniprot_structures = uniprot_fetcher.get_uniprot_structures()

    if selected_source and selected_id:
        try:
            if selected_source == "foldseek":
                details = foldseek_fetcher.get_alignment_details(int(selected_id))
                ref_pdb = details.get("reference_pdb_path")
                aligned_pdb = details.get("pdb_path")
            elif selected_source == "uniprot":
                details = uniprot_fetcher.get_uniprot_alignment_details(int(selected_id))
                ref_pdb = details.get("reference_pdb")
                aligned_pdb = details.get("aligned_pdb")
        except:
            ref_pdb, aligned_pdb = None, None

    return render_template(
        "foldseek_selector.html",
        foldseek_structures=foldseek_structures,
        uniprot_structures=uniprot_structures,
        selected_source=selected_source,
        selected_id=selected_id,
        ref_pdb=ref_pdb,
        aligned_pdb=aligned_pdb
    )