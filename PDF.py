# 重新排序 PDF 頁面
def reorder_pdf(pdf_path, new_order):
    reader = pypdf.PdfReader(pdf_path)
    writer = pypdf.PdfWriter()
    for idx in new_order:
        writer.add_page(reader.pages[idx])
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp:
        writer.write(temp)
        return temp.name

def main():
    set_style()
    st.title("📄 PDF 編輯器")

    uploaded_file = st.file_uploader("請上傳 PDF 文件", type="pdf")

    if uploaded_file:
        # 儲存到暫存目錄
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(uploaded_file.read())
            pdf_path = tmp.name

        reader = pypdf.PdfReader(pdf_path)
        num_pages = len(reader.pages)

        # 顯示所有頁面縮圖
        thumbnails = [generate_thumbnail(pdf_path, i) for i in range(num_pages)]
        actions = []
        rotation_angles = []

        st.subheader("🖼 預覽與操作")
        for i in range(0, num_pages, 6):
            cols = st.columns(6)
            for j in range(6):
                idx = i + j
                if idx < num_pages:
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
                pdf_path = delete_page(pdf_path, idx)
                st.success(f"頁面 {idx+1} 已刪除")
                st.experimental_rerun()

        # 執行旋轉
        for idx, angle in rotation_angles:
            if angle != 0:
                pdf_path = rotate_pdf(pdf_path, idx, angle)
                st.success(f"頁面 {idx+1} 已旋轉 {angle} 度")
                st.experimental_rerun()

        # 拖曳排序
        st.subheader("🔀 拖曳重新排序頁面")
        reorder_data = [
            {"id": i, "label": f"頁面 {i+1}"} for i in range(len(pypdf.PdfReader(pdf_path).pages))
        ]
        reordered = DraggableList(reorder_data, key="pdf_reorder")
        
        # 確保返回的 reordered 是一個可迭代的列表
        if isinstance(reordered, list):
            new_order = [item["id"] for item in reordered]
        else:
            new_order = list(range(len(reorder_data)))

        if new_order != list(range(len(new_order))):
            pdf_path = reorder_pdf(pdf_path, new_order)
            st.success("✅ 頁面順序已更新")
            st.experimental_rerun()

        # 下載按鈕
        with open(pdf_path, "rb") as f:
            st.download_button("📥 下載編輯後的 PDF", f, file_name="edited.pdf")

if __name__ == "__main__":
    main()
