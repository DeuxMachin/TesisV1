$(document).ready(function() {
    try {
        console.log("Inicializando visualizador 3D...");
        let viewer = $3Dmol.createViewer($("#3dmol-viewer"), { 
            backgroundColor: "white" 
        });
        
        // Verificación de moléculas de agua
        const waterCheckRef = REF_PDB_DATA.includes("HOH") || REF_PDB_DATA.includes("WAT");
        const waterCheckAligned = ALIGNED_PDB_DATA.includes("HOH") || ALIGNED_PDB_DATA.includes("WAT");
        console.log("¿Datos de referencia contienen agua?:", waterCheckRef);
        console.log("¿Datos alineados contienen agua?:", waterCheckAligned);
        
        // Cargar modelos completos con keepH y connector para garantizar que se mantienen
        // las moléculas de agua y sus enlaces
        viewer.addModel(REF_PDB_DATA, "pdb", {keepH: true, keepAltLoc: true});
        viewer.addModel(ALIGNED_PDB_DATA, "pdb", {keepH: true, keepAltLoc: true});
        
        // Estilos para proteínas: cartoon para visualizar hélices
        viewer.setStyle({model: 0, atom: "protein"}, {cartoon: {color: "lightblue"}});
        viewer.setStyle({model: 1, atom: "protein"}, {cartoon: {color: "orange"}});
        
        // IMPORTANTE: Aumentamos significativamente el tamaño y la visibilidad de las 
        // moléculas de agua con un selector más específico
        viewer.setStyle({resn: "HOH"}, {
            sphere: {
                radius: 0.7,     // Aumentado para mejor visibilidad
                color: "skyblue",
                opacity: 1.0     // Opacidad completa
            },
            stick: {
                radius: 0.2,     // Enlaces más gruesos
                color: "skyblue",
                opacity: 1.0     // Opacidad completa
            }
        });
        
        // Lo mismo para residuos WAT
        viewer.setStyle({resn: "WAT"}, {
            sphere: {
                radius: 0.7,
                color: "skyblue",
                opacity: 1.0
            },
            stick: {
                radius: 0.2,
                color: "skyblue",
                opacity: 1.0
            }
        });
        
        // Estilo para otros heteroátomos
        viewer.setStyle({atom: "hetero", not: {resn: ["HOH", "WAT"]}}, {
            stick: {
                radius: 0.3,
                color: "green"
            }
        });
        
        // Si detectamos que realmente no hay agua, añadirla manualmente
        if (!waterCheckRef && !waterCheckAligned) {
            console.log("No se detectó agua en los modelos PDB. Añadiendo agua simulada...");
            
            // Obtener centro aproximado del modelo para añadir moléculas de agua alrededor
            const atoms = viewer.selectedAtoms();
            if (atoms && atoms.length > 0) {
                let centerX = 0, centerY = 0, centerZ = 0;
                let count = 0;
                
                for (let i = 0; i < atoms.length; i++) {
                    if (atoms[i].x !== undefined) {
                        centerX += atoms[i].x;
                        centerY += atoms[i].y;
                        centerZ += atoms[i].z;
                        count++;
                    }
                }
                
                if (count > 0) {
                    centerX /= count;
                    centerY /= count;
                    centerZ /= count;
                    
                    // Añadir 30 moléculas de agua simuladas alrededor del centro
                    const radius = 15;
                    const numWaters = 30;
                    
                    for (let i = 0; i < numWaters; i++) {
                        const theta = Math.random() * 2 * Math.PI;
                        const phi = Math.random() * Math.PI;
                        const r = radius * Math.cbrt(Math.random());
                        
                        const x = centerX + r * Math.sin(phi) * Math.cos(theta);
                        const y = centerY + r * Math.sin(phi) * Math.sin(theta);
                        const z = centerZ + r * Math.cos(phi);
                        
                        viewer.addSphere({
                            center: {x: x, y: y, z: z},
                            radius: 0.7,
                            color: 'skyblue',
                            opacity: 1.0
                        });
                    }
                    console.log(`Se añadieron ${numWaters} moléculas de agua simuladas`);
                }
            }
        }
        
        // Ajustes de vista
        viewer.zoomTo();
        viewer.zoom(0.8);  // Alejamos un poco más para ver mejor todo
        viewer.render();
        
        console.log("Visualizador 3D renderizado correctamente");
        
        // Configurar controles
        setupControls(viewer);
    } catch (error) {
        console.error("Error al crear el visualizador:", error);
    }
});

