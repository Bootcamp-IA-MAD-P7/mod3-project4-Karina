const COLORES = {
    fortnite:         { color: "#bf00ff", icon: "🟣" },
    genshin_impact:   { color: "#00f5ff", icon: "🔵" },
    league_of_legends:{ color: "#c89b3c", icon: "⚔️" },
    minecraft:        { color: "#00ff88", icon: "🟢" },
    valorant:         { color: "#ff003c", icon: "🔴" },
    vrchat:           { color: "#ff6600", icon: "🟠" },
}

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

function showTab(tab) {
    document.querySelectorAll(".tab-content").forEach(t => t.classList.remove("active"))
    document.querySelectorAll(".tab-btn").forEach(b => b.classList.remove("active"))
    document.getElementById("tab-" + tab).classList.add("active")
    event.target.classList.add("active")
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
    document.getElementById("videoInput").value = ""
    document.getElementById("videoPlayer").src = ""
}

function mostrarResultados(data) {
    const container = document.getElementById("resultados")
    container.style.display = "block"
    document.getElementById("btnNuevo").style.display = "block"

    if (!data.detecciones || data.detecciones.length === 0) {
        container.innerHTML = `<div class="no-detecciones">⚠️ NO SE DETECTARON LOGOS EN EL VÍDEO</div>`
        return
    }

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

        if (data.length === 0) {
            container.innerHTML = `<div class="no-detecciones">NO HAY ANÁLISIS GUARDADOS AÚN</div>`
            return
        }

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
