import streamlit as st
import pypdf
from PIL import Image
import fitz  # PyMuPDF
import tempfile

# 文清風格樣式
def set_style():
    st.markdown("""
    <style>
    body {
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

# 產生縮圖
def generate_thumbnail(pdf_path, page_num):
    doc = fitz.open(pdf_path)
    page = doc.load_page(page_num)
    pix = page.get_pixmap(matrix=fitz.Matrix(0.4, 0.4))
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    return img

# 旋轉頁面
def rotate_pdf(pdf_path, page_num, angle):
    reader = pypdf.PdfReader(pdf_path)
    writer = pypdf.PdfWriter()
    for i, page in enumerate(reader.pages):
        if i == page_num:
            page.rotate(angle)
        writer.add_page(page)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        writer.write(temp)
        return temp.name

# 刪除頁面
def delete_page(pdf_path, page_num):
    reader = pypdf.PdfReader(pdf_path)
    writer = pypdf.PdfWriter()
    for i, page in enumerate(reader.pages):
        if i != page_num:
            writer.add_page(page)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        writer.write(temp)
        return temp.name

# 重新排序頁面
def reorder_pdf(pdf_path, new_order):
    reader = pypdf.PdfReader(pdf_path)
    writer = pypdf.PdfWriter()
    for idx in new_order:
        writer.add_page(reader.pages[idx])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        writer.write(temp)
        return temp.name

# 合併 PDF 文件
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
        # 儲存所有上傳的 PDF 文件
        pdf_paths = []
        for uploaded_file in uploaded_files:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                tmp.write(uploaded_file.read())
                pdf_paths.append(tmp.name)

        # 顯示所有頁面縮圖
        thumbnails = [generate_thumbnail(pdf_paths[0], i) for i in range(len(pypdf.PdfReader(pdf_paths[0]).pages))]
        actions = []
        rotation_angles = []

        st.subheader("🖼 預覽與操作")
        for i in range(0, len(thumbnails), 6):
            cols = st.columns(6)
            for j in range(6):
                idx = i + j
                if idx < len(thumbnails):
                    with cols[j]:
                        st.image(thumbnails[idx], use_container_width=True)
                        action = st.radio(
                            f"頁面 {idx+1}",
                            ['無動作', '旋轉', '刪除'],
                            key=f"action_{idx}"
                        )
                        actions.append(action)

                        if action == '旋轉':
                            angle = st.selectbox(
                                f"旋轉角度 (頁面 {idx+1})",
                                [90, 180, 270],
                                index=0,
                                key=f"angle_{idx}"
                            )
                            rotation_angles.append((idx, angle))
                        else:
                            rotation_angles.append((idx, 0))

        # 執行刪除
        for idx, action in enumerate(actions):
            if action == '刪除':
                pdf_paths[0] = delete_page(pdf_paths[0], idx)
                st.success(f"頁面 {idx+1} 已刪除")

        # 執行旋轉
        for idx, angle in rotation_angles:
            if angle != 0:
                pdf_paths[0] = rotate_pdf(pdf_paths[0], idx, angle)
                st.success(f"頁面 {idx+1} 已旋轉 {angle} 度")

        # 重新排序頁面
        st.subheader("🔀 重新排序頁面")
        page_order = list(range(len(pypdf.PdfReader(pdf_paths[0]).pages)))
        
        # 更新為選擇頁面順序
        reordered = st.multiselect(
            "請選擇頁面順序 (拖動排序)",
            options=page_order,
            format_func=lambda x: f"頁面 {x+1}",
            key="reorder_selectbox"
        )
        
        if reordered != page_order:
            pdf_paths[0] = reorder_pdf(pdf_paths[0], reordered)
            st.success("✅ 頁面順序已更新")

        # 合併選項
        if len(uploaded_files) > 1:
            st.subheader("📄 合併多個 PDF 文件")
            if st.button("合併文件"):
                merged_pdf = merge_pdfs(pdf_paths)
                st.success("✅ 合併完成")

                # 下載合併後的 PDF 文件
                with open(merged_pdf, "rb") as f:
                    st.download_button("📥 下載合併後的 PDF", f, file_name="merged.pdf")

        # 下載編輯後的 PDF 文件
        with open(pdf_paths[0], "rb") as f:
            st.download_button("📥 下載編輯後的 PDF", f, file_name="edited.pdf")

if __name__ == "__main__":
    main()
