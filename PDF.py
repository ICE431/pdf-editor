# 安裝依賴套件（只需執行一次）
# pip install streamlit pypdf

import streamlit as st
from pypdf import PdfReader, PdfWriter
import tempfile

st.set_page_config(page_title="PDF 編輯器", page_icon="📄")
st.title("📄 線上 PDF 編輯工具")
st.markdown("上傳多個 PDF，選擇要移除的頁面，然後合併下載。")

uploaded_files = st.file_uploader("📤 上傳 PDF 檔案（可多選）", type="pdf", accept_multiple_files=True)

if uploaded_files:
    all_pages = []
    file_page_refs = []

    # 擷取所有 PDF 頁面，並列出讓使用者選擇刪除
    for idx, file in enumerate(uploaded_files):
        reader = PdfReader(file)
        for i, page in enumerate(reader.pages):
            label = f"{file.name} - 第 {i+1} 頁"
            all_pages.append((file, i))
            file_page_refs.append(label)

    # 多選要「刪除」的頁面
    pages_to_remove = st.multiselect("❌ 選擇你要刪除的頁面", file_page_refs)

    # 合併按鈕
    if st.button("📎 合併 PDF"):
        writer = PdfWriter()

        for file, page_num in all_pages:
            label = f"{file.name} - 第 {page_num+1} 頁"
            if label not in pages_to_remove:
                reader = PdfReader(file)
                writer.add_page(reader.pages[page_num])

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            writer.write(tmp_file.name)

            with open(tmp_file.name, "rb") as f:
                st.success("✅ 合併完成！")
                st.download_button("📥 下載合併後的 PDF", f, file_name="merged.pdf")
