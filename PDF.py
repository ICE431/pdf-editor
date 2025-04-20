import streamlit as st
import PyPDF2
from PIL import Image
import io
import tempfile
import fitz  # PyMuPDF for rendering PDF pages as images
from io import BytesIO
import os

# PDF 頁面預覽
def generate_thumbnail(pdf_path, page_num):
    doc = fitz.open(pdf_path)  # Open the PDF
    page = doc.load_page(page_num)  # Load the specific page
    pix = page.get_pixmap()  # Render page to an image
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)  # Convert to PIL Image
    return img

# PDF 旋轉
def rotate_pdf(pdf_path, page_num, angle):
    doc = PyPDF2.PdfReader(pdf_path)
    output = PyPDF2.PdfWriter()
    
    # Rotate the specified page
    for i in range(len(doc.pages)):
        page = doc.pages[i]
        if i == page_num:
            page.rotate_clockwise(angle)  # Rotate the selected page
        output.add_page(page)
    
    # Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.close()
        with open(temp_file.name, 'wb') as f:
            output.write(f)
    return temp_file.name

# 頁面排序（這裏是用自訂排序邏輯）
def reorder_pdf(pdf_path, new_order):
    doc = PyPDF2.PdfReader(pdf_path)
    output = PyPDF2.PdfWriter()
    
    for page_num in new_order:
        output.add_page(doc.pages[page_num])
    
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        temp_file.close()
        with open(temp_file.name, 'wb') as f:
            output.write(f)
    return temp_file.name

# Streamlit UI
def main():
    st.title("PDF 編輯器")

    uploaded_file = st.file_uploader("上傳 PDF 文件", type="pdf")
    if uploaded_file is not None:
        # 處理上傳的 PDF
        pdf_path = f"/tmp/{uploaded_file.name}"
        with open(pdf_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # 顯示預覽圖
        num_pages = len(PyPDF2.PdfReader(pdf_path).pages)
        thumbnails = []
        for i in range(min(num_pages, 6)):  # 只顯示最多6個頁面
            thumbnail = generate_thumbnail(pdf_path, i)
            thumbnails.append(thumbnail)
        
        # 顯示 6 個頁面縮略圖（水平排列）
        cols = st.columns(6)
        for i, thumb in enumerate(thumbnails):
            cols[i].image(thumb, use_column_width=True)

        # 旋轉控制
        selected_page = st.slider("選擇旋轉頁面", 0, num_pages - 1, 0)
        angle = st.slider("選擇旋轉角度", 0, 360, 0, 90)
        
        if angle != 0:
            rotated_pdf = rotate_pdf(pdf_path, selected_page, angle)
            st.success(f"頁面 {selected_page + 1} 已旋轉 {angle} 度！")
            pdf_path = rotated_pdf  # 更新 PDF 路徑為旋轉後的文件

        # 頁面排序
        page_order = list(range(num_pages))
        new_order = st.multiselect(
            "重新排序頁面",
            page_order,
            default=page_order,
            format_func=lambda x: f"頁面 {x + 1}"
        )
        
        if new_order != page_order:
            reordered_pdf = reorder_pdf(pdf_path, new_order)
            st.success("頁面排序已更新！")
            pdf_path = reordered_pdf  # 更新 PDF 路徑為排序後的文件
            
        # 顯示合併後的 PDF 下載鏈接
        with open(pdf_path, "rb") as f:
            st.download_button("下載編輯後的 PDF", f, file_name="edited_pdf.pdf")

if __name__ == "__main__":
    main()
