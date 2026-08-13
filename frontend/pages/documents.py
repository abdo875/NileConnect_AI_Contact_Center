import streamlit as st
from services import document_service
from components.navbar import render_navbar
from components.alerts import show_success, show_error, show_api_error
from components.forms import section_header
from utils.formatters import format_datetime, format_file_size, status_badge

ALLOWED_TYPES = {
    "application/pdf": "PDF",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": "DOCX",
    "text/plain": "TXT",
}


def show() -> None:
    render_navbar("📚 Knowledge Base")

    tab1, tab2 = st.tabs(["📄 Documents", "⬆️ Upload Document"])

    # ── Tab 1: List ───────────────────────────────────────────────
    with tab1:
        documents = document_service.get_documents(limit=100)

        if isinstance(documents, dict) and "error" in documents:
            show_api_error(documents)
            return

        if not documents:
            st.info("📭 No documents uploaded yet.")
            return

        # Summary counts
        ready = sum(1 for d in documents if d.get("status") == "READY")
        processing = sum(1 for d in documents if d.get("status") == "PROCESSING")
        c1, c2, c3 = st.columns(3)
        c1.metric("Total Documents", len(documents))
        c2.metric("Ready", ready)
        c3.metric("Processing", processing)

        st.markdown("---")

        for doc in documents:
            icon = {"pdf": "📕", "docx": "📘", "txt": "📄"}.get(doc.get("file_type", ""), "📁")
            with st.expander(
                f"{icon} {doc.get('original_name', 'N/A')}  |  {status_badge(doc.get('status',''))}  |  {format_file_size(doc.get('file_size'))}",
                expanded=False,
            ):
                c1, c2 = st.columns(2)
                with c1:
                    st.write(f"**Original Name:** {doc.get('original_name', '—')}")
                    st.write(f"**File Type:** {doc.get('file_type', '—').upper()}")
                    st.write(f"**Size:** {format_file_size(doc.get('file_size'))}")
                with c2:
                    st.write(f"**Status:** {status_badge(doc.get('status', '—'))}")
                    st.write(f"**Uploaded:** {format_datetime(doc.get('created_at'))}")

                if st.button("🗑️ Delete Document", key=f"del_doc_{doc['id']}", type="secondary"):
                    result = document_service.delete_document(doc["id"])
                    if "error" in result:
                        show_error(result["error"])
                    else:
                        show_success("Document deleted.")
                        st.rerun()

    # ── Tab 2: Upload ─────────────────────────────────────────────
    with tab2:
        section_header("Upload Document", "Add a PDF, DOCX, or TXT file to the knowledge base")

        st.info("📌 Documents uploaded here will be available to the AI Assistant in Phase 2 (Agentic RAG).")

        uploaded_file = st.file_uploader(
            "Choose a file",
            type=["pdf", "docx", "txt"],
            help="Supported formats: PDF, DOCX, TXT",
        )

        if uploaded_file:
            st.write(f"**File:** {uploaded_file.name}")
            st.write(f"**Size:** {format_file_size(uploaded_file.size)}")
            st.write(f"**Type:** {uploaded_file.type}")

            if st.button("⬆️ Upload to Knowledge Base", type="primary"):
                with st.spinner("Uploading..."):
                    file_bytes = uploaded_file.read()
                    result = document_service.upload_document(
                        file_bytes,
                        uploaded_file.name,
                        uploaded_file.type,
                    )
                if "error" in result:
                    show_error(result["error"])
                else:
                    show_success(f"'{uploaded_file.name}' uploaded successfully!")
                    st.rerun()
