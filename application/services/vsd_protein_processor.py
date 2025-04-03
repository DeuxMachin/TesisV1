import sqlite3
from abc import ABC, abstractmethod



# INTERFAZ ABSTRACTA (Principio de Abierto/Cerrado - OCP)
class DatabaseHandler(ABC):
    @abstractmethod
    def execute_query(self, query: str, params: tuple = ()): 
        pass

# CLASE QUE MANEJA CONEXIONES A SQLITE (Principio de Responsabilidad Única - SRP)
class SQLiteHandler(DatabaseHandler):
    def __init__(self, db_name: str):
        self.db_name = db_name

    def execute_query(self, query: str, params: tuple = ()): 
        with sqlite3.connect(self.db_name) as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor.fetchall()

# CLASE PARA CREAR LA TABLA (Principio de Única Responsabilidad - SRP)
class VSDTableCreator:
    def __init__(self, db_handler: DatabaseHandler):
        self.db_handler = db_handler

    def create_table(self):
        create_table_query = """
        CREATE TABLE IF NOT EXISTS ValidVSDProteins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            protein_id TEXT NOT NULL,
            source TEXT CHECK(source IN ('UniProt', 'FoldSeek')),
            has_pdb BOOLEAN NOT NULL
        );
        """
        self.db_handler.execute_query(create_table_query)
        print("Tabla ValidVSDProteins creada correctamente.")

        create_calculations_table_query = """
        CREATE TABLE IF NOT EXISTS ProteinCalculations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vsd_protein_id INTEGER NOT NULL,
            composicion_porcentajes TEXT,
            composicion_conteo TEXT,
            masa_molecular FLOAT,
            pI FLOAT,
            hidrofobicidad_promedio FLOAT,
            carga_neta_ph7 FLOAT,
            numero_nodos INT,
            numero_aristas INT,
            grado_promedio FLOAT,
            densidad FLOAT,
            grafo BLOB,
            FOREIGN KEY (vsd_protein_id) REFERENCES ValidVSDProteins(id)
        );
        """
        self.db_handler.execute_query(create_calculations_table_query)
        print("Tabla ProteinCalculations creada correctamente.")

# CLASE PARA INSERTAR DATOS DE UNIPROT (Principio de Segregación de Interfaces - ISP)
class UniProtDataInserter:
    def __init__(self, db_handler: DatabaseHandler):
        self.db_handler = db_handler

    def insert_data(self):
        insert_query = """
        INSERT OR IGNORE INTO ValidVSDProteins (protein_id, source, has_pdb)
        SELECT 
            p.accession_number AS protein_id,
            'UniProt' AS source,
            ts.has_pdb
        FROM Proteins p
        JOIN Alignments a ON p.accession_number = a.source_id
        JOIN ThreeDStructures ts ON p.accession_number = ts.accession_number
        WHERE a.alignment_id IN (
            SELECT DISTINCT alignment_id FROM AlignedZones WHERE vsd_valido = 1
        )
        AND a.pdb IS NOT NULL;
        """
        self.db_handler.execute_query(insert_query)
        print("Proteínas UniProt insertadas correctamente.")

# CLASE PARA INSERTAR DATOS DE FOLDSEEK
class FoldSeekDataInserter:
    def __init__(self, db_handler: DatabaseHandler):
        self.db_handler = db_handler

    def insert_data(self):
        insert_query = """
        INSERT OR IGNORE INTO ValidVSDProteins (protein_id, source, has_pdb)
        SELECT 
            f.foldseek_id AS protein_id,
            'FoldSeek' AS source,
            1 AS has_pdb
        FROM FoldSeek f
        JOIN FoldSeekAlignmentDetails fad ON f.foldseek_id = fad.foldseek_id
        JOIN FoldSeekAlignedZones faz ON fad.alignment_detail_id = faz.alignment_detail_id
        JOIN ReferenceSequences rz ON f.id_referencia = rz.reference_sequence_id
        WHERE f.database_name != 'gmgcl_id'
        AND fad.pdb IS NOT NULL
        AND fad.alignment_detail_id IN (
            SELECT DISTINCT faz.alignment_detail_id FROM FoldSeekAlignedZones faz WHERE faz.vsd_valido = 1
        )
        GROUP BY f.foldseek_id, fad.alignment_detail_id;
        """
        self.db_handler.execute_query(insert_query)
        print("Proteínas FoldSeek insertadas correctamente.")

# CLASE PRINCIPAL QUE ORQUESTA TODO (Principio de Inversión de Dependencias - DIP)
class VSDProteinProcessor:
    def __init__(self, db_handler: DatabaseHandler):
        self.table_creator = VSDTableCreator(db_handler)
        self.uniprot_inserter = UniProtDataInserter(db_handler)
        self.foldseek_inserter = FoldSeekDataInserter(db_handler)

    def process(self):
        self.table_creator.create_table()
        self.uniprot_inserter.insert_data()
        self.foldseek_inserter.insert_data()
        print("✅ Proceso de inserción de proteínas VSD completado.")
        
"""

# Si este script se ejecuta directamente, se ejecutará el procesamiento
def main():
    # Configuración de la base de datos
    db_name = "./database/proteins_discovery.db"
    db_handler = SQLiteHandler(db_name)
    processor = VSDProteinProcessor(db_handler)
    processor.process()

if __name__ == "__main__":
    main()
"""