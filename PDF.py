import streamlit as st
from pypdf import PdfReader, PdfWriter
import fitz  # PyMuPDF
from PIL import Image
import tempfile

st.set_page_config(page_title="PDF 編輯器", page_icon="📄", layout="wide")
st.title("📄 PDF 可視化編輯工具（預覽、刪除、旋轉）")

uploaded_files = st.file_uploader("📤 上傳 PDF（可多選）", type="pdf", accept_multiple_files=True)

if uploaded_files:
    st.header("👀 預覽並操作每一頁")
    all_pages = []
    remove_flags = []
    rotate_flags = []

    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        uploaded_file.seek(0)

        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=70)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            label = f"{file_name} - 第 {i+1} 頁"
            col1, col2 = st.columns([2, 1])
            with col1:
                st.image(img, caption=label, use_column_width=True)

            # 使用者對每頁的控制選項
            with col2:
                remove = st.checkbox(f"刪除這一頁", key=f"remove_{file_name}_{i}")
                rotate = st.button(f"🔄 旋轉 90°", key=f"rotate_{file_name}_{i}")

            # 儲存控制資訊
            all_pages.append((file_name, uploaded_file, i))
            remove_flags.append(remove)
            rotate_flags.append(rotate)

    if st.button("📎 合併 PDF"):
        writer = PdfWriter()

        for idx, (name, file, page_num) in enumerate(all_pages):
            if remove_flags[idx]:
                continue  # 使用者打勾刪除這一頁

            file.seek(0)
            reader = PdfReader(file)
            page = reader.pages[page_num]

            # 檢查是否需要旋轉
            if rotate_flags[idx]:
                page.rotate(90)  # rotate clockwise 90°

            writer.add_page(page)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            writer.write(tmp_file.name)
            with open(tmp_file.name, "rb") as f:
                st.success("✅ 合併完成！")
                st.download_button("📥 下載合併後的 PDF", f, file_name="merged.pdf")

