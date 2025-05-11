import streamlit as st
import json
import time
import re

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import base64
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from io import BytesIO
import textwrap

# ========== UTILIDADES ==========
def get_airport_name(oaci_code):
    oaci_to_name = {
        'SAEZ': 'EZEIZA/MINISTRO PISTARINI',
        'SACO': 'CORDOBA/ING. AER. A. L. V. TARAVELLA',
        'SABE': 'AEROPARQUE J. NEWBERY',
        'SAAR': 'ROSARIO/ ISLAS MALVINAS',
        'SAZM': 'MAR DEL PLATA/ASTOR PIAZZOLLA',
        'AVTD': 'AVISOS A TODAS LAS FIRS',
        'SAVF': 'AVISOS FIR COMODORO',
        'SACF': 'AVISOS FIR CORDOBA',
        'SAEF': 'AVISOS FIR EZEIZA',
        'SAMF': 'AVISOS FIR MENDOZA',
        'SARR': 'AVISOS FIR RESISTENCIA',
        'SANC': 'CATAMARCA',
        'SARI': 'CATARATAS DEL IGUAZU / M. C. E. KRAUSE',
        'SAAC': 'CONCORDIA/COMODORO PIERRESTEGUI',
        'SACE': 'CORDOBA/ESCUELA DE AVIACION MILITAR',
        'SARC': 'CORRIENTES',
        'SARF': 'FORMOSA',
        'SAZG': 'GENERAL PICO',
        'SATG': 'GOYA',
        'SASJ': 'JUJUY/GOBERNADOR GUZMAN',
        'SADL': 'LA PLATA',
        'SANL': 'LA RIOJA/CAP.VICENTE A.ALMONACID',
        'SAMM': 'MALARGÜE',
        'SADJ': 'MARIANO MORENO',
        'SATM': 'MERCEDES/CORRIENTES',
        'SADM': 'MORON/ PRESIDENTE RIVADAVIA',
        'SAZN': 'NEUQUEN/PRESIDENTE PERON',
        'SAZX': 'NUEVE DE JULIO',
        'SAAP': 'PARANA/GRAL. URQUIZA',
        'SARL': 'PASO DE LOS LIBRES',
        'SAZP': 'PEHUAJO/COM. PEDRO ZANNI',
        'SARP': 'POSADAS',
        'SAVY': 'PUERTO MADRYN/EL TEHUELCHE',
        'SAAI': 'PUNTA INDIO',
        'SADQ': 'QUILMES',
        'SAFR': 'RAFAELA/SANTA FE',
        'SATR': 'RECONQUISTA',
        'SARE': 'RESISTENCIA',
        'SAOC': 'RIO CUARTO/AREA DE MATERIAL',
        'SASA': 'SALTA',
        'SAZS': 'SAN CARLOS DE BARILOCHE',
        'SADF': 'SAN FERNANDO',
        'SAOU': 'SAN LUIS/BRIGADIER MAYOR D.CESAR RAUL OJEDA',
        'SAZY': 'SAN MARTIN DE LOS ANDES/AVIADOR C.CAMPOS',
        'SAMR': 'SAN RAFAEL/S.A. SANTIAGO GERMANO',
        'SAAV': 'SANTA FE/SAUCE VIEJO',
        'SAZR': 'SANTA ROSA',
        'SANE': 'SANTIAGO DEL ESTERO VICECOMODORO D LA PAZ ARAGONES',
        'SAZT': 'TANDIL/HEROES DE MALVINAS',
        'SANR': 'TERMAS DE RIO HONDO',
        'SANT': 'TUCUMAN/TEN. BENJAMIN MATIENZO',
        'SAOS': 'VALLE DEL CONCLARA',
        'SAFV': 'VENADO TUERTO',
        'SAWB': 'VICECOMODORO MARAMBIO',
        'SAVV': 'VIEDMA/GOBERNADOR CASTELLO',
        'SAZV': 'VILLA GESELL',
        'SAOR': 'VILLA REYNOLDS',
        'SAHZ': 'ZAPALA',
        'SAZB': 'BAHIA BLANCA/CTE ESPORA',
        'SAWC': 'EL CALAFATE',
        'SAWE': 'RIO GRANDE',
        'SAWG': 'RIO GALLEGOS/PILOTO CIVIL N. FERNANDEZ',
        'SAWH': 'USHUAIA/MALVINAS ARGENTINAS',
        'SAME': 'MENDOZA/EL PLUMERILLO',
        'SAVC': 'COMODORO RIVADAVIA/GRAL. E. MOSCONI',
        'SAVT': 'TRELEW/ALMIRANTE ZAR'
    }
    return oaci_to_name.get(oaci_code.upper(), oaci_code)

def buscar_notam(nombre):
    span = WebDriverWait(driver, 10).until(
        EC.element_to_be_clickable((By.CLASS_NAME, "select2-selection__rendered"))
    )
    span.click()
    WebDriverWait(driver, 10).until(
        EC.visibility_of_element_located((By.CLASS_NAME, "select2-results"))
    )
    option = driver.find_element(By.XPATH, f"//li[text()='{nombre}']")
    option.click()
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.ID, "pibdata"))
    )
    time.sleep(2)
    tabla = driver.find_element(By.ID, "pibdata")
    return tabla.text

