import sqlite3
import requests
from vmd import molecule, atomsel
import pymol2
import os
from Bio.PDB import PDBParser, PDBIO, Select
from io import StringIO
import time

class StructureProcessor:
    def __init__(self, db_path):
        self.db_path = db_path

    def process_all_valid_structures(self):
        """Process all valid structures (both UniProt and FoldSeek) from database"""
        print("Processing UniProt structures...")
        self.process_uniprot_structures(self.db_path)

        print("Processing FoldSeek structures...")
        self.process_foldseek_structures(self.db_path)

    def process_uniprot_structures(self,db_path):
        # Get valid accessions
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT DISTINCT A.source_id
            FROM Alignments A
            JOIN AlignedZones AZ ON A.alignment_id = AZ.alignment_id
			JOIN ThreeDStructures TD ON A.source_id = TD.accession_number
            WHERE AZ.vsd_valido = 1 AND (TD.has_alphafold = 1 OR TD.has_pdb =1 )
        ''')
        accessions = [row[0] for row in cursor.fetchall()]
        conn.close()

        for accession_number in accessions:
            structures = self.get_protein_structures(db_path, accession_number)
            for structure_id, pdb_id, resolution, download_link, source in structures:
                if self.process_structure(db_path, accession_number, structure_id, source, pdb_id, resolution, download_link):
                    break

    def process_foldseek_structures(self,db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT F.foldseek_id, F.hyperlink, F.dbStartPos, F.dbEndPos
            FROM FoldSeek F
			JOIN FoldSeekAlignmentDetails fad ON F.foldseek_id = fad.foldseek_id
			JOIN FoldSeekAlignedZones faz ON fad.alignment_detail_id = faz.alignment_detail_id
            WHERE alphafold_pdb IS NOT NULL AND database_name != 'gmgcl_id' AND vsd_valido = 1
        ''')
        entries = cursor.fetchall()
        conn.close()

        for foldseek_id, download_link, start_pos, end_pos in entries:
            self.process_foldseek_entry(db_path, foldseek_id, download_link, start_pos, end_pos)

    def get_protein_structures(self, db_path, accession_number):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Consulta para PDB
        cursor.execute('''
            SELECT P.pdb_entry_id, P.pdb_id, P.resolution, P.download_link, 'PDB' as source
            FROM PDBEntries P
            JOIN ThreeDStructures T ON P.structure_id = T.structure_id
            WHERE T.accession_number = ? AND T.has_pdb = 1
        ''', (accession_number,))
        pdb_results = cursor.fetchall()

        # Consulta para AlphaFold
        cursor.execute('''
            SELECT AF.alphafold_id, AF.identifier, NULL, AF.download_link, 'AlphaFold' as source
            FROM AlphaFoldData AF
            JOIN ThreeDStructures T ON AF.structure_id = T.structure_id
            WHERE T.accession_number = ? AND T.has_alphafold = 1
        ''', (accession_number,))
        alphafold_results = cursor.fetchall()

        conn.close()

        # Combinar los resultados
        structures = pdb_results + alphafold_results
        return structures

    def process_structure(self,db_path, accession_number, structure_id, source, pdb_id, resolution, download_link):
        response = requests.get(download_link)
        if response.status_code != 200:
            return False

        pdb_content = response.content.decode('utf-8')
        seq = self.get_sequence_from_db(db_path, accession_number)
        if not seq:
            return False

        aligned_pdb = self.cut_and_align_pdb(db_path, pdb_content, seq, accession_number)
        if not aligned_pdb:
            return False

        success_info = f"{source}, {pdb_id}, {resolution or download_link}"
        self.store_aligned_pdb_uniprot(db_path, accession_number, aligned_pdb, success_info)
        return True

    def get_sequence_from_db(self,db_path, accession_number):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT seq FROM Alignments WHERE source_id = ?
        ''', (accession_number,))
        seq = cursor.fetchone()
        conn.close()
        return seq[0].replace('-', '') if seq else None

    def get_reference_pdb_uniprot(self, db_path, accession_number):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT R.pdb 
            FROM ReferenceSequences R
            JOIN Alignments A ON R.reference_sequence_id = A.reference_sequence_id
            WHERE A.source_id = ?
        ''', (accession_number,))
        ref_pdb = cursor.fetchone()
        conn.close()
        return ref_pdb[0] if ref_pdb else None

    def cut_and_align_pdb(self, db_path, pdb_content, sequence, accession_number):
        temp_pdb = f"temp_{os.getpid()}.pdb"
        cut_pdb = f"cut_{os.getpid()}.pdb"

        with open(temp_pdb, 'w') as f:
            f.write(pdb_content)

        mol_id = molecule.load('pdb', temp_pdb)
        selection = atomsel(f"protein and sequence {sequence}", molid=mol_id)

        if len(selection) == 0:
            return None

        chains = selection.get('chain')
        primary_chain = sorted(set(chains))[0] if chains else None
        if primary_chain:
            final_selection = atomsel(f"chain {primary_chain} and sequence {sequence}", molid=mol_id)
            final_selection.write('pdb', cut_pdb)

        with open(cut_pdb, 'r') as f:
            cut_pdb_content = f.read()

        os.remove(temp_pdb)
        os.remove(cut_pdb)

        ref_pdb = self.get_reference_pdb_uniprot(db_path, accession_number)
        if not ref_pdb:
            return None

        with pymol2.PyMOL() as pymol_session:
            pymol_session.cmd.read_pdbstr(ref_pdb, "reference")
            pymol_session.cmd.read_pdbstr(cut_pdb_content, "target")
            pymol_session.cmd.align("target", "reference")
            aligned_pdb = pymol_session.cmd.get_pdbstr("target")

        return aligned_pdb

    def store_aligned_pdb_uniprot(self, db_path, accession_number, aligned_pdb, success_info):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE Alignments
            SET pdb = ?, success_info = ?
            WHERE source_id = ?
        ''', (aligned_pdb, success_info, accession_number))
        conn.commit()
        conn.close()

    def get_reference_pdb_foldseek(self, db_path, foldseek_id):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            SELECT R.pdb 
            FROM ReferenceSequences R
            JOIN FoldSeek F ON R.reference_sequence_id = F.id_referencia
            WHERE F.foldseek_id = ?
        ''', (foldseek_id,))
        ref_pdb = cursor.fetchone()
        conn.close()
        return ref_pdb[0] if ref_pdb else None

    def process_foldseek_entry(self, db_path, foldseek_id, download_link, start_pos, end_pos):
        attempts = 3
        for attempt in range(attempts):
            try:
                response = requests.get(download_link)
                if response.status_code == 200:
                    foldseek_pdb_content = response.text
                    ref_pdb = self.get_reference_pdb_foldseek(db_path, foldseek_id)
                    if not ref_pdb:
                        return False

                    cut_pdb = self.cut_pdb_by_position(foldseek_pdb_content, start_pos, end_pos)
                    aligned_pdb = self.align_pdb(ref_pdb, cut_pdb)
                    if not aligned_pdb:
                        return False

                    self.store_aligned_pdb_foldseek(db_path, foldseek_id, aligned_pdb)
                    return True
            except requests.exceptions.RequestException as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                time.sleep(5)

        return False

    def cut_pdb_by_position(self, pdb_content, start_pos, end_pos):
        parser = PDBParser(QUIET=True)
        structure = parser.get_structure("foldseek", StringIO(pdb_content))

        class ResidueSelect(Select):
            def accept_residue(self, residue):
                return start_pos <= residue.id[1] <= end_pos

        output_io = StringIO()
        io = PDBIO()
        io.set_structure(structure)
        io.save(output_io, ResidueSelect())
        return output_io.getvalue()

    def align_pdb(self, ref_pdb, target_pdb):
        with pymol2.PyMOL() as pymol_session:
            pymol_session.cmd.read_pdbstr(ref_pdb, "reference")
            pymol_session.cmd.read_pdbstr(target_pdb, "target")
            pymol_session.cmd.align("target", "reference")
            return pymol_session.cmd.get_pdbstr("target")

    def store_aligned_pdb_foldseek(self,db_path, foldseek_id, aligned_pdb):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE FoldSeekAlignmentDetails
            SET pdb = ?
            WHERE foldseek_id = ?
        ''', (aligned_pdb, foldseek_id))
        conn.commit()
        conn.close()