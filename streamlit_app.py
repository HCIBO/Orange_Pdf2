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

            matches = re.findall(
                r"N° d'appui\s+(\d+).*?Latitude\s+([\d°'\.\"]+[NS]).*?Longitude\s+([\d°'\.\"]+[EO])",
                text,
                re.DOTALL
            )

            adresse = re.search(r"[Aa]dresse\s*[:\-]?\s*(.+)", text)
            commune = re.search(r"[Cc]ommune\s*[:\-]?\s*(.+)", text)
            code_insee = re.search(r"[Cc]ode INSEE\s*[:\-]?\s*(\d{5})", text)
            hauteur = re.search(r"[Hh]auteur\s*[:\-]?\s*([\d,.]+ ?m)", text)
            composite = re.search(r"[Cc]omposite\s*[:\-]?\s*(Oui|Non)", text)
            niveau = re.search(r"(R\+?\d+|R0|R1)", text)
            environnements = re.search(r"[Ee]nvironnement[s]*\s*[:\-]?\s*(.+)", text)

            for appui, lat, lon in matches:
                lat_decimal = dms_to_decimal(lat)
                lon_decimal = dms_to_decimal(lon)
                maps_link = f"https://www.google.com/maps?q={lat_decimal},{lon_decimal}" if lat_decimal and lon_decimal else ""

                result = {
                    "dosya": uploaded_file.name,
                    "appui": appui,
                    "adresse": adresse.group(1).strip() if adresse else "-",
                    "commune": commune.group(1).strip() if commune else "-",
                    "code_insee": code_insee.group(1).strip() if code_insee else "-",
                    "hauteur": hauteur.group(1).strip() if hauteur else "-",
                    "composite": composite.group(1).strip() if composite else "-",
                    "niveau": niveau.group(1).strip() if niveau else "-",
                    "environnements": environnements.group(1).strip() if environnements else "-",
                    "latitude": lat,
                    "longitude": lon,
                    "maps_link": maps_link
                }
                results.append(result)

    if results:
        st.success(f"{len(results)} sonuç bulundu.")

        output_text = io.StringIO()
        for r in results:
            st.markdown(f"""
**📁 Dosya:** {r['dosya']}  
**N° d'appui:** {r['appui']}  
**Adresse:** {r['adresse']}  
**Commune:** {r['commune']}  
**Code INSEE:** {r['code_insee']}  
**Hauteur:** {r['hauteur']}  
**Composite:** {r['composite']}  
**Niveau:** {r['niveau']}  
**Environnements:** {r['environnements']}  
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
Environnements: {r['environnements']}
Latitude: {r['latitude']}
Longitude: {r['longitude']}
Google Maps: {r['maps_link']}
{'-'*50}\n\n""")

        st.download_button("⬇️ TXT Dosyasını İndir", output_text.getvalue(), file_name="output.txt")

    else:
        st.warning("❌ Veri bulunamadı. PDF formatını kontrol et.")
