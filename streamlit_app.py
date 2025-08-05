import streamlit as st
import pdfplumber
import re
import io

st.set_page_config(page_title="PDF Koordinat Çıkarıcı", layout="centered")
st.title("📍 PDF Koordinat Çıkarıcı")
st.markdown("Tüm sahaları otomatik çeken araç: `N° d'appui`, `Adresse`, `Commune`, `Code INSEE`, `Hauteur`, `Composite`, `Niveau`, `Environnements`, `Koordinatlar`, `Google Maps`")

uploaded_file = st.file_uploader("📄 PDF dosyasını yükle", type=["pdf"])

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

            # Koordinat eşleşmesi
            matches = re.findall(
                r"N° d'appui\s+(\d+).*?Latitude\s+([\d°'\.\"]+[NS]).*?Longitude\s+([\d°'\.\"]+[EO])",
                text,
                re.DOTALL
            )

            # Diğer alanlar (toleranslı)
            def extract(pattern, default="-"):
                result = re.search(pattern, text, re.IGNORECASE)
                return result.group(1).strip() if result else default

            adresse = extract(r"Adresse\s*[:\-]?\s*(.+)")
            commune = extract(r"Commune\s*[:\-]?\s*(.+)")
            code_insee = extract(r"Code INSEE\s*[:\-]?\s*(\d{5})")
            hauteur = extract(r"Hauteur\s*[:\-]?\s*([\d.,]+ ?m)")
            composite = extract(r"Composite\s*[:\-]?\s*(Oui|Non)")
            niveau = extract(r"(R\+?\d+|R0|R1)")
            environnements_raw = extract(r"Environnement[s]*\s*[:\-]?\s*(.+)")

            environnements_list = [e.strip() for e in environnements_raw.split(",")] if environnements_raw != "-" else ["-"]

            for appui, lat, lon in matches:
                lat_decimal = dms_to_decimal(lat)
                lon_decimal = dms_to_decimal(lon)
                maps_link = f"https://www.google.com/maps?q={lat_decimal},{lon_decimal}" if lat_decimal and lon_decimal else ""

                result = {
                    "dosya": uploaded_file.name,
                    "appui": appui,
                    "adresse": adresse,
                    "commune": commune,
                    "code_insee": code_insee,
                    "hauteur": hauteur,
                    "composite": composite,
                    "niveau": niveau,
                    "environnements": environnements_list,
                    "latitude": lat,
                    "longitude": lon,
                    "maps_link": maps_link
                }
                results.append(result)

    if results:
        st.success(f"{len(results)} sonuç bulundu.")

        output_text = io.StringIO()
        for r in results:
            envs = ", ".join(r["environnements"])
            st.markdown(f"""
**📁 Dosya:** {r['dosya']}  
**N° d'appui:** {r['appui']}  
**Adresse:** {r['adresse']}  
**Commune:** {r['commune']}  
**Code INSEE:** {r['code_insee']}  
**Hauteur:** {r['hauteur']}  
**Composite:** {r['composite']}  
**Niveau:** {r['niveau']}  
**Environnements:** {envs}  
**Latitude:** {r['latitude']}  
**Longitude:** {r['longitude']}  
🔗 [Google Maps]({r['maps_link']})  
---
""")

            output_text.write(f"""📁 Dosya: {r['dosya']}
N° d'appui: {r['appui']}
Adresse: {r['adresse']}
Commune: {r['commune']}
Code INSEE: {r['code_insee']}
Hauteur: {r['hauteur']}
Composite: {r['composite']}
Niveau: {r['niveau']}
Environnements: {envs}
Latitude: {r['latitude']}
Longitude: {r['longitude']}
Google Maps: {r['maps_link']}
{'-'*50}\n\n""")

        st.download_button("⬇️ TXT Dosyasını İndir", output_text.getvalue(), file_name="output.txt")
    else:
        st.warning("❌ Veri bulunamadı. PDF formatını kontrol et.")
