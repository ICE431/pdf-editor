import streamlit as st
from pypdf import PdfReader, PdfWriter
import fitz  # PyMuPDF
from PIL import Image
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

    for file_index, uploaded_file in enumerate(uploaded_files):
        file_name = uploaded_file.name
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        uploaded_file.seek(0)

        for page_index, page in enumerate(doc):
            pix = page.get_pixmap(dpi=100)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            img = img.resize((int(pix.width * 0.5), int(pix.height * 0.5)))  # 縮圖 50%

            label = f"{file_name} - 第 {page_index+1} 頁"
            page_labels.append(label)

            with st.container():
                cols = st.columns(6)
                col = cols[page_index % 6]  # 每 6 張換行
                with col:
                    st.image(img, caption=label, use_column_width=True)

                    # 唯一 key 防止衝突
                    remove = st.checkbox("刪除", key=f"remove_{file_index}_{page_index}")

                    rotate_key = f"rotate_{file_index}_{page_index}"
                    if rotate_key not in st.session_state:
                        st.session_state[rotate_key] = 0

                    if st.button("🔄 旋轉 90°", key=f"rotate_btn_{file_index}_{page_index}"):
                        st.session_state[rotate_key] = (st.session_state[rotate_key] + 90) % 360

                    st.caption(f"旋轉角度：{st.session_state[rotate_key]}°")

            all_pages.append((file_index, file_name, uploaded_file, page_index))
            remove_flags.append(remove)
            rotate_degrees.append(st.session_state[rotate_key])

    # 頁面排序功能
    st.subheader("📋 拖曳選擇要保留頁面並排序")
    page_order = st.multiselect(
        "✅ 選擇保留並排序的頁面（順序會照這個排列）",
        options=page_labels,
        default=[label for idx, label in enumerate(page_labels) if not remove_flags[idx]]
    )

    if st.button("📎 合併 PDF"):
        writer = PdfWriter()

        for label in page_order:
            idx = page_labels.index(label)
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