def generar_pdf_notam(resultados, filename="NOTAMs_resultado.pdf"):
    """Genera un PDF con los resultados de la búsqueda de NOTAMs respetando los márgenes y saltos de línea."""
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 12)
    y = 750
    x = 50
    line_height = 12
    max_line_width = 510
    bottom_margin = 80  # Ajustado para mayor espacio

    patron_notam = re.compile(r"^A\d{3,4}/\d{4}")  # Detecta Axxx/xxxx o Axxxx/xxxx

    for codigo, texto_notams in resultados.items():
        p.drawString(x, y, f"NOTAMs para {codigo}:")
        y -= 20
        p.setFont("Helvetica", 10)

        notams = texto_notams.strip().split('\n\n')

        for notam in notams:
            lines = notam.strip().split('\n')

            for line in lines:
                # **Si la línea inicia con "Axxx/xxxx" o "Axxxx/xxxx", agregar un salto de línea antes**
                if patron_notam.match(line.strip()):
                    y -= 15  # Espacio moderado para mejorar visibilidad

                if y < bottom_margin + 20:  # Evita que el contenido sobresalga en el pie de página
                    p.showPage()
                    p.setFont("Helvetica", 10)
                    y = 750
                
                words = line.strip().split()
                line_buffer = ""

                for word in words:
                    if p.stringWidth(line_buffer + word, "Helvetica", 10) < max_line_width:
                        line_buffer += word + " "
                    else:
                        p.drawString(x, y, line_buffer.strip())
                        y -= line_height
                        line_buffer = word + " "

                if line_buffer:
                    p.drawString(x, y, line_buffer.strip())
                    y -= line_height

            y -= 30  # Espacio entre NOTAMs para mejor lectura

        p.setFont("Helvetica-Bold", 12)
        y -= 20
        if y < bottom_margin + 20:
            p.showPage()
            p.setFont("Helvetica-Bold", 12)
            y = 750

    p.save()
    buffer.seek(0)
    return buffer

    
# ========== CONFIG STREAMLIT ==========
st.set_page_config(page_title="Buscador de NOTAMs", layout="centered", page_icon="🛫")
st.title("🔎 Buscador de NOTAMs")
st.markdown("**Creado por Fernandez Milton**")

# Animación de avión
with st.spinner('Iniciando sistema...'):
    st.markdown("""
    <style>
    .airplane {
        animation: fly 5s ease-in-out infinite alternate;
        display: inline-block;
        font-size: 36px;
    }
    @keyframes fly {
        from { transform: translateX(0); }
        to { transform: translateX(30px); }
    }
    </style>
    <div class="airplane">✈️</div>
    """, unsafe_allow_html=True)
# Crear un checkbox para simular la ventana modal
if st.checkbox("ℹ️ Abrir Ayuda"):
    # Dentro de la ventana modal, mostrar el contenido de ayuda
    st.markdown("""
    <div style="background-color: #f1f1f1; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);">
        
        🌐 Avisos FIR:
        
            AVTD ➜ Todas las FIRs
            SAVF ➜ FIR Comodoro
            SACF ➜ FIR Córdoba
            SAEF ➜ FIR Ezeiza
            SAMF ➜ FIR Mendoza
            SAAR ➜ FIR Resistencia
        
        
        📬 Consultas o sugerencias:
        milton.fernandez1993@gmail.com
    </div>
    """, unsafe_allow_html=True)
# ========== INTERFAZ ==========

# Input aeropuertos
aeropuertos_input = st.text_input("Ingresá los códigos OACI separados por coma:",
                                  st.session_state.get("aeropuertos", ""))
st.session_state.aeropuertos = aeropuertos_input

if st.button("Buscar NOTAMs"):
    aeropuertos = [a.strip().upper() for a in aeropuertos_input.split(",") if a.strip()]
    total = len(aeropuertos)
    resultados = {}

    options = Options()
    options.add_argument('--headless')
    options.add_argument('--disable-gpu')
    options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
    driver.get("https://ais.anac.gov.ar/notam")

    progress = st.progress(0)
    progreso_texto = st.empty()

    progreso_texto.text(f"Buscando NOTAMs...")

    for i, codigo in enumerate(aeropuertos):
        nombre = get_airport_name(codigo)
        try:
            resultado = buscar_notam(nombre)
            resultados[codigo] = resultado
        except Exception as e:
            resultados[codigo] = f"Error buscando NOTAM para {codigo}: {str(e)}"

        porcentaje = (i + 1) / total
        progress.progress(porcentaje)
        progreso_texto.text(f"Buscando {i+1} de {total} - {codigo}")

    driver.quit()

    st.success("Búsqueda finalizada")
    st.markdown("---")

    # Generar el PDF
    pdf_buffer = generar_pdf_notam(resultados)

    # Ofrecer la descarga del PDF
    st.download_button(
        label="Descargar NOTAMs en PDF",
        data=pdf_buffer,
        file_name="NOTAMs_resultado.pdf",
        mime="application/pdf"
    )

    # Opcional: Mostrar los resultados en la app (como antes)
    for codigo, resultado in resultados.items():
        st.markdown(f"### {codigo}")
        st.text(resultado)
