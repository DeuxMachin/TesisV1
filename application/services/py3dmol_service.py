import py3Dmol
import os
import tempfile
import json
import pymol2
from vmd import molecule, atomsel

class Py3DMolService:
    @staticmethod

    
    @staticmethod
    def combine_pdbs(pdb1_path, pdb2_path, output_path):
        """
        Combina dos archivos PDB usando PyMOL, tal como en Streamlit.
        """
        with pymol2.PyMOL() as pymol:
            pymol.cmd.load(pdb1_path, "molecule1")
            pymol.cmd.load(pdb2_path, "molecule2")
            pymol.cmd.create("combined", "molecule1 or molecule2")
            pymol.cmd.save(output_path, "combined")
    
    @staticmethod
    def get_residue_info(pdb_data):
        """
        Obtiene información de residuos usando VMD, como en Streamlit.
        """
        # Guardar PDB como archivo temporal
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        pdb_path = os.path.join(temp_dir, f"temp_{os.getpid()}.pdb")
        
        with open(pdb_path, 'w') as f:
            f.write(pdb_data)
            
        try:
            molid = molecule.load('pdb', pdb_path)
            sel = atomsel('all')
            residues = list(set([(r, sel.resname[i]) for i, r in enumerate(sel.resid)]))
            residues.sort(key=lambda x: x[0])  # Ordenar por número de residuo
            
            # Formatear información de residuos
            residue_info = [f"{resname}{resid}" for resid, resname in residues]
            resids = [resid for resid in residues]
            count = len(residues)
            
            molecule.delete(molid)
            os.unlink(pdb_path)
            
            return residue_info, count, resids
        except Exception as e:
            print(f"Error obteniendo información de residuos: {e}")
            try:
                os.unlink(pdb_path)
            except:
                pass
            return None, 0, []
    
    @staticmethod
    def get_zone_residues(pdb_data, zone_sequence, all_sequence):
        """
        Obtiene los IDs de residuos para una zona específica, como en Streamlit.
        """
        # Guardar PDB como archivo temporal
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        pdb_path = os.path.join(temp_dir, f"temp_zone_{os.getpid()}.pdb")
        
        with open(pdb_path, 'w') as f:
            f.write(pdb_data)
            
        try:
            molid = molecule.load('pdb', pdb_path)
            sel = atomsel('all')
            residues = list(set([(r, sel.resname[i]) for i, r in enumerate(sel.resid)]))
            residues.sort(key=lambda x: x[0])
            
            # Encontrar inicio de zona en la secuencia completa
            zone_start_idx = all_sequence.replace("-", "").find(zone_sequence)
            if zone_start_idx == -1:
                return []
                
            # Mapear residuos de zona a IDs de residuos PDB
            zone_residues = []
            for i in range(len(zone_sequence)):
                if zone_start_idx + i < len(residues):
                    zone_residues.append(residues[zone_start_idx + i][0])
                    
            molecule.delete(molid)
            os.unlink(pdb_path)
            
            return zone_residues
        except Exception as e:
            print(f"Error procesando zona: {e}")
            try:
                os.unlink(pdb_path)
            except:
                pass
            return []
    
    @staticmethod
    def create_mutation_visualization(pdb_data, res_seq=None, res_zone_seq=None, selected_option="Secuencia completa", selected_zones=None, selected_residues=None, show_labels=True):
        """
        Crea un visualizador de mutaciones como en Streamlit.
        """
        # Crear archivo temporal para los datos PDB
        temp_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "temp")
        os.makedirs(temp_dir, exist_ok=True)
        pdb_path = os.path.join(temp_dir, f"temp_mutation_{os.getpid()}.pdb")
        
        with open(pdb_path, 'w') as f:
            f.write(pdb_data)
        
        viewer = py3Dmol.view(width=800, height=600)
        
        with open(pdb_path, 'r') as f:
            pdb_content = f.read()
            viewer.addModel(pdb_content, "pdb")
        
        viewer.setStyle({'cartoon': {'color': 'white'}})

        # Determinar qué residuos mutados mostrar
        matching_resids = []
        if selected_option == "Secuencia completa" and res_seq:
            matching_resids = [resid for resid, (aa, match) in res_seq.items() if match == '*']
        elif res_zone_seq and selected_zones:
            for zone in res_zone_seq:
                if zone['zone_number'] in selected_zones:
                    matching_resids.extend([resid for resid, match in zone['matches'] if match == '*'])
        
        # Si se elige "Secuencia completa", se muestran todos los residuos
        if selected_option == "Secuencia completa":
            selected_resids = matching_resids
        else:
            # Convertir IDs de residuos a enteros si son strings
            if selected_residues and isinstance(selected_residues[0], str):
                selected_resids = [int(r) for r in selected_residues]
            else:
                selected_resids = selected_residues if selected_residues else []

        # Aplicar estilo a los residuos seleccionados
        for resid in selected_resids:
            viewer.addStyle({'resi': str(resid)}, {'cartoon': {'color': 'red'}, 'stick': {'color': 'red'}})

        # Agregar etiquetas solo si están activadas
        if show_labels and selected_resids:
            viewer.addResLabels({'resi': selected_resids}, {
                'fontColor': 'black', 
                'backgroundColor': 'white', 
                'showBackground': True, 
                'fontSize': 12, 
                'alignment': 'center'
            })

        viewer.zoomTo()
        
        # Obtener HTML
        html = viewer._make_html()
        
        # Limpiar archivo temporal
        try:
            os.unlink(pdb_path)
        except:
            pass
        
        return html