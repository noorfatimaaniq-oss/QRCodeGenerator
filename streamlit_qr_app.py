import streamlit as st
import qrcode
from qrcode.constants import ERROR_CORRECT_H
from PIL import Image
import io
import csv
import zipfile
from datetime import datetime
import qrcode.image.svg

# ----------------- Page Config -----------------
st.set_page_config(
    page_title="NOFA QR Code Generator",
    layout="wide"
)

st.markdown(
    "<h1 style='text-align:center;color:#1E3A8A;'>NOFA QR Code Generator</h1>",
    unsafe_allow_html=True
)

# ----------------- Session State -----------------
if "qr_images" not in st.session_state:
    st.session_state.qr_images = []

if "qr_data_list" not in st.session_state:
    st.session_state.qr_data_list = []

# ----------------- QR Generator -----------------
def generate_qr(qr_data, qr_color, bg_color, logo_file=None):
    qr = qrcode.QRCode(
        version=1,
        error_correction=ERROR_CORRECT_H,
        box_size=10,
        border=4
    )
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(
        fill_color=qr_color,
        back_color=bg_color
    ).convert("RGB")

    if logo_file:
        logo = Image.open(logo_file).convert("RGBA")
        size = img.size[0] // 4
        logo = logo.resize((size, size))
        pos = ((img.size[0] - size) // 2, (img.size[1] - size) // 2)
        img.paste(logo, pos, logo)

    return img

# ----------------- Sidebar -----------------
with st.sidebar:
    st.markdown("## QR Settings")

    qr_type = st.selectbox(
        "QR Type",
        ["Text/URL", "Wi-Fi", "VCard", "Batch"]
    )

    qr_color = st.color_picker("QR Color", "#000000")
    bg_color = st.color_picker("Background", "#FFFFFF")

    logo_file = st.file_uploader(
        "Optional Logo",
        type=["png", "jpg", "jpeg"]
    )

    st.markdown("---")

    data = None
    batch_file = None

    if qr_type == "Text/URL":
        data = st.text_input("Enter URL or Text")

    elif qr_type == "Wi-Fi":
        ssid = st.text_input("SSID")
        password = st.text_input("Password")
        if ssid and password:
            data = f"WIFI:T:WPA;S:{ssid};P:{password};;"

    elif qr_type == "VCard":
        name = st.text_input("Name")
        phone = st.text_input("Phone")
        email = st.text_input("Email")
        if name and phone and email:
            data = f"""BEGIN:VCARD
VERSION:3.0
N:{name}
TEL:{phone}
EMAIL:{email}
END:VCARD"""

    elif qr_type == "Batch":
        batch_file = st.file_uploader("Upload TXT / CSV", type=["txt", "csv"])

    generate = st.button("Generate QR")
    reset = st.button("Reset")

# ----------------- Logic -----------------
if generate:
    st.session_state.qr_images = []
    st.session_state.qr_data_list = []

    if qr_type == "Batch" and batch_file:
        lines = batch_file.getvalue().decode().splitlines()
        if batch_file.name.endswith(".csv"):
            reader = csv.reader(lines)
            for row in reader:
                if row:
                    st.session_state.qr_data_list.append(row[0])
        else:
            st.session_state.qr_data_list = lines
    elif data:
        st.session_state.qr_data_list = [data]

    for q in st.session_state.qr_data_list:
        img = generate_qr(q, qr_color, bg_color, logo_file)
        st.session_state.qr_images.append(img)

if reset:
    st.session_state.qr_images = []
    st.session_state.qr_data_list = []

# ----------------- Preview -----------------
if st.session_state.qr_images:
    st.markdown("## Generated QR Codes")

    cols = st.columns(3)

    for i, img in enumerate(st.session_state.qr_images):
        with cols[i % 3]:
            st.image(img, width=300)

            # --- Format Selector ---
            format_option = st.selectbox(
                "Select Format",
                ["PNG", "SVG"],
                key=f"format_{i}"
            )

            download_buf = io.BytesIO()
            file_name = f"qr_{i+1}"

            if format_option == "PNG":
                img.save(download_buf, format="PNG")
                mime_type = "image/png"
                file_name += ".png"

            else:  # SVG
                factory = qrcode.image.svg.SvgImage
                svg_img = qrcode.make(
                    st.session_state.qr_data_list[i],
                    image_factory=factory
                )
                svg_img.save(download_buf)
                mime_type = "image/svg+xml"
                file_name += ".svg"

            st.download_button(
                "Download",
                download_buf.getvalue(),
                file_name,
                mime_type
            )

    # -------- ZIP Download (PNG only – standard) --------
    if len(st.session_state.qr_images) > 1:
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w") as zf:
            for i, img in enumerate(st.session_state.qr_images):
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                zf.writestr(f"qr_{i+1}.png", buf.getvalue())

        st.download_button(
            "Download All QR Codes (ZIP)",
            zip_buf.getvalue(),
            "qr_codes.zip",
            "application/zip"
        )
