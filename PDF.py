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

# 旋轉頁面
def rotate_pages(pdf_path, rotate_actions):
    reader = pypdf.PdfReader(pdf_path)
    writer = pypdf.PdfWriter()
    for i, page in enumerate(reader.pages):
        if i in rotate_actions:
            page.rotate_clockwise(rotate_actions[i])
        writer.add_page(page)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        writer.write(temp)
        return temp.name

# 重新排序
def reorder_pdf_pages(pdf_path, new_order):
    reader = pypdf.PdfReader(pdf_path)
    writer = pypdf.PdfWriter()
    for i in new_order:
        writer.add_page(reader.pages[i])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        writer.write(temp)
        return temp.name

# 合併 PDF
def merge_pdfs(pdf_paths):
    writer = pypdf.PdfWriter()
    for path in pdf_paths:
        reader = pypdf.PdfReader(path)
        for page in reader.pages:
            writer.add_page(page)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        writer.write(temp)
        return temp.name

# 主介面
def main():
    set_style()
    st.title("📄 PDF 編輯器")

    uploaded_files = st.file_uploader("請上傳 PDF 文件", type="pdf", accept_multiple_files=True)

    if uploaded_files:
        pdf_paths = []
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                pdf_paths.append(tmp.name)

        st.subheader("🖼 預覽與操作")
        all_actions = []
        thumbnails_all = []

        for pdf_index, pdf_path in enumerate(pdf_paths):
            reader = pypdf.PdfReader(pdf_path)
            thumbnails = generate_thumbnails_once(pdf_path)
            thumbnails_all.append((pdf_path, thumbnails, len(reader.pages)))

        pages_to_delete = {}
        rotate_actions = {}

        for pdf_path, thumbnails, total_pages in thumbnails_all:
            for i in range(0, total_pages, 6):
                cols = st.columns(6)
                for j in range(6):
                    idx = i + j
                    if idx < total_pages:
                        with cols[j]:
                            st.image(thumbnails[idx], use_container_width=True)
                            action = st.radio(
                                f"頁面 {idx+1}",
                                ['無動作', '刪除', '旋轉'],
                                key=f"action_{pdf_path}_{idx}"
                            )

                            if action == '刪除':
                                pages_to_delete.setdefault(pdf_path, []).append(idx)
                            elif action == '旋轉':
                                angle = st.selectbox(
                                    f"旋轉角度 (頁面 {idx+1})",
                                    [90, 180, 270],
                                    key=f"angle_{pdf_path}_{idx}"
                                )
                                rotate_actions.setdefault(pdf_path, {})[idx] = angle

        # 套用刪除與旋轉操作
        updated_pdf_paths = []
        for original_path in pdf_paths:
            temp_path = original_path
            if original_path in pages_to_delete:
                temp_path = delete_pages(temp_path, pages_to_delete[original_path])
            if original_path in rotate_actions:
                temp_path = rotate_pages(temp_path, rotate_actions[original_path])
            updated_pdf_paths.append(temp_path)

        # 取得所有頁面的資訊供排序使用
        all_pages = []
        for path in updated_pdf_paths:
            reader = pypdf.PdfReader(path)
            for idx in range(len(reader.pages)):
                all_pages.append((path, idx))

        st.subheader("🔀 重新排序所有 PDF 頁面")
        page_order = list(range(len(all_pages)))
        reordered = st.multiselect(
            "請選擇所有頁面順序",
            options=page_order,
            format_func=lambda x: f"頁面 {x+1}",
            key="reorder_selectbox"
        )

        if reordered:
            # 將所有選擇的頁面順序組成新 PDF
            writer = pypdf.PdfWriter()
            for idx in reordered:
                pdf_path, page_num = all_pages[idx]
                reader = pypdf.PdfReader(pdf_path)
                writer.add_page(reader.pages[page_num])
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
                writer.write(temp)
                st.success("✅ 頁面順序已更新")
                with open(temp.name, "rb") as f:
                    st.download_button("📥 下載編輯後的 PDF", f, file_name="edited_sorted.pdf")

        if len(updated_pdf_paths) > 1:
            st.subheader("📄 合併多個 PDF 文件")
            if st.button("合併文件"):
                merged_pdf = merge_pdfs(updated_pdf_paths)
                st.success("✅ 合併完成")
                with open(merged_pdf, "rb") as f:
                    st.download_button("📥 下載合併後的 PDF", f, file_name="merged_sorted.pdf")

        st.info("🔧 所有操作（刪除、旋轉、排序）完成後，請下載或合併輸出 PDF。")

if __name__ == "__main__":
    main()
