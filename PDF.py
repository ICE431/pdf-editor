import streamlit as st
from pypdf import PdfReader, PdfWriter
from pdf2image import convert_from_bytes
import tempfile

st.set_page_config(page_title="PDF 編輯器", page_icon="📄")
st.title("📄 PDF 可視化編輯工具")
st.markdown("上傳 PDF，選擇要移除的頁面，預覽後合併下載。")

uploaded_files = st.file_uploader("📤 上傳 PDF（可多選）", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_pages = []
    file_page_refs = []
    preview_thumbnails = []

    st.header("👀 PDF 預覽與選擇")

    for idx, uploaded_file in enumerate(uploaded_files):
        pdf_name = uploaded_file.name
        images = convert_from_bytes(uploaded_file.read(), dpi=100)
        
        # 必須重新打開 PDF 用於後續處理
        uploaded_file.seek(0)
        reader = PdfReader(uploaded_file)

        for i, img in enumerate(images):
            page_label = f"{pdf_name} - 第 {i+1} 頁"
            st.image(img, caption=page_label, use_column_width=True)
            all_pages.append((uploaded_file, i))  # 記錄檔案與頁碼
            file_page_refs.append(page_label)
            preview_thumbnails.append(img)

    # ✅ 勾選要刪除的頁面
    pages_to_remove = st.multiselect("❌ 選擇你要刪除的頁面", file_page_refs)

    # ✅ 合併按鈕
    if st.button("📎 合併 PDF"):
        writer = PdfWriter()

        for file, page_num in all_pages:
            label = f"{file.name} - 第 {page_num+1} 頁"
            if label not in pages_to_remove:
                file.seek(0)  # 每次重新開啟
                reader = PdfReader(file)
                writer.add_page(reader.pages[page_num])

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            writer.write(tmp_file.name)

            with open(tmp_file.name, "rb") as f:
                st.success("✅ 合併完成！")
                st.download_button("📥 下載合併後的 PDF", f, file_name="merged.pdf")
