import streamlit as st
import pypdf
from PIL import Image
import tempfile
import fitz  # PyMuPDF for rendering PDF pages as images
from io import BytesIO
from st_draggable_list import DraggableList  # 用於可拖曳排序

# 設置 Streamlit 配色為文清風格
def set_style():
    st.markdown("""
    <style>
    body {
        background-color: #f4f4f4;
        color: #333;
    }
    .stButton>button {
        background-color: #6a9dff;
        color: white;
        font-size: 16px;
    }
    .stSlider>div>div>div>input {
        background-color: #e6effb;
    }
    .stRadio>div>div>div>label {
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

# PDF 頁面預覽
def generate_thumbnail(pdf_path, page_num):
    doc = fitz.open(pdf_path)  # Open the PDF
    page = doc.load_page(page_num)  # Load the specific page
    pix = page.get_pixmap()  # Render page to an image
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)  # Convert to PIL Image
    return img

# PDF 旋轉
def rotate_pdf(pdf_path, page_num, angle):
    doc = pypdf.PdfReader(pdf_path)
    page = doc.pages[page_num]
    page.rotate(angle)
    
    output = pypdf.PdfWriter()
    output.add_page(page)
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.close()
        with open(temp_file.name, 'wb') as f:
            output.write(f)
    return temp_file.name

# 頁面刪除
def delete_page(pdf_path, page_num):
    doc = pypdf.PdfReader(pdf_path)
    output = pypdf.PdfWriter()
    for i in range(len(doc.pages)):
        if i != page_num:
            output.add_page(doc.pages[i])
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.close()
        with open(temp_file.name, 'wb') as f:
            output.write(f)
    return temp_file.name

# 頁面排序
def reorder_pdf(pdf_path, new_order):
    doc = pypdf.PdfReader(pdf_path)
    output = pypdf.PdfWriter()
    for page_num in new_order:
        output.add_page(doc.pages[page_num])
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.close()
        with open(temp_file.name, 'wb') as f:
            output.write(f)
    return temp_file.name

# Streamlit UI
def main():
    set_style()  # 設置文清風格

    st.title("PDF 編輯器")

    uploaded_file = st.file_uploader("上傳 PDF 文件", type="pdf")
    if uploaded_file is not None:
        # 處理上傳的 PDF
        pdf_path = f"/tmp/{uploaded_file.name}"
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # 顯示預覽圖
        num_pages = len(pypdf.PdfReader(pdf_path).pages)
        thumbnails = []
        for i in range(num_pages):  # 顯示所有頁面的縮略圖
            thumbnail = generate_thumbnail(pdf_path, i)
            thumbnails.append(thumbnail)

        # 準備可拖曳排序的資料
        draggable_data = [
            {"id": f"page_{i}", "order": i, "name": f"頁面 {i+1}", "image": thumbnails[i]}
            for i in range(num_pages)
        ]

        # 顯示可拖曳排序的頁面縮圖
        draggable_list = DraggableList(draggable_data, key="pdf_pages")
        st.write(draggable_list)

        # 取得排序後的頁面順序
        sorted_pages = draggable_list.get_sorted()

        # 顯示排序後的頁面順序
        st.write("排序後的頁面順序：", [page["name"] for page in sorted_pages])

        # 處理頁面旋轉和刪除
        for i, page in enumerate(sorted_pages):
            cols = st.columns(2)
            with cols[0]:
                action = st.radio(
                    f"選擇頁面 {i+1} 動作",
                    ['無動作', '旋轉', '刪除'],
                    key=f"action_{i}"
                )
                if action == '旋轉':
                    angle = st.selectbox(
                        f"選擇頁面 {i+1} 旋轉角度",
                        options=[0, 90, 180, 270],
                        index=0,  # 預設為 0 度
                        key=f"select_angle_{i}"
                    )
                    if angle != 0:
                        rotated_pdf = rotate_pdf(pdf_path, i, angle)
                        st.success(f"頁面 {i+1} 已旋轉 {angle} 度！")
                elif action == '刪除':
                    pdf_path = delete_page(pdf_path, i)
                    st.success(f"頁面 {i+1} 已刪除！")

        # 顯示合併後的 PDF 下載鏈接
        with open(pdf_path, "rb") as f:
            st.download_button("下載編輯後的 PDF", f, file_name="edited_pdf.pdf")

if __name__ == "__main__":
    main()
