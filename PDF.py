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
    pix = page.get_pixmap(matrix=fitz.Matrix(0.4, 0.4))  # 設定縮放比例
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    
    # 確保圖片大小適合顯示
    img.thumbnail((300, 300))  # 設定縮圖最大寬高為300
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
def reorder_pdf(pdf_paths, new_order):
    writer = pypdf.PdfWriter()
    for idx in new_order:
        pdf_path, page_num = pdf_paths[idx]
        reader = pypdf.PdfReader(pdf_path)
        writer.add_page(reader.pages[page_num])
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
        all_actions = []  # 用於記錄所有的動作
        all_rotation_angles = []  # 用於記錄所有的旋轉角度
        pdf_page_info = []  # 用來儲存每個PDF文件的頁面資訊 (PDF路徑 + 頁碼)

        st.subheader("🖼 預覽與操作")
        
        # 顯示每個 PDF 文件的縮圖並處理頁面操作
        for pdf_path in pdf_paths:
            reader = pypdf.PdfReader(pdf_path)
            num_pages = len(reader.pages)
            
            # 生成該 PDF 文件的所有縮圖
            pdf_thumbnails = [generate_thumbnail(pdf_path, i) for i in range(num_pages)]
            
            # 顯示每個 PDF 文件的縮圖
            for i in range(0, num_pages, 6):
                cols = st.columns(6)
                for j in range(6):
                    idx = i + j
                    if idx < num_pages:
                        with cols[j]:
                            st.image(pdf_thumbnails[idx], use_container_width=True)
                            action = st.radio(
                                f"頁面 {idx+1}",
                                ['無動作', '旋轉', '刪除'],
                                key=f"action_{pdf_path}_{idx}"
                            )
                            all_actions.append((pdf_path, idx, action))

                            if action == '旋轉':
                                angle = st.selectbox(
                                    f"旋轉角度 (頁面 {idx+1})",
                                    [90, 180, 270],
                                    index=0,
                                    key=f"angle_{pdf_path}_{idx}"
                                )
                                all_rotation_angles.append((pdf_path, idx, angle))
                            else:
                                all_rotation_angles.append((pdf_path, idx, 0))
                            
                            # 儲存每個PDF頁面資訊 (pdf路徑 + 頁面索引)
                            pdf_page_info.append((pdf_path, idx))

        # 執行刪除
        for pdf_path, idx, action in all_actions:
            if action == '刪除':
                pdf_paths[0] = delete_page(pdf_path, idx)
                st.success(f"頁面 {idx+1} 已刪除")

        # 執行旋轉
        for pdf_path, idx, angle in all_rotation_angles:
            if angle != 0:
                pdf_paths[0] = rotate_pdf(pdf_path, idx, angle)
                st.success(f"頁面 {idx+1} 已旋轉 {angle} 度")

        # 合併排序選單
        st.subheader("🔀 重新排序所有 PDF 頁面")
        page_order = list(range(len(pdf_page_info)))

        reordered = st.multiselect(
            "請選擇所有頁面順序",
            options=page_order,
            format_func=lambda x: f"頁面 {x+1}",
            key="reorder_selectbox"
        )

        if reordered:
            merged_pdf = reorder_pdf(pdf_page_info, reordered)
            st.success("✅ 頁面順序已更新")

            # 下載編輯後的 PDF 文件
            with open(merged_pdf, "rb") as f:
                st.download_button("📥 下載編輯後的 PDF", f, file_name="edited_sorted.pdf")

        # 合併選項
        if len(uploaded_files) > 1:
            st.subheader("📄 合併多個 PDF 文件")
            if st.button("合併文件"):
                merged_pdf = merge_pdfs(pdf_paths)
                st.success("✅ 合併完成")

                # 下載合併後的 PDF 文件
                with open(merged_pdf, "rb") as f:
                    st.download_button("📥 下載合併後的 PDF", f, file_name="merged_sorted.pdf")

if __name__ == "__main__":
    main()