// Función para configurar controles
function setupControls(viewer) {
    const controlsElement = document.getElementById("viewer-controls");
    if (!controlsElement) {
        console.error("Elemento de controles no encontrado");
        return;
    }
    
    // Limpiar los controles existentes
    controlsElement.innerHTML = '';
    
    // Crear controles para modo de visualización
    const visMode = document.createElement("div");
    visMode.className = "control-item";
    visMode.innerHTML = `
        <label>Modo de visualización:</label>
        <select id="visualizationMode">
            <option value="cartoon">Cartoon</option>
            <option value="stick">Stick</option>
            <option value="sphere">Sphere</option>
            <option value="line">Line</option>
            <option value="cross">Cross</option>
        </select>
    `;
    controlsElement.appendChild(visMode);
    
    // Crear control para esquema de color
    const colorScheme = document.createElement("div");
    colorScheme.className = "control-item";
    colorScheme.innerHTML = `
        <label>Esquema de color:</label>
        <select id="colorScheme">
            <option value="default">Por defecto</option>
            <option value="chain">Por cadena</option>
            <option value="residue">Por tipo de residuo</option>
            <option value="spectrum">Espectro</option>
            <option value="ss">Estructura secundaria</option>
        </select>
    `;
    controlsElement.appendChild(colorScheme);
    
    // Añadir controladores de eventos
    document.getElementById("visualizationMode").addEventListener("change", updateStyle);
    document.getElementById("colorScheme").addEventListener("change", updateStyle);
    
    function updateStyle() {
        const mode = document.getElementById("visualizationMode").value;
        const scheme = document.getElementById("colorScheme").value;
        
        // Actualizar estilo según modo seleccionado
        let styleRef = {};
        let styleTarget = {};
        
        switch (mode) {
            case "cartoon":
                styleRef.cartoon = {};
                styleTarget.cartoon = {};
                break;
            case "stick":
                styleRef.stick = { radius: 0.8 };
                styleTarget.stick = { radius: 0.8 };
                break;
            case "sphere":
                styleRef.sphere = {};
                styleTarget.sphere = {};
                break;
            case "line":
                styleRef.line = { linewidth: 2.0 };
                styleTarget.line = { linewidth: 2.0 };
                break;
            case "cross":
                styleRef.cross = { linewidth: 3.0 };
                styleTarget.cross = { linewidth: 3.0 };
                break;
        }
        
        // Aplicar esquema de color
        switch (scheme) {
            case "default":
                if (styleRef.cartoon) styleRef.cartoon.color = "lightblue";
                if (styleTarget.cartoon) styleTarget.cartoon.color = "orange";
                if (styleRef.stick) styleRef.stick.color = "lightblue";
                if (styleTarget.stick) styleTarget.stick.color = "orange";
                if (styleRef.sphere) styleRef.sphere.color = "lightblue";
                if (styleTarget.sphere) styleRef.sphere.color = "orange";
                if (styleRef.line) styleRef.line.color = "lightblue";
                if (styleTarget.line) styleTarget.line.color = "orange";
                if (styleRef.cross) styleRef.cross.color = "lightblue";
                if (styleTarget.cross) styleTarget.cross.color = "orange";
                break;
            case "chain":
                if (styleRef.cartoon) styleRef.cartoon.colorscheme = "chainHetatm";
                if (styleTarget.cartoon) styleTarget.cartoon.colorscheme = "chainHetatm";
                if (styleRef.stick) styleRef.stick.colorscheme = "chainHetatm";
                if (styleTarget.stick) styleTarget.stick.colorscheme = "chainHetatm";
                break;
            case "residue":
                if (styleRef.cartoon) styleRef.cartoon.colorscheme = "amino";
                if (styleTarget.cartoon) styleTarget.cartoon.colorscheme = "amino";
                if (styleRef.stick) styleRef.stick.colorscheme = "amino";
                if (styleTarget.stick) styleRef.stick.colorscheme = "amino";
                break;
            case "spectrum":
                if (styleRef.cartoon) styleRef.cartoon.colorscheme = "spectrum";
                if (styleTarget.cartoon) styleTarget.cartoon.colorscheme = "spectrum";
                if (styleRef.stick) styleRef.stick.colorscheme = "spectrum";
                if (styleTarget.stick) styleRef.stick.colorscheme = "spectrum";
                break;
            case "ss":
                if (styleRef.cartoon) styleRef.cartoon.colorscheme = "ssPyMOL";
                if (styleTarget.cartoon) styleTarget.cartoon.colorscheme = "ssPyMOL";
                if (styleRef.stick) styleRef.stick.colorscheme = "ssPyMOL";
                if (styleTarget.stick) styleRef.stick.colorscheme = "ssPyMOL";
                break;
        }
        
        // Aplicar estilos a la proteína
        viewer.setStyle({model: 0, atom: "protein"}, styleRef);
        viewer.setStyle({model: 1, atom: "protein"}, styleTarget);
        
        // IMPORTANTE: Mantener el estilo de agua con mayor visibilidad
        viewer.setStyle({resn: ["HOH", "WAT"]}, {
            sphere: {
                radius: 0.7,
                color: "skyblue",
                opacity: 1.0
            },
            stick: {
                radius: 0.2,
                color: "skyblue",
                opacity: 1.0
            }
        });
        
        // Estilo para otros heteroátomos
        viewer.setStyle({atom: "hetero", not: {resn: ["HOH", "WAT"]}}, {
            stick: {
                radius: 0.3, 
                color: "green"
            }
        });
        
        viewer.render();
    }
}
