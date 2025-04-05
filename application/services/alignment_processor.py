import sqlite3

def procesar_estructura_foldseek(alignment_detail_id: int, db_path: str) -> dict:
    print(f"Procesando FoldSeek ID: {alignment_detail_id}")
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
            print("FoldSeek: No se encontraron datos de alineamiento para el ID proporcionado")
            return {
                "ref_pdb": None, 
                "aligned_pdb": None,
                "alineamiento_principal": None,
                "zonas_alineadas": []
            }

        similarity_value = row[3]

        if similarity_value > 1:
            formatted_similarity = round(similarity_value, 2)
        else:
            formatted_similarity = round(similarity_value * 100, 2)

        alignment_main = {
            "reference": row[0],
            "match": row[1],
            "target": row[2],
            "similarity": formatted_similarity
        }
        aligned_pdb = row[4]
        ref_pdb = row[5]

        # Comprobemos si el problema está en la consulta SQL
        # Primero veamos si hay zonas alineadas para este alineamiento:
        cursor.execute("""
            SELECT COUNT(*) FROM FoldSeekAlignedZones 
            WHERE alignment_detail_id = ?
        """, (alignment_detail_id,))
        count = cursor.fetchone()[0]
        print(f"FoldSeek: Hay {count} zonas alineadas para alignment_detail_id={alignment_detail_id}")

        if count == 0:
            # No hay zonas, intentemos ver todas las zonas de alineamiento en la BD
            cursor.execute("SELECT COUNT(*) FROM FoldSeekAlignedZones")
            total_count = cursor.fetchone()[0]
            print(f"FoldSeek: Hay un total de {total_count} zonas alineadas en la base de datos")
            
            # Ver si el problema es que no hay reference_zone_id válidos
            cursor.execute("""
                SELECT 
                    faz.fragment, 
                    faz.match, 
                    faz.reference_zone_id
                FROM FoldSeekAlignedZones faz
                WHERE faz.alignment_detail_id = ?
                LIMIT 4
            """, (alignment_detail_id,))
            
            raw_zones = cursor.fetchall()
            print(f"FoldSeek: Encontradas {len(raw_zones)} zonas sin JOIN con reference_zone_id")
            
            zonas = []
            for rz in raw_zones:
                fragment = rz[0] if rz[0] else ""
                match = rz[1] if rz[1] else ""
                ref_zone_id = rz[2]
                
                ref_seq = ""
                if ref_zone_id:
                    cursor.execute("""
                        SELECT sequence_fragment FROM ReferenceZones 
                        WHERE zone_id = ?
                    """, (ref_zone_id,))
                    ref_result = cursor.fetchone()
                    if ref_result:
                        ref_seq = ref_result[0]
                    else:
                        print(f"FoldSeek: No se encontró secuencia de referencia para zone_id={ref_zone_id}")
                
                zonas.append((ref_seq, match, fragment))
        else:
            # Hay zonas, intentemos la consulta normal
            cursor.execute("""
                SELECT 
                    rz.sequence_fragment, 
                    faz.match, 
                    faz.fragment
                FROM FoldSeekAlignedZones faz
                JOIN ReferenceZones rz ON faz.reference_zone_id = rz.zone_id
                WHERE faz.alignment_detail_id = ? 
                LIMIT 4;
            """, (alignment_detail_id,))
            
            zonas = cursor.fetchall()
            print(f"FoldSeek: Se encontraron {len(zonas)} zonas con JOIN")

        # Crear las zonas alineadas sólo con los datos reales
        aligned_zones = []
        for zona in zonas:
            aligned_zones.append({
                "ref": zona[0] if zona[0] else "",
                "match": zona[1] if zona[1] else "",
                "target": zona[2] if zona[2] else ""
            })
            
        
        while len(aligned_zones) < 4:
            aligned_zones.append({
                "ref": "No disponible para esta estructura",
                "match": "",
                "target": ""
            })

    print(f"FoldSeek: Se procesaron {len(aligned_zones)} zonas alineadas")
    return {
        "ref_pdb": ref_pdb,
        "aligned_pdb": aligned_pdb,
        "alineamiento_principal": alignment_main,
        "zonas_alineadas": aligned_zones
    }
