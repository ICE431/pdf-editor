import streamlit as st
from pypdf import PdfReader, PdfWriter
import fitz  # PyMuPDF
from PIL import Image
from st_draggable_list import DraggableList
import tempfile

st.set_page_config(page_title="PDF 編輯器", page_icon="📄", layout="wide")
st.title("📄 PDF 可視化編輯工具（預覽、刪除、旋轉、排序）")

uploaded_files = st.file_uploader("📤 上傳 PDF（可多選）", type="pdf", accept_multiple_files=True)

if uploaded_files:
    st.header("👀 預覽並操作每一頁")

    all_pages = []
    remove_flags = []
    rotate_degrees = []
    page_labels = []

    page_info_list = []

    # 收集所有 PDF 頁面資訊
    for file_index, uploaded_file in enumerate(uploaded_files):
        file_name = uploaded_file.name
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        uploaded_file.seek(0)

        for page_index, page in enumerate(doc):
            pix = page.get_pixmap(dpi=100)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = img.resize((int(pix.width * 0.5), int(pix.height * 0.5)))  # 縮圖 50%

            label = f"{file_name} - 第 {page_index+1} 頁"
            rotate_key = f"rotate_{file_index}_{page_index}"
            if rotate_key not in st.session_state:
                st.session_state[rotate_key] = 0

            page_info_list.append({
                "file_index": file_index,
                "file_name": file_name,
                "uploaded_file": uploaded_file,
                "page_index": page_index,
                "label": label,
                "img": img,
                "rotate_key": rotate_key
            })

    # 使用 DraggableList 顯示可排序的頁面列表
    draggable_list = DraggableList(page_info_list, key="pdf_pages", width="100%")
    st.write(draggable_list)

    # 排序後的頁面順序
    sorted_pages = draggable_list

    # 顯示排序後的頁面預覽
    for idx, info in enumerate(sorted_pages):
        with st.expander(f"📄 頁面 {idx + 1}: {info['label']}"):
            st.image(info["img"], caption=info["label"], use_column_width=True)

            remove = st.checkbox("刪除", key=f"remove_{info['file_index']}_{info['page_index']}")
            if st.button("🔄 旋轉 90°", key=f"rotate_btn_{info['file_index']}_{info['page_index']}"):
                st.session_state[info["rotate_key"]] = (st.session_state[info["rotate_key"]] + 90) % 360

            st.caption(f"旋轉角度：{st.session_state[info['rotate_key']]}°")

            all_pages.append((
                info["file_index"],
                info["file_name"],
                info["uploaded_file"],
                info["page_index"]
            ))
            remove_flags.append(remove)
            rotate_degrees.append(st.session_state[info["rotate_key"]])
            page_labels.append(info["label"])

    # 合併 PDF
    if st.button("📎 合併 PDF"):
        writer = PdfWriter()

        for idx in range(len(all_pages)):
            if remove_flags[idx]:
                continue

            file_index, file_name, file, page_num = all_pages[idx]

            file.seek(0)
            reader = PdfReader(file)
            page = reader.pages[page_num]

            if rotate_degrees[idx]:
                page.rotate(rotate_degrees[idx])

            writer.add_page(page)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            writer.write(tmp_file.name)
            with open(tmp_file.name, "rb") as f:
                st.success("✅ 合併完成！")
                st.download_button("📥 下載合併後的 PDF", f, file_name="merged.pdf")
