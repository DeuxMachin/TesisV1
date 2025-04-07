// molstar_viewer.js

async function renderMolstarStructure(encodedRefPDB, encodedAlignedPDB) {
    try {
        const plugin = await createMolstarViewer("molstar-viewer");

        const refPDB = atob(encodedRefPDB);
        const alignedPDB = atob(encodedAlignedPDB);

        await plugin.loadStructureFromData(refPDB, "pdb", { label: "Referencia" });
        await plugin.loadStructureFromData(alignedPDB, "pdb", { label: "Alineado" });

        plugin.managers.camera.focus.reset();
        plugin.managers.camera.focus.setFromStructures();
    } catch (error) {
        console.error("Error al cargar estructuras con Mol*:", error);
    }
}

async function createMolstarViewer(targetId) {
    const element = document.getElementById(targetId);

    if (!element) throw new Error("Elemento DOM no encontrado");

    const plugin = new window.Molstar.PluginViewer(element, {
        layoutIsExpanded: false,
        layoutShowControls: true,
        layoutShowRemoteState: false,
        layoutShowSequence: true,
        layoutShowLog: false,
        layoutShowLeftPanel: false
    });

    return plugin;
}

$(document).ready(function() {
    console.log("Iniciando visualizador de proteínas...");
    
    const viewerContainer = document.getElementById('molstar-viewer');
    const loadingElement = document.getElementById('molstar-loading');
    
    if (!viewerContainer) {
        console.error("No se encontró el contenedor del visualizador");
        return;
    }
    
    try {
        // Mostrar indicador de carga
        if (loadingElement) loadingElement.style.display = 'block';
        
        // Obtener datos codificados
        const refPdbData = viewerContainer.getAttribute('data-ref-pdb');
        const alignedPdbData = viewerContainer.getAttribute('data-aligned-pdb');
        
        if (!refPdbData || !alignedPdbData) {
            throw new Error("No se encontraron datos PDB codificados");
        }
        
        // Decodificar datos PDB
        const refPdb = atob(refPdbData);
        const alignedPdb = atob(alignedPdbData);
        
        // Configurar el visualizador Mol*
        molstar.Viewer.create(viewerContainer, {
            layoutIsExpanded: false,
            layoutShowControls: true,
            layoutShowSequence: true,
            layoutShowLog: false,
            layoutShowLeftPanel: true,
            viewportBackground: '#000'
        }).then(viewer => {
            // Primero mostrar la estructura de referencia en azul
            return viewer.loadStructureFromData(refPdb, "pdb", {
                label: "Estructura Referencia",
                color: 'blue'
            }).then(() => {
                // Luego mostrar la estructura alineada en naranja
                return viewer.loadStructureFromData(alignedPdb, "pdb", {
                    label: "Estructura Alineada", 
                    color: 'orange'
                });
            }).then(() => {
                // Usar API correcta para resetear cámara y configurar fondo
                try {
                    // Método 1: API más reciente
                    if (viewer.canvas3d && typeof viewer.canvas3d.requestCameraReset === 'function') {
                        viewer.canvas3d.requestCameraReset();
                        viewer.canvas3d.setBackground(0x000000);
                    } 
                    // Método 2: API alternativa
                    else if (viewer.scene && typeof viewer.scene.resetCamera === 'function') {
                        viewer.scene.resetCamera();
                        viewer.scene.setBackground(0x000000);
                    }
                    // Método 3: Otro formato de API
                    else if (typeof viewer.resetCamera === 'function') {
                        viewer.resetCamera();
                        if (typeof viewer.setBackground === 'function') {
                            viewer.setBackground('#000');
                        }
                    } 
                    // Si ninguno funciona
                    else {
                        console.log("No se encontró método apropiado para resetear la cámara");
                    }
                } catch (cameraError) {
                    console.warn("No se pudo resetear la cámara:", cameraError);
                }
                
                // Ocultar el indicador de carga
                if (loadingElement) loadingElement.style.display = 'none';
                console.log("Visualizador inicializado correctamente");
            });
        }).catch(error => {
            console.error("Error en visualizador:", error);
            viewerContainer.innerHTML = `
                <div style="padding: 20px; color: white; background-color: #660000; text-align: center; border-radius: 8px;">
                    <h3>Error en el visualizador</h3>
                    <p>${error.message || "Error desconocido"}</p>
                </div>`;
            if (loadingElement) loadingElement.style.display = 'none';
        });
    } catch (error) {
        console.error("Error general:", error);
        viewerContainer.innerHTML = `
            <div style="padding: 20px; color: white; background-color: #660000; text-align: center; border-radius: 8px;">
                <h3>Error en el visualizador</h3>
                <p>${error.message || "Error desconocido"}</p>
            </div>`;
        if (loadingElement) loadingElement.style.display = 'none';
    }
});
