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
        
        // Cargar modelos completos
        viewer.addModel(REF_PDB_DATA, "pdb", {keepH: true});
        viewer.addModel(ALIGNED_PDB_DATA, "pdb", {keepH: true});
        
        // Estilos para proteínas: cartoon para visualizar hélices
        viewer.setStyle({model: 0, atom: "protein"}, {cartoon: {color: "lightblue"}});
        viewer.setStyle({model: 1, atom: "protein"}, {cartoon: {color: "orange"}});
        
        // Estilo "ball and stick" para moléculas de agua
        viewer.setStyle({resn: ["HOH", "WAT"]}, {
            sphere: {
                radius: 0.35,   // Esferas para átomos
                color: "skyblue" 
            },
            stick: {
                radius: 0.15,   // Palos más delgados para enlaces
                color: "skyblue"
            }
        });
        
        // Estilo para otros heteroátomos
        viewer.setStyle({atom: "hetero", not: {resn: ["HOH", "WAT"]}}, {
            stick: {
                radius: 0.3,
                color: "green"
            }
        });
        
        // Ajustes de vista
        viewer.zoomTo();
        viewer.zoom(0.9);
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
                if (styleTarget.sphere) styleTarget.sphere.color = "orange";
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
                if (styleTarget.stick) styleTarget.stick.colorscheme = "amino";
                break;
            case "spectrum":
                if (styleRef.cartoon) styleRef.cartoon.colorscheme = "spectrum";
                if (styleTarget.cartoon) styleTarget.cartoon.colorscheme = "spectrum";
                if (styleRef.stick) styleRef.stick.colorscheme = "spectrum";
                if (styleTarget.stick) styleTarget.stick.colorscheme = "spectrum";
                break;
            case "ss":
                if (styleRef.cartoon) styleRef.cartoon.colorscheme = "ssPyMOL";
                if (styleTarget.cartoon) styleTarget.cartoon.colorscheme = "ssPyMOL";
                if (styleRef.stick) styleRef.stick.colorscheme = "ssPyMOL";
                if (styleTarget.stick) styleTarget.stick.colorscheme = "ssPyMOL";
                break;
        }
        
        // Aplicar estilos a la proteína
        viewer.setStyle({model: 0, atom: "protein"}, styleRef);
        viewer.setStyle({model: 1, atom: "protein"}, styleTarget);
        
        // Mantener el estilo "ball and stick" para agua
        viewer.setStyle({resn: ["HOH", "WAT"]}, {
            sphere: {
                radius: 0.35,
                color: "skyblue" 
            },
            stick: {
                radius: 0.15,
                color: "skyblue"
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
