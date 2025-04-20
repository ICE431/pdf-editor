import streamlit as st
from pypdf import PdfReader, PdfWriter
import fitz  # PyMuPDF
from PIL import Image
import tempfile

st.set_page_config(page_title="PDF 編輯器", page_icon="📄")
st.title("📄 PDF 可視化編輯工具（支援合併與刪除）")

uploaded_files = st.file_uploader("📤 上傳 PDF（可多選）", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_pages = []
    page_labels = []

    st.header("👀 預覽 PDF 頁面")
    
    for uploaded_file in uploaded_files:
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        uploaded_file.seek(0)  # 重設指標
        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=100)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            label = f"{uploaded_file.name} - 第 {i+1} 頁"
            st.image(img, caption=label, use_column_width=True)

            all_pages.append((uploaded_file.name, uploaded_file, i))  # 儲存檔案名、檔案本體與頁碼
            page_labels.append(label)

    # 多選要刪除的頁面
    pages_to_remove = st.multiselect("❌ 選擇要刪除的頁面", page_labels)

    if st.button("📎 合併 PDF"):
        writer = PdfWriter()

        for name, file, page_num in all_pages:
            label = f"{name} - 第 {page_num+1} 頁"
            if label not in pages_to_remove:
                file.seek(0)
                reader = PdfReader(file)
                writer.add_page(reader.pages[page_num])

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            writer.write(tmp_file.name)
            with open(tmp_file.name, "rb") as f:
                st.success("✅ 合併完成！")
                st.download_button("📥 下載合併後的 PDF", f, file_name="merged.pdf")
