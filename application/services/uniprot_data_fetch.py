import sqlite3
import os
import zipfile
from datetime import datetime

class UniProtDataFetch():
    def __init__(self, db_path):
        self.db_path = db_path
    
    def get_uniprot_structures(self):
        """
        Obtiene las estructuras disponibles de UniProt desde la vista uniprot_summary_view.

        Args:
            database_path (str): Ruta de la base de datos.

        Returns:
            list: Lista de diccionarios con las estructuras disponibles.
        """
        query = """
            SELECT 
                p.accession_number,
                p.name AS protein_name,
                a.alignment_id,
                ts.has_pdb,
                ts.has_alphafold
            FROM Proteins p
            JOIN Alignments a ON p.accession_number = a.source_id
            JOIN ThreeDStructures ts ON p.accession_number = ts.accession_number
            WHERE a.alignment_id IN (
                SELECT DISTINCT alignment_id 
                FROM AlignedZones 
                WHERE vsd_valido = 1
            )
            AND (a.pdb IS NOT NULL)
			ORDER BY has_pdb DESC;
            """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()

                # Convertir los resultados en una lista de diccionarios
                structures = [
                    {
                        "accession_number": row[0],
                        "protein_name": row[1],
                        "alignment_id": row[2],
                        "has_pdb": row[3],
                        "has_alphafold": row[4]
                    }
                    for row in rows
                ]
                return structures
        except Exception as e:
            print(f"Error fetching UniProt structures: {e}")
            return []

    def get_uniprot_alignment_details(self, alignment_id):
        """
        Obtiene los detalles de alineamiento de UniProt desde la vista uniprot_summary_view.

        Args:
            database_path (str): Ruta de la base de datos.
            alignment_id (int): ID del alineamiento.

        Returns:
            dict: Detalles del alineamiento y zonas alineadas.
        """
        query = """
            SELECT 
                p.sequence AS protein_sequence,
                a.adjusted_score,
                a.similarity,
                a.seq_ref,
                a.seq,
                a.match AS alignment_match,
                r.pdb AS reference_pdb,
                a.pdb,
                a.success_info,
                GROUP_CONCAT(az.aligned_zone_id, ', ') AS aligned_zone_ids,
                GROUP_CONCAT(az.reference_zone_id, ', ') AS reference_zone_ids,
                GROUP_CONCAT(az.aligned_sequence, ' | ') AS aligned_sequences,
                GROUP_CONCAT(az.match, ', ') AS zone_matches,
                GROUP_CONCAT(az.hydrophobicity_aligned, ', ') AS hydrophobicity_aligned,
                GROUP_CONCAT(az.volume_aligned, ', ') AS volume_aligned,
                GROUP_CONCAT(az.delta_hydrophobicity, ', ') AS delta_hydrophobicity,
                GROUP_CONCAT(az.delta_volume, ', ') AS delta_volume,
                GROUP_CONCAT(az.tipo_carga, ', ') AS tipo_carga,
                GROUP_CONCAT(az.cargas, '| ') AS cargas,
                GROUP_CONCAT(az.cargas_reference, '| ') AS cargas_reference,
                p.name,
                p.full_name,
                p.organism,
                p.gene,
                p.description,
                p.sequence
            FROM Proteins p
            JOIN Alignments a ON p.accession_number = a.source_id
            JOIN AlignedZones az ON a.alignment_id = az.alignment_id
            JOIN ThreeDStructures ts ON p.accession_number = ts.accession_number
            JOIN ReferenceSequences r ON a.reference_sequence_id = r.reference_sequence_id
            WHERE a.alignment_id = ?
            GROUP BY a.alignment_id, p.accession_number;
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (alignment_id,))
                row = cursor.fetchone()
                if row:
                    return {
                        "protein_sequence": row[0],
                        "adjusted_score": row[1],
                        "similarity": row[2],
                        "seq_ref": row[3],
                        "seq": row[4],
                        "alignment_match": row[5],
                        "reference_pdb": row[6],
                        "aligned_pdb": row[7],
                        "success_info": row[8],
                        "aligned_zone_ids": row[9].split(", "),
                        "reference_zone_ids": row[10].split(", "),
                        "aligned_sequences": row[11].split(" | "),
                        "zone_matches": row[12].split(", "),
                        "hydrophobicity_aligned": row[13].split(", "),
                        "volume_aligned": row[14].split(", "),
                        "delta_hydrophobicity": row[15].split(", "),
                        "delta_volume": row[16].split(", "),
                        "tipo_carga": row[17].split(", "),
                        "cargas": row[18].split("| "),
                        "cargas_reference": row[19].split("| "),
                        "name": row[20],
                        "full_name": row[21],
                        "organism": row[22],
                        "gene": row[23],
                        "description": row[24],
                        "sequence": row[25]
                    }
                return {}
        except Exception as e:
            print(f"Error fetching UniProt alignment details: {e}")
            return {}
        
    def get_zone_numbers(self, zone_ids):
        """
        Obtiene los números de las zonas alineadas a partir de sus IDs.
        Args:
            database_path (str): Ruta al archivo de la base de datos.
            zone_ids (list): Lista de IDs de zona.
        Returns:
            list: Lista de números de zonas.
        """
        query = """
            SELECT zone_number, sequence_fragment
            FROM ReferenceZones
            WHERE zone_id = ?
        """
        try:
            zone_numbers = {}
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                for zone_id in zone_ids:
                    cursor.execute(query, (zone_id,))
                    result = cursor.fetchone()
                    if result:
                        zone_numbers[result[0]] = result[1]
            return zone_numbers
        except Exception as e:
            print(f"Error fetching zone numbers: {e}")
            return []

    def create_uniprot_download_package(self, alignment_id, ref_pdb, aligned_pdb, combined_pdb_path):
        """
        Crea un paquete ZIP para alineamientos UniProt.

        Args:
            database_path (str): Ruta de la base de datos.
            alignment_id (int): ID del alineamiento.
            ref_pdb (str): Contenido del archivo PDB de referencia.
            aligned_pdb (str): Contenido del archivo PDB alineado.
            combined_pdb_path (str): Ruta del archivo combinado.

        Returns:
            str: Ruta del archivo ZIP creado.
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = os.path.join(os.path.dirname(combined_pdb_path), f"uniprot_data_{timestamp}.zip")

            # Obtener detalles del alineamiento
            alignment_details = self.get_uniprot_alignment_details(alignment_id)
            if not alignment_details:
                return None
            success_info = alignment_details["success_info"].split(", ")

            # Crear contenido informativo
            info_content = f"""UniProt Alignment Information
==============================
Alignment ID: {alignment_id}
Protein Name: {alignment_details["name"]}
Full Name   : {alignment_details["full_name"]}
Organism    : {alignment_details["organism"]}
Gene        : {alignment_details["gene"]}
Structure   : {success_info[0]}
ID {"PDB" if success_info[0] == "PDB" else "AlphaFold"}: {success_info[1]}
{"Resolution" if success_info[0] == "PDB" else "Download Link"}: {success_info[2]}

Sequence Alignment
==============================
Reference: {alignment_details["seq_ref"]}
Match    : {alignment_details["alignment_match"]}
Target   : {alignment_details["seq"]}

Zone Analysis
==============================
"""
            
            references_zones_ids = alignment_details["reference_zone_ids"]  
            fragment = alignment_details["aligned_sequences"]
            zone_match = alignment_details["zone_matches"]
            hydrophobicity = alignment_details["hydrophobicity_aligned"]
            volume = alignment_details["volume_aligned"]
            delta_hydrophobicity = alignment_details["delta_hydrophobicity"]
            delta_volume = alignment_details["delta_volume"]
            tipo_carga = alignment_details["tipo_carga"]
            cargas = alignment_details["cargas"]
            reference_charges = alignment_details["cargas_reference"]
            for i in range(len(fragment)):
                zone_data = self.get_zone_numbers(references_zones_ids[i])
                zone_number = list(zone_data.keys())[0]
                zone_seq= zone_data[list(zone_data.keys())[0]]
                info_content += f"""
Zone {zone_number}:
-------------
Reference Zone      : {zone_seq}
Match               : {zone_match}
Fragment            : {fragment}
Hydrophobicity      : {hydrophobicity}
Volume              : {volume}
Delta Hydrophobicity: {delta_hydrophobicity}
Delta Volume        : {delta_volume}
Charge Type         : {tipo_carga}
Reference Charges   : {reference_charges}
Target Charges      : {cargas}
"""
        
            # Crear archivo ZIP
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.writestr("reference.pdb", ref_pdb)
                zipf.writestr("aligned.pdb", aligned_pdb)
                with open(combined_pdb_path, 'r') as f:
                    zipf.writestr("combined.pdb", f.read())
                zipf.writestr("alignment_info.txt", info_content)

            return zip_path
    
        except Exception as e:
            print(f"Error creating UniProt download package: {e}")
            return None