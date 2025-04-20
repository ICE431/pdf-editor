import streamlit as st
from pypdf import PdfReader, PdfWriter
import fitz  # PyMuPDF
from PIL import Image
import tempfile

# 設定頁面配置
st.set_page_config(page_title="PDF 編輯器", page_icon="📄", layout="wide")
st.title("📄 PDF 可視化編輯工具（預覽、刪除、旋轉、排序）")

# 上傳 PDF 文件
uploaded_files = st.file_uploader("📤 上傳 PDF（可多選）", type="pdf", accept_multiple_files=True)

if uploaded_files:
    st.header("👀 預覽並操作每一頁")

    all_pages = []
    remove_flags = []
    rotate_degrees = []

    for uploaded_file in uploaded_files:
        file_name = uploaded_file.name
        doc = fitz.open(stream=uploaded_file.read(), filetype="pdf")
        uploaded_file.seek(0)

        for i, page in enumerate(doc):
            pix = page.get_pixmap(dpi=70)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            # ✅ 縮小預覽 70%
            img = img.resize((int(pix.width * 0.7), int(pix.height * 0.7)))

            label = f"{file_name} - 第 {i+1} 頁"
            col1, col2 = st.columns([2, 1])
            with col1:
                st.image(img, caption=label, use_column_width=True)

            with col2:
                # 刪除 checkbox
                remove = st.checkbox(f"刪除這一頁", key=f"remove_{file_name}_{i}")

                # 初始化旋轉角度（記錄在 session）
                rotate_key = f"rotate_angle_{file_name}_{i}"
                if rotate_key not in st.session_state:
                    st.session_state[rotate_key] = 0

                # 旋轉按鈕（每次點就加 90）
                rotate_btn_key = f"rotate_btn_{file_name}_{i}"
                if st.button("🔄 旋轉 90°", key=rotate_btn_key):
                    st.session_state[rotate_key] = (st.session_state[rotate_key] + 90) % 360

                st.text(f"目前旋轉：{st.session_state[rotate_key]}°")

            # 儲存頁面資料
            all_pages.append((file_name, uploaded_file, i))
            remove_flags.append(remove)
            rotate_degrees.append(st.session_state[rotate_key])

    # 設定頁面排序（顯示所有頁面並允許排序）
    page_order = st.multiselect(
        "📋 排序頁面（拖動選擇順序）",
        options=[f"{file_name} - 第 {i+1} 頁" for file_name, _, i in all_pages],
        default=[f"{file_name} - 第 {i+1} 頁" for file_name, _, i in all_pages]
    )

    # 合併 PDF
    if st.button("📎 合併 PDF"):
        writer = PdfWriter()

        # 按照選擇的頁面順序添加
        for label in page_order:
            file_name, file, page_num = all_pages[
                [f"{file_name} - 第 {i+1} 頁" for file_name, _, i in all_pages].index(label)
            ]
            if remove_flags[all_pages.index((file_name, file, page_num))]:
                continue  # 刪除不需要的頁面

            file.seek(0)
            reader = PdfReader(file)
            page = reader.pages[page_num]

            # 旋轉
            degrees = rotate_degrees[all_pages.index((file_name, file, page_num))]
            if degrees:
                page.rotate(degrees)

            writer.add_page(page)

        # 生成合併後的 PDF 並提供下載
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
            writer.write(tmp_file.name)
            with open(tmp_file.name, "rb") as f:
                st.success("✅ 合併完成！")
                st.download_button("📥 下載合併後的 PDF", f, file_name="merged.pdf")
