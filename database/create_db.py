import sqlite3
import os

def database_exists(db_name):
    """
    Verifica si la base de datos existe y tiene las tablas necesarias.
    
    Args:
        db_name (str): Nombre del archivo de la base de datos.
    
    Returns:
        bool: True si existe y tiene estructura correcta, False en caso contrario.
    """
    if not os.path.exists(db_name):
        return False
    
    try:
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        
        # Verificar si existe al menos una tabla crítica
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='Proteins'
        """)
        
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    except sqlite3.Error:
        return False

def create_connection(db_name):
    """
    Crea una conexión a la base de datos SQLite.
    
    Args:
        db_name (str): Nombre del archivo de la base de datos.

    Returns:
        sqlite3.Connection: Objeto de conexión a la base de datos.
    """
    try:
        conn = sqlite3.connect(db_name)
        print(f"Conexión a la base de datos '{db_name}' establecida correctamente.")
        return conn
    except sqlite3.Error as e:
        print(f"Error al conectar con la base de datos: {e}")
        raise

def create_table(cursor, create_statement):
    """
    Crea una tabla en la base de datos si no existe.

    Args:
        cursor (sqlite3.Cursor): Cursor para ejecutar comandos SQL.
        create_statement (str): Instrucción SQL para crear la tabla.
    """
    try:
        cursor.execute(create_statement)
        print("Tabla creada o ya existente.")
    except sqlite3.Error as e:
        print(f"Error al crear la tabla: {e}")
        raise

def create_database(db_name, force_create=False):
    """
    Crea la estructura de la base de datos.

    Args:
        db_name (str): Nombre del archivo de la base de datos.
    """
    connection = create_connection(db_name)
    cursor = connection.cursor()
    
    if database_exists(db_name) and not force_create:
        print(f"Base de datos '{db_name}' ya existe y contiene las tablas necesarias.")
        return False

    # Lista de declaraciones SQL para crear tablas
    tables = [
        '''CREATE TABLE IF NOT EXISTS Proteins (
            accession_number TEXT PRIMARY KEY,
            name TEXT,
            full_name TEXT,
            organism TEXT,
            gene TEXT,
            description TEXT,
            sequence TEXT,
            length INTEGER
        );''',

        '''CREATE TABLE IF NOT EXISTS ProteinShortNames (
            short_name_id INTEGER PRIMARY KEY AUTOINCREMENT,
            accession_number TEXT,
            short_name TEXT,
            FOREIGN KEY (accession_number) REFERENCES Proteins (accession_number)
        );''',

        '''CREATE TABLE IF NOT EXISTS ProteinAlternativeNames (
            alt_name_id INTEGER PRIMARY KEY AUTOINCREMENT,
            accession_number TEXT,
            alternative_name TEXT,
            FOREIGN KEY (accession_number) REFERENCES Proteins (accession_number)
        );''',

        '''CREATE TABLE IF NOT EXISTS ReferenceSequences (
            reference_sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_segment TEXT,
            source_protein TEXT,
            pdb TEXT,
            FOREIGN KEY (source_protein) REFERENCES Proteins (accession_number)
        );''',

        '''CREATE TABLE IF NOT EXISTS ReferenceZones (
            zone_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_sequence_id INTEGER,
            zone_number INTEGER,
            sequence_fragment TEXT,
            volume FLOAT,
            hydrophobicity FLOAT,
            FOREIGN KEY (reference_sequence_id) REFERENCES ReferenceSequences (reference_sequence_id)
        );''',

        '''CREATE TABLE IF NOT EXISTS ThreeDStructures (
            structure_id INTEGER PRIMARY KEY AUTOINCREMENT,
            accession_number TEXT,
            has_pdb BOOLEAN,
            has_alphafold BOOLEAN,
            FOREIGN KEY (accession_number) REFERENCES Proteins (accession_number)
        );''',

        '''CREATE TABLE IF NOT EXISTS AlphaFoldData (
            alphafold_id INTEGER PRIMARY KEY AUTOINCREMENT,
            structure_id INTEGER,
            identifier TEXT,
            download_link TEXT,
            pdb TEXT,  -- Nueva columna agregada
            FOREIGN KEY (structure_id) REFERENCES ThreeDStructures (structure_id)
        );''',

        '''CREATE TABLE IF NOT EXISTS PDBEntries (
            pdb_entry_id INTEGER PRIMARY KEY AUTOINCREMENT,
            structure_id INTEGER,
            pdb_id TEXT,
            resolution TEXT,
            download_link TEXT,
            pdb TEXT,  -- Nueva columna agregada
            FOREIGN KEY (structure_id) REFERENCES ThreeDStructures (structure_id)
        );''',

        '''CREATE TABLE IF NOT EXISTS Isoforms (
            isoform_id TEXT PRIMARY KEY,
            accession_number TEXT,
            isoform_sequence TEXT,
            isoform_name TEXT,
            FOREIGN KEY (accession_number) REFERENCES Proteins (accession_number)
        );''',

        '''CREATE TABLE IF NOT EXISTS Alignments (
            alignment_id INTEGER PRIMARY KEY AUTOINCREMENT,
            reference_sequence_id INTEGER,
            source_id TEXT,
            source_type TEXT CHECK(source_type IN ('Protein', 'Isoform')),
            adjusted_score FLOAT,
            similarity FLOAT,
            seq_ref TEXT,
            seq TEXT,
            match TEXT, 
            pdb TEXT,             
            success_info TEXT,          
            FOREIGN KEY (reference_sequence_id) REFERENCES ReferenceSequences (reference_sequence_id),
            FOREIGN KEY (source_id) REFERENCES Proteins (accession_number) ON DELETE CASCADE,
            FOREIGN KEY (source_id) REFERENCES Isoforms (isoform_id) ON DELETE CASCADE
        );''',

        '''CREATE TABLE IF NOT EXISTS AlignedZones (
            aligned_zone_id INTEGER PRIMARY KEY AUTOINCREMENT,
            alignment_id INTEGER,
            reference_zone_id INTEGER,
            aligned_sequence TEXT,
            match TEXT,
            hydrophobicity_aligned FLOAT,
            volume_aligned FLOAT,
            delta_hydrophobicity FLOAT,
            delta_volume FLOAT,
            tipo_carga TEXT,
            cargas TEXT,
            cargas_reference TEXT,
            vsd_valido BOOLEAN,
            FOREIGN KEY (alignment_id) REFERENCES Alignments (alignment_id),
            FOREIGN KEY (reference_zone_id) REFERENCES ReferenceZones (zone_id)
        );''',

        '''CREATE TABLE IF NOT EXISTS FoldSeek (
            foldseek_id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_referencia INTEGER,
            database_name TEXT,
            target TEXT,
            seqId FLOAT,
            alnLength INTEGER,
            mismatches INTEGER,
            gapsOpened INTEGER,
            qStartPos INTEGER,
            qEndPos INTEGER,
            dbStartPos INTEGER,
            dbEndPos INTEGER,
            prob FLOAT,
            eval FLOAT,
            score FLOAT,
            qLen INTEGER,
            dbLen INTEGER,
            qAln TEXT,
            dbAln TEXT,
            tCa TEXT,
            tSeq TEXT,
            taxId INTEGER,
            taxName TEXT,
            alphafold_pdb TEXT,
            protein_name TEXT,
            hyperlink TEXT,
            FOREIGN KEY (id_referencia) REFERENCES ReferenceSequences (reference_sequence_id)
        );''',

        '''CREATE TABLE IF NOT EXISTS FoldSeekAlignmentDetails (
            alignment_detail_id INTEGER PRIMARY KEY AUTOINCREMENT,
            foldseek_id INTEGER,
            reference_aligned TEXT,
            match TEXT,
            target_aligned TEXT,
            similarity FLOAT,
            pdb TEXT,
            FOREIGN KEY (foldseek_id) REFERENCES FoldSeek (foldseek_id)
        );''',

        '''CREATE TABLE IF NOT EXISTS FoldSeekAlignedZones (
            aligned_zone_id INTEGER PRIMARY KEY AUTOINCREMENT,
            alignment_detail_id INTEGER,
            reference_zone_id INTEGER,
            fragment TEXT,
            match TEXT,
            hydrophobicity FLOAT,
            volume FLOAT,
            delta_hydrophobicity FLOAT,
            delta_volume FLOAT,
            tipo_carga TEXT,
            cargas TEXT,
            cargas_reference TEXT,
            vsd_valido BOOLEAN,
            FOREIGN KEY (alignment_detail_id) REFERENCES FoldSeekAlignmentDetails (alignment_detail_id),
            FOREIGN KEY (reference_zone_id) REFERENCES ReferenceZones (zone_id)
        );''',

        '''CREATE TABLE IF NOT EXISTS HelicesDetails (
            helices_id INTEGER PRIMARY KEY AUTOINCREMENT,
            aligned_zone_id INTEGER,
            zone_number INTEGER,
            helix TEXT,
            residue_id INTEGER,
            location TEXT CHECK(location IN ('I', 'O')),
            FOREIGN KEY (aligned_zone_id) REFERENCES AlignedZones (aligned_zone_id)
        );'''
    ]

    for create_statement in tables:
        create_table(cursor, create_statement)

    connection.commit()
    connection.close()
    print("Base de datos y tablas creadas correctamente.")

"""
# Ejecución principal
def main():
    db_name = "proteins_discovery.db"
    create_database(db_name)

if __name__ == "__main__":
    main()
"""