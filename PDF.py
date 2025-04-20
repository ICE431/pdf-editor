import streamlit as st
import pypdf
from PIL import Image
import io
import tempfile
import fitz  # PyMuPDF for rendering PDF pages as images
from io import BytesIO
import os

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
    # Open the PDF file
    doc = pypdf.PdfReader(pdf_path)
    page = doc.pages[page_num]

    # Rotate the page (pypdf method)
    page.rotate(angle)
    
    # Write the rotated PDF
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

    # Skip the page to be deleted
    for i in range(len(doc.pages)):
        if i != page_num:
            output.add_page(doc.pages[i])

    # Write the updated PDF
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.close()
        with open(temp_file.name, 'wb') as f:
            output.write(f)
    return temp_file.name

# 頁面排序（這裏是用 streamlit-draggable 或自訂排序邏輯）
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

        # 每行顯示 6 個頁面縮略圖，由上往下排列
        for i in range(0, num_pages, 6):
            cols = st.columns(6)
            for j in range(6):
                page_index = i + j
                if page_index < num_pages:
                    img = thumbnails[page_index]
                    cols[j].image(img, use_container_width=True)
                    # 點擊圖像來選擇該頁面進行旋轉或刪除
                    action = cols[j].radio(
                        f"選擇頁面 {page_index + 1}",
                        ['無動作', '旋轉', '刪除'],
                        key=f"action_{page_index}"
                    )
                    
                    if action == '旋轉':
                        # 使用下拉選單選擇旋轉角度
                        angle = st.selectbox(
                            f"選擇頁面 {page_index + 1} 旋轉角度",
                            options=[0, 90, 180, 270],
                            index=0,  # 預設為 0 度
                            key=f"select_angle_{page_index}"
                        )
                        if angle != 0:
                            rotated_pdf = rotate_pdf(pdf_path, page_index, angle)
                            st.success(f"頁面 {page_index + 1} 已旋轉 {angle} 度！")
                    
                    if action == '刪除':
                        pdf_path = delete_page(pdf_path, page_index)
                        st.success(f"頁面 {page_index + 1} 已刪除！")

        # **頁面排序部分** - 使用下拉選單進行頁面排序
        page_order = list(range(num_pages))
        new_order = st.multiselect(
            "重新排序頁面",
            page_order,
            default=page_order,
            format_func=lambda x: f"頁面 {x + 1}",
            key="page_order"
        )
        
        if new_order != page_order:
            reordered_pdf = reorder_pdf(pdf_path, new_order)
            st.success("頁面排序已更新！")
            
        # 顯示合併後的 PDF 下載鏈接
        with open(pdf_path, "rb") as f:
            st.download_button("下載編輯後的 PDF", f, file_name="edited_pdf.pdf")

if __name__ == "__main__":
    main()
