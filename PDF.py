import streamlit as st
import pypdf
from PIL import Image
import fitz  # PyMuPDF
import tempfile
from st_draggable_list import DraggableList

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

# 依新順序重排 PDF
def reorder_pdf(pdf_path, new_order):
    reader = pypdf.PdfReader(pdf_path)
    writer = pypdf.PdfWriter()
    for idx in new_order:
        writer.add_page(reader.pages[idx])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        writer.write(temp)
        return temp.name

# 主介面
def main():
    set_style()
    st.title("📄 PDF 編輯器")

    uploaded_file = st.file_uploader("請上傳 PDF 文件", type="pdf")

    if uploaded_file:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            pdf_path = tmp.name

        reader = pypdf.PdfReader(pdf_path)
        num_pages = len(reader.pages)

        # 產生縮圖 & UI
        st.subheader("🖼 預覽與操作")
        actions = [None] * num_pages
        angles = [0] * num_pages

        for i in range(0, num_pages, 6):
            cols = st.columns(6)
            for j in range(6):
                idx = i + j
                if idx < num_pages:
                    with cols[j]:
                        try:
                            thumbnail = generate_thumbnail(pdf_path, idx)
                            st.image(thumbnail, use_container_width=True)
                        except:
                            st.warning(f"無法載入頁面 {idx+1} 預覽")

                        action = st.radio(f"頁面 {idx+1}", ["無動作", "旋轉", "刪除"], key=f"action_{idx}")
                        actions[idx] = action
                        if action == "旋轉":
                            angles[idx] = st.selectbox("角度", [90, 180, 270], key=f"angle_{idx}")

        # 執行刪除（先做刪除避免索引混亂）
        for idx in reversed(range(len(actions))):
            if actions[idx] == "刪除":
                pdf_path = delete_page(pdf_path, idx)
                st.success(f"✅ 頁面 {idx+1} 已刪除")
                st.experimental_rerun()

        # 執行旋轉
        for idx, angle in enumerate(angles):
            if actions[idx] == "旋轉" and angle in [90, 180, 270]:
                pdf_path = rotate_pdf(pdf_path, idx, angle)
                st.success(f"✅ 頁面 {idx+1} 已旋轉 {angle} 度")
                st.experimental_rerun()

        # 拖曳排序
        st.subheader("🔀 拖曳重新排序頁面")
        page_count = len(pypdf.PdfReader(pdf_path).pages)
        reorder_data = [{"id": i, "label": f"頁面 {i+1}"} for i in range(page_count)]
        reordered = DraggableList(reorder_data, key="reorder_list")
        new_order = [item["id"] for item in reordered]

        if new_order != list(range(page_count)):
            pdf_path = reorder_pdf(pdf_path, new_order)
            st.success("✅ 頁面順序已更新")
            st.experimental_rerun()

        # 下載按鈕
        with open(pdf_path, "rb") as f:
            st.download_button("📥 下載編輯後的 PDF", f, file_name="edited.pdf")

if __name__ == "__main__":
    main()
