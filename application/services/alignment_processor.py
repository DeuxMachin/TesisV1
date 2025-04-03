import sqlite3

def procesar_estructura_foldseek(alignment_detail_id: int, db_path: str) -> dict:
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        # Obtener alineamiento principal
        cursor.execute("""
            SELECT fad.reference_aligned, fad.match, fad.target_aligned, fad.similarity, fad.pdb, rz.pdb 
            FROM FoldSeekAlignmentDetails fad
            JOIN FoldSeek f ON fad.foldseek_id = f.foldseek_id
            JOIN ReferenceSequences rz ON f.id_referencia = rz.reference_sequence_id
            WHERE fad.alignment_detail_id = ?
        """, (alignment_detail_id,))
        row = cursor.fetchone()

        if not row:
            raise ValueError("No se encontraron datos de alineamiento para el ID proporcionado")

        alignment_main = {
            "reference": row[0],
            "match": row[1],
            "target": row[2],
            "similarity": round(row[3] * 100, 2)
        }
        aligned_pdb = row[4]
        ref_pdb = row[5]

        # Obtener zonas alineadas
        cursor.execute("""
            SELECT zona_referencia, match, zona_objetivo
            FROM FoldSeekAlignedZones
            WHERE alignment_detail_id = ? AND vsd_valido = 1
            ORDER BY id_zona;
        """, (alignment_detail_id,))
        zonas = cursor.fetchall()

        aligned_zones = [{
            "ref": z[0],
            "match": z[1],
            "target": z[2]
        } for z in zonas]

    return {
        "ref_pdb": ref_pdb,
        "aligned_pdb": aligned_pdb,
        "alineamiento_principal": alignment_main,
        "zonas_alineadas": aligned_zones
    }
