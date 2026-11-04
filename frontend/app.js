const COLORES = {
    fortnite:         { color: "#bf00ff", icon: "🟣" },
    genshin_impact:   { color: "#00f5ff", icon: "🔵" },
    league_of_legends:{ color: "#c89b3c", icon: "⚔️" },
    minecraft:        { color: "#00ff88", icon: "🟢" },
    valorant:         { color: "#ff003c", icon: "🔴" },
    vrchat:           { color: "#ff6600", icon: "🟠" },
}

let ultimoAnalisis = null
let ultimoHistorial = null

// Partículas de fondo
function crearParticulas() {
    const container = document.getElementById("particles")
    for (let i = 0; i < 40; i++) {
        const p = document.createElement("div")
        p.className = "particle"
        p.style.left = Math.random() * 100 + "vw"
        p.style.animationDuration = (Math.random() * 10 + 8) + "s"
        p.style.animationDelay = (Math.random() * 10) + "s"
        p.style.background = Math.random() > 0.5 ? "#00f5ff" : "#bf00ff"
        container.appendChild(p)
    }
}

function showTab(tab, e) {
    document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"))
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"))
    document.getElementById("tab-" + tab).classList.add("active")
    e.target.classList.add("active")
}

// Drag & Drop
const uploadZone = document.getElementById("uploadZone")
uploadZone.addEventListener("dragover", e => { e.preventDefault(); uploadZone.classList.add("dragover") })
uploadZone.addEventListener("dragleave", () => uploadZone.classList.remove("dragover"))
uploadZone.addEventListener("drop", e => {
    e.preventDefault()
    uploadZone.classList.remove("dragover")
    const file = e.dataTransfer.files[0]
    if (file && file.type.startsWith("video/")) mostrarPreview(file)
})

document.getElementById("videoInput").addEventListener("change", e => {
    if (e.target.files[0]) mostrarPreview(e.target.files[0])
})

function mostrarPreview(file) {
    const preview = document.getElementById("videoPreview")
    const player = document.getElementById("videoPlayer")
    const name = document.getElementById("videoName")
    player.src = URL.createObjectURL(file)
    name.textContent = "📁 " + file.name
    preview.style.display = "block"
    document.getElementById("uploadZone").style.display = "none"
}

async function analizar() {
    const input = document.getElementById("videoInput")
    const confianza = document.getElementById("confianza").value / 100

    if (!input.files[0]) {
        alert("Selecciona un vídeo primero")
        return
    }

    const btn = document.getElementById("btnAnalizar")
    btn.disabled = true
    document.getElementById("progressContainer").style.display = "block"
    document.getElementById("resultados").style.display = "none"

    const formData = new FormData()
    formData.append("video", input.files[0])
    formData.append("confianza", confianza)

    try {
        const res = await fetch("/analizar", { method: "POST", body: formData })
        const data = await res.json()
        mostrarResultados(data)
    } catch (e) {
        alert("Error al analizar el vídeo")
    } finally {
        btn.disabled = false
        document.getElementById("progressContainer").style.display = "none"
    }
}

function nuevoAnalisis() {
    document.getElementById("uploadZone").style.display = "block"
    document.getElementById("videoPreview").style.display = "none"
    document.getElementById("resultados").style.display = "none"
    document.getElementById("btnNuevo").style.display = "none"
    document.getElementById("btnPDF").style.display = "none"
    document.getElementById("videoInput").value = ""
    document.getElementById("videoPlayer").src = ""
    ultimoAnalisis = null
}

