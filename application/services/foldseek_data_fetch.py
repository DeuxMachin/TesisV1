import sqlite3
import os
import zipfile
from datetime import datetime

class FoldSeekDataFetch():
    def __init__(self, db_path):
        self.db_path = db_path
    def get_foldseek_structures(self):
        """
        Obtiene las estructuras de FoldSeek disponibles desde la vista foldseek_summary_view.

        Args:
            database_path (str): Ruta al archivo de la base de datos.

        Returns:
            list: Lista de diccionarios con las estructuras disponibles.
        """
        query = """
            SELECT 
                f.database_name,
                f.alphafold_pdb,
                fad.alignment_detail_id
            FROM FoldSeek f
            JOIN FoldSeekAlignmentDetails fad ON f.foldseek_id = fad.foldseek_id
            JOIN FoldSeekAlignedZones faz ON fad.alignment_detail_id = faz.alignment_detail_id
            JOIN ReferenceSequences rz ON f.id_referencia = rz.reference_sequence_id
            WHERE f.database_name != 'gmgcl_id'
            AND fad.pdb IS NOT NULL
            AND fad.alignment_detail_id IN (
                SELECT DISTINCT faz.alignment_detail_id 
                FROM FoldSeekAlignedZones faz
                WHERE faz.vsd_valido = 1
            )
            GROUP BY f.foldseek_id, fad.alignment_detail_id;
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                rows = cursor.fetchall()

                # Convertir los resultados en una lista de diccionarios
                structures = [
                    {
                        "database_name": row[0],
                        "target": row[1],
                        "alignment_detail_id": row[2],
                        
                    }
                    for row in rows
                ]
                
                return structures
        except Exception as e:
            print(f"Error fetching FoldSeek structures: {e}")
            return []
    
            
    def get_alignment_details(self, alignment_detail_id):
        """
        Obtiene los detalles del alineamiento, incluidas las zonas alineadas.

        Args:
            database_path (str): Ruta al archivo de la base de datos.
            alignment_detail_id (int): ID del detalle de alineamiento.

        Returns:
            dict: Detalles del alineamiento y sus zonas alineadas.
        """
        query = """
            SELECT 
                fad.reference_aligned,
                fad.match AS alignment_match,
                fad.target_aligned,
                fad.similarity,
                fad.pdb,
                rz.pdb AS reference_pdb,
                GROUP_CONCAT(faz.fragment, ' | ') AS aligned_fragments,
                GROUP_CONCAT(faz.match, ', ') AS fragment_matches,
                GROUP_CONCAT(faz.hydrophobicity, ', ') AS fragment_hydrophobicities,
                GROUP_CONCAT(faz.volume, ', ') AS fragment_volumes,
                GROUP_CONCAT(faz.delta_hydrophobicity, ', ') AS delta_hydrophobicities,
                GROUP_CONCAT(faz.delta_volume, ', ') AS delta_volumes,
                GROUP_CONCAT(faz.tipo_carga, ', ') AS charge_types,
                GROUP_CONCAT(faz.cargas, '| ') AS charges,
                GROUP_CONCAT(faz.cargas_reference, '| ') AS reference_charges,
                GROUP_CONCAT(faz.reference_zone_id, ', ') AS reference_zone_ids
            FROM FoldSeekAlignmentDetails fad
            JOIN FoldSeekAlignedZones faz ON fad.alignment_detail_id = faz.alignment_detail_id
            JOIN FoldSeek f ON fad.foldseek_id = f.foldseek_id
            JOIN ReferenceSequences rz ON f.id_referencia = rz.reference_sequence_id
            WHERE fad.alignment_detail_id = ?
            GROUP BY fad.alignment_detail_id;
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(query, (alignment_detail_id,))
                row = cursor.fetchone()
                if row:
                    return {
                    "reference_aligned": row[0],
                    "alignment_match": row[1],
                    "target_aligned": row[2],
                    "similarity": row[3],
                    "pdb_path": row[4],
                    "reference_pdb_path": row[5],
                    "aligned_fragments": row[6].split(" | ") if row[6] else [],
                    "fragment_matches": row[7].split(", ") if row[7] else [],
                    "fragment_hydrophobicities": row[8].split(", ") if row[8] else [],
                    "fragment_volumes": row[9].split(", ") if row[9] else [],
                    "delta_hydrophobicities": row[10].split(", ") if row[10] else [],
                    "delta_volumes": row[11].split(", ") if row[11] else [],
                    "charge_types": row[12].split(", ") if row[12] else [],
                    "charges": row[13].split("| ") if row[13] else [],
                    "reference_charges": row[14].split("| ") if row[14] else [],
                    "reference_zone_ids": row[15].split(", ") if row[15] else []
                },
                else:
                    return {}
        except Exception as e:
            print(f"Error fetching alignment details: {e}")
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

    def create_download_package_from_view(self, alignment_detail_id, ref_pdb, aligned_pdb, combined_pdb_path):
        """
        Crea un paquete ZIP con datos basados en la vista foldseek_summary_view.

        Args:
            database_path (str): Ruta de la base de datos.
            alignment_detail_id (int): ID del alineamiento.
            ref_pdb (str): Contenido del archivo PDB de referencia.
            aligned_pdb (str): Contenido del archivo PDB alineado.
            combined_pdb_path (str): Ruta del archivo combinado.

        Returns:
            str: Ruta del archivo ZIP creado.
        """
        try:
            # Crear timestamp para un nombre único
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_path = os.path.join(os.path.dirname(combined_pdb_path), f"foldseek_data_{timestamp}.zip")

            # Conectar a la base de datos y obtener datos desde la vista
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Obtener detalles del alineamiento
            query = """
                SELECT 
                    f.database_name, 
                    f.target, 
                    f.taxName, 
                    f.taxId, 
                    f.hyperlink, 
                    fad.similarity, 
                    fad.reference_aligned, 
                    fad.match AS alignment_match, 
                    fad.target_aligned
                FROM FoldSeek f
                JOIN FoldSeekAlignmentDetails fad ON f.foldseek_id = fad.foldseek_id
                WHERE fad.alignment_detail_id = ?;

            """
            cursor.execute(query, (alignment_detail_id,))
            data = cursor.fetchone()
            if not data:
                return None

            db_name, target, taxName, taxId, hyperlink, similarity, ref_aligned, match, target_aligned = data

            # Obtener datos de las zonas alineadas
            zone_query = """
                SELECT 
                    GROUP_CONCAT(faz.reference_zone_id, ', ') AS reference_zone_ids,
                    GROUP_CONCAT(faz.fragment, ' | ') AS aligned_fragments,
                    GROUP_CONCAT(faz.match, ', ') AS fragment_matches,
                    GROUP_CONCAT(faz.hydrophobicity, ', ') AS fragment_hydrophobicities,
                    GROUP_CONCAT(faz.volume, ', ') AS fragment_volumes,
                    GROUP_CONCAT(faz.delta_hydrophobicity, ', ') AS delta_hydrophobicities,
                    GROUP_CONCAT(faz.delta_volume, ', ') AS delta_volumes,
                    GROUP_CONCAT(faz.tipo_carga, ', ') AS charge_types,
                    GROUP_CONCAT(faz.cargas, '| ') AS charges,
                    GROUP_CONCAT(faz.cargas_reference, '| ') AS reference_charges
                FROM FoldSeekAlignedZones faz
                WHERE faz.alignment_detail_id = ?
                GROUP BY faz.alignment_detail_id;

            """
            cursor.execute(zone_query, (alignment_detail_id,))
            zones_data = cursor.fetchall()
            

            zone_numbers_query = """
            SELECT zone_number, sequence_fragment
            FROM ReferenceZones
            WHERE zone_id = ?
            """
            # Crear contenido informativo
            info_content = f"""FoldSeek Alignment Information
==============================
Database: {db_name}
Target: {target}
Similarity: {similarity:.2f}%
Taxonomy Name: {taxName}
Taxonomy ID: {taxId}
Hyperlink: {hyperlink}

Sequence Alignment
==============================
Reference: {ref_aligned}
Match    : {match}
Target   : {target_aligned}

Zone Analysis
==============================
"""
            zone_numbers = []
            for idx, zone in enumerate(zones_data, start=1):
                references_zones_ids, fragment, zone_match, hydrophobicity, volume, delta_hydrophobicity, delta_volume, tipo_carga, cargas, reference_charges = zone
            
            references_zones_ids = references_zones_ids.split(", ")    
            fragment = fragment.split(" | ")
            zone_match = zone_match.split(", ")
            hydrophobicity = hydrophobicity.split(", ")
            volume = volume.split(", ")
            delta_hydrophobicity = delta_hydrophobicity.split(", ")
            delta_volume = delta_volume.split(", ")
            tipo_carga = tipo_carga.split(", ")
            cargas = cargas.split("| ")
            reference_charges = reference_charges.split("| ")
            for i in range(len(fragment)):
                cursor.execute(zone_numbers_query, (references_zones_ids[i],))
                zone_data=(cursor.fetchall()[0])        
                info_content += f"""
Zone {zone_data[0]}:
-------------
Reference Zone : {zone_data[1]}
Match          : {zone_match[i]}
Fragment       : {fragment[i]}
Hydrophobicity : {hydrophobicity[i]}
Volume         : {volume[i]}
Delta Hydrophobicity: {delta_hydrophobicity[i]}
Delta Volume   : {delta_volume[i]}
Charge Type    : {tipo_carga[i]}
Reference Charges: {reference_charges[i]}
Target Charges : {cargas[i]}
"""

            conn.close()
            # Crear archivo ZIP
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # Añadir PDBs de referencia y alineado
                zipf.writestr("reference.pdb", ref_pdb)
                zipf.writestr("aligned.pdb", aligned_pdb)

                # Añadir archivo combinado
                with open(combined_pdb_path, 'r') as f:
                    zipf.writestr("combined.pdb", f.read())

                # Añadir archivo de información
                zipf.writestr("alignment_info.txt", info_content)

            return zip_path

        except Exception as e:
            print(f"Error creating download package: {e}")
            return None