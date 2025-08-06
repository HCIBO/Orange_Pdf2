import streamlit as st
import pdfplumber
import re
import io

st.set_page_config(page_title="Extracteur de Coordonnées PDF", layout="centered")
st.title("📍 Extracteur de Coordonnées PDF par HamitCIBO")
st.markdown("Un outil simple et efficace pour extraire les informations nécessaires.")

uploaded_file = st.file_uploader("📄 Téléversez un fichier PDF", type=["pdf"])

def dms_to_decimal(coord):
    match = re.match(r"(\d+)°(\d+)'([\d.]+)\"?([NSEW])", coord)
    if not match:
        return None
    deg, minutes, seconds, direction = match.groups()
    decimal = float(deg) + float(minutes)/60 + float(seconds)/3600
    if direction in ['S', 'W']:
        decimal *= -1
    return round(decimal, 6)

if uploaded_file is not None:
    with pdfplumber.open(uploaded_file) as pdf:
        results = []
        for page in pdf.pages:
            text = page.extract_text()
            if not text:
                continue

            matches = re.findall(
                r"N° d'appui\s+(\d+).*?Latitude\s+([\d°'\.\"]+[NS]).*?Longitude\s+([\d°'\.\"]+[EO])",
                text,
                re.DOTALL
            )

            def extract(pattern, default="-"):
                result = re.search(pattern, text, re.IGNORECASE)
                return result.group(1).strip() if result else default

            adresse = extract(r"Adresse\s*[:\-]?\s*(.+)")
            commune = extract(r"Commune\s*[:\-]?\s*(.+)")
            code_insee = extract(r"Code INSEE\s*[:\-]?\s*(\d{5})")

            for appui, lat, lon in matches:
                lat_decimal = dms_to_decimal(lat)
                lon_decimal = dms_to_decimal(lon)
                maps_link = f"https://www.google.com/maps?q={lat_decimal},{lon_decimal}" if lat_decimal and lon_decimal else ""

                result = {
                    "fichier": uploaded_file.name,
                    "appui": appui,
                    "adresse": adresse,
                    "commune": commune,
                    "code_insee": code_insee,
                    "latitude": lat,
                    "longitude": lon,
                    "maps_link": maps_link
                }
                results.append(result)

    if results:
        st.success(f"{len(results)} résultat(s) trouvé(s).")

        output_text = io.StringIO()
        for r in results:
            st.markdown(f"""
**📁 Fichier :** {r['fichier']}  
**N° d'appui :** {r['appui']}  
**Adresse :** {r['adresse']}  
**Commune :** {r['commune']}  
**Code INSEE :** {r['code_insee']}  
**Latitude :** {r['latitude']}  
**Longitude :** {r['longitude']}  
🔗 [Google Maps]({r['maps_link']})  
---
""")

            output_text.write(f"""📁 Fichier : {r['fichier']}
N° d'appui : {r['appui']}
Adresse : {r['adresse']}
Commune : {r['commune']}
Code INSEE : {r['code_insee']}
Latitude : {r['latitude']}
Longitude : {r['longitude']}
Google Maps : {r['maps_link']}
{'-'*50}\n\n""")

        st.download_button("⬇️ Télécharger le fichier TXT", output_text.getvalue(), file_name="coordonnees.txt")
    else:
        st.warning("❌ Aucune donnée trouvée. Veuillez vérifier le format du PDF.")