function mostrarResultados(data) {
    ultimoAnalisis = data
    const container = document.getElementById("resultados")
    container.style.display = "block"
    document.getElementById("btnNuevo").style.display = "block"

    if (!data.detecciones || data.detecciones.length === 0) {
        container.innerHTML = `<div class="no-detecciones">⚠️ NO SE DETECTARON LOGOS EN EL VÍDEO</div>`
        return
    }

    document.getElementById("btnPDF").style.display = "block"

    let html = `<p class="resultado-header">✅ ANÁLISIS COMPLETADO — ${data.duracion}s DE VÍDEO</p>`
    html += `<div class="cards-grid">`

    data.detecciones.forEach((d, i) => {
        const info = COLORES[d.clase] || { color: "#ffffff", icon: "🎮" }
        html += `
        <div class="card" style="border-color: ${info.color}33; animation-delay: ${i * 0.1}s">
            <div class="card-icon">${info.icon}</div>
            <div class="card-name" style="color: ${info.color}">${d.clase.replace(/_/g, " ")}</div>
            <div class="card-tiempo" style="color: ${info.color}">${d.tiempo}s</div>
            <div class="card-pct">${d.porcentaje}% del vídeo</div>
            <div class="card-bar">
                <div class="card-bar-fill" style="width: ${d.porcentaje}%; background: ${info.color}"></div>
            </div>
        </div>`
    })

    html += `</div>`
    container.innerHTML = html
}

async function cargarHistorial() {
    const container = document.getElementById("historialContainer")
    container.innerHTML = `<p style="text-align:center; color: var(--neon-cyan); font-family: Orbitron; letter-spacing:2px; font-size:0.8rem">CARGANDO...</p>`

    try {
        const res = await fetch("/historial")
        const data = await res.json()
        ultimoHistorial = data

        if (data.length === 0) {
            container.innerHTML = `<div class="no-detecciones">NO HAY ANÁLISIS GUARDADOS AÚN</div>`
            document.getElementById("btnCSV").style.display = "none"
            return
        }

        document.getElementById("btnCSV").style.display = "block"

        let html = `<table class="historial-table">
            <thead><tr>
                <th>VÍDEO</th><th>MARCA</th><th>TIEMPO</th><th>%</th><th>DURACIÓN</th><th>FECHA</th>
            </tr></thead><tbody>`

        data.forEach(r => {
            const info = COLORES[r.clase] || { color: "#ffffff" }
            html += `<tr>
                <td>${r.video}</td>
                <td style="color: ${info.color}">${r.clase.replace(/_/g, " ")}</td>
                <td>${r.tiempo}s</td>
                <td>${r.porcentaje}%</td>
                <td>${r.duracion_video}s</td>
                <td>${r.fecha}</td>
            </tr>`
        })

        html += `</tbody></table>`
        container.innerHTML = html
    } catch (e) {
        container.innerHTML = `<div class="no-detecciones">ERROR AL CARGAR EL HISTORIAL</div>`
    }
}

crearParticulas()

function descargarCSV() {
    const cabecera = ["video", "clase", "tiempo_s", "porcentaje", "duracion_video_s", "fecha"]
    const filas = ultimoHistorial.map(r => [
        `"${r.video}"`,
        r.clase,
        r.tiempo,
        r.porcentaje,
        r.duracion_video,
        `"${r.fecha}"`
    ].join(","))

    const csv = [cabecera.join(","), ...filas].join("\n")
    const blob = new Blob([csv], { type: "text/csv;charset=utf-8;" })
    const url = URL.createObjectURL(blob)
    const a = document.createElement("a")
    a.href = url
    a.download = `historial_gamelogo_${Date.now()}.csv`
    a.click()
    URL.revokeObjectURL(url)
}

