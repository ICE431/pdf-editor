import streamlit as st
import pypdf
from PIL import Image
import fitz  # PyMuPDF
import tempfile

# 文清風格樣式
def set_style():
    st.markdown("""
    <style>
    .stApp {
        background-color: #f9f9f9;
        font-family: "Noto Sans TC", sans-serif;
    }
    .stButton>button {
        background-color: #6a9dff;
        color: white;
        font-size: 16px;
        border-radius: 6px;
        padding: 6px 12px;
    }
    .stSelectbox>div>div {
        background-color: #eef3fa;
    }
    </style>
    """, unsafe_allow_html=True)

# 一次產生所有縮圖
def generate_thumbnails_once(pdf_path):
    doc = fitz.open(pdf_path)
    thumbnails = []
    for i in range(len(doc)):
        page = doc.load_page(i)
        pix = page.get_pixmap(matrix=fitz.Matrix(0.4, 0.4))
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        img.thumbnail((300, 300))
        thumbnails.append(img)
    return thumbnails

# 刪除頁面
def delete_pages(pdf_path, pages_to_delete):
    reader = pypdf.PdfReader(pdf_path)
    writer = pypdf.PdfWriter()
    for i, page in enumerate(reader.pages):
        if i not in pages_to_delete:
            writer.add_page(page)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        writer.write(temp)
        return temp.name

# 合併 + 重新排序
def merge_and_reorder_pages(pages):
    writer = pypdf.PdfWriter()
    for pdf_path, page_num in pages:
        reader = pypdf.PdfReader(pdf_path)
        writer.add_page(reader.pages[page_num])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        writer.write(temp)
        return temp.name

# 主介面
def main():
    set_style()
    st.title("📄 PDF 編輯器（刪除 / 合併 / 重新排序）")

    uploaded_files = st.file_uploader("請上傳一個或多個 PDF 文件", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        # 儲存上傳的檔案
        pdf_paths = []
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                pdf_paths.append(tmp.name)

        st.subheader("🖼 預覽與刪除")
        pages_to_keep = []  # 所有要保留的頁面 (for排序與合併)
        thumbnails_all = []

        for pdf_path in pdf_paths:
            reader = pypdf.PdfReader(pdf_path)
            thumbnails = generate_thumbnails_once(pdf_path)
            thumbnails_all.append((pdf_path, thumbnails, len(reader.pages)))

        for pdf_path, thumbnails, total_pages in thumbnails_all:
            for i in range(0, total_pages, 6):
                cols = st.columns(6)
                for j in range(6):
                    idx = i + j
                    if idx < total_pages:
                        with cols[j]:
                            st.image(thumbnails[idx], use_container_width=True)
                            keep = st.checkbox(f"保留頁面 {idx+1}", value=True, key=f"{pdf_path}_{idx}")
                            if keep:
                                pages_to_keep.append((pdf_path, idx))

        if not pages_to_keep:
            st.warning("請至少保留一個頁面。")
            return

        st.subheader("🔀 重新排序 + 合併 PDF")
        default_order = list(range(len(pages_to_keep)))
        reordered = st.multiselect(
            "請選擇輸出頁面順序",
            options=default_order,
            format_func=lambda x: f"{x+1}: PDF第 {pages_to_keep[x][1]+1} 頁",
            default=default_order
        )

        if reordered:
            sorted_pages = [pages_to_keep[i] for i in reordered]
            merged_pdf = merge_and_reorder_pages(sorted_pages)
            st.success("✅ 已重新排序並合併頁面")
            with open(merged_pdf, "rb") as f:
                st.download_button("📥 下載最終 PDF", f, file_name="merged_reordered.pdf")

if __name__ == "__main__":
    main()