function descargarPDF() {
    const { jsPDF } = window.jspdf
    const doc = new jsPDF()
    const data = ultimoAnalisis
    const fecha = new Date().toLocaleString("es-ES")

    // Fondo negro
    doc.setFillColor(5, 5, 16)
    doc.rect(0, 0, 210, 297, "F")

    // Cabecera
    doc.setFont("helvetica", "bold")
    doc.setFontSize(22)
    doc.setTextColor(0, 245, 255)
    doc.text("GAMELOGO DETECTOR", 105, 20, { align: "center" })

    doc.setFontSize(10)
    doc.setTextColor(96, 96, 170)
    doc.setFont("helvetica", "normal")
    doc.text("// Informe de detecciones de logos //", 105, 28, { align: "center" })

    doc.setDrawColor(0, 245, 255)
    doc.setLineWidth(0.5)
    doc.line(15, 33, 195, 33)

    // Info del vídeo
    doc.setFontSize(10)
    doc.setFont("helvetica", "bold")
    doc.setTextColor(191, 0, 255)
    doc.text("VÍDEO:", 15, 42)
    doc.setFont("helvetica", "normal")
    doc.setTextColor(224, 224, 255)
    doc.text(data.video, 40, 42)

    doc.setFont("helvetica", "bold")
    doc.setTextColor(191, 0, 255)
    doc.text("DURACIÓN:", 15, 50)
    doc.setFont("helvetica", "normal")
    doc.setTextColor(224, 224, 255)
    doc.text(`${data.duracion}s`, 45, 50)

    doc.setFont("helvetica", "bold")
    doc.setTextColor(191, 0, 255)
    doc.text("FECHA:", 15, 58)
    doc.setFont("helvetica", "normal")
    doc.setTextColor(224, 224, 255)
    doc.text(fecha, 35, 58)

    doc.setDrawColor(96, 96, 170)
    doc.setLineWidth(0.3)
    doc.line(15, 63, 195, 63)

    // Cabecera tabla
    doc.setFontSize(9)
    doc.setFont("helvetica", "bold")
    doc.setTextColor(0, 245, 255)
    doc.text("MARCA", 15, 72)
    doc.text("TIEMPO", 120, 72)
    doc.text("PORCENTAJE", 155, 72)
    doc.setDrawColor(0, 245, 255)
    doc.line(15, 75, 195, 75)

    const COLORES_RGB = {
        fortnite:          [191, 0, 255],
        genshin_impact:    [0, 245, 255],
        league_of_legends: [200, 155, 60],
        minecraft:         [0, 255, 136],
        valorant:          [255, 0, 60],
        vrchat:            [255, 102, 0],
    }

    let y = 84
    data.detecciones.forEach(d => {
        const rgb = COLORES_RGB[d.clase] || [224, 224, 255]

        // Fila de fondo
        doc.setFillColor(20, 20, 40)
        doc.rect(15, y - 5, 180, 8, "F")

        // Barra de porcentaje
        const barWidth = Math.min((d.porcentaje / 100) * 180, 180)
        doc.setFillColor(...rgb)
        doc.setGState(new doc.GState({ opacity: 0.25 }))
        doc.rect(15, y - 5, barWidth, 8, "F")
        doc.setGState(new doc.GState({ opacity: 1 }))

        // Texto fila
        doc.setFont("helvetica", "bold")
        doc.setFontSize(9)
        doc.setTextColor(...rgb)
        doc.text(d.clase.replace(/_/g, " ").toUpperCase(), 17, y)
        doc.setFont("helvetica", "normal")
        doc.setTextColor(224, 224, 255)
        doc.text(`${d.tiempo}s`, 120, y)
        doc.text(`${d.porcentaje}%`, 155, y)

        y += 12
    })

    // Total
    doc.setDrawColor(96, 96, 170)
    doc.line(15, y, 195, y)
    y += 8
    doc.setFont("helvetica", "bold")
    doc.setFontSize(10)
    doc.setTextColor(0, 255, 136)
    doc.text(`DURACIÓN TOTAL: ${data.duracion}s`, 15, y)

    // Footer
    doc.setFontSize(8)
    doc.setTextColor(96, 96, 170)
    doc.text("// POWERED BY YOLOv8 + FASTAPI — GameLogo Detector //", 105, 285, { align: "center" })

    const nombreArchivo = `informe_${data.video.replace(/\.[^.]+$/, "")}_${Date.now()}.pdf`
    doc.save(nombreArchivo)
}
