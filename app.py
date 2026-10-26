from pathlib import Path

import streamlit as st

from rag import answer_query, build_index, get_index, retrieve

st.set_page_config(page_title="DocChat", layout="centered")

st.title("DocChat")
st.caption("Ask questions about your documents.")

if "index" not in st.session_state:
    with st.spinner("Loading index..."):
        try:
            st.session_state.index = get_index()
        except Exception as e:
            st.session_state.index = None
            st.warning(str(e))

_, col = st.columns([4, 1])

with col:
    if st.button("Rebuild Index", use_container_width=True):
        with st.spinner("Indexing..."):
            try:
                st.session_state.index = build_index()
                st.success("Done.")
            except Exception as e:
                st.error(str(e))

query = st.text_input("Question", placeholder="What topics are covered in Unit I?")

if query:
    if st.session_state.index is None:
        st.error("No index found. Add files to the docs/ folder and click Rebuild Index.")
    else:
        with st.spinner("Thinking..."):
            chunks = retrieve(query, st.session_state.index)
            response = answer_query(query, chunks)

        st.markdown("### Answer")
        st.write(response)

        with st.expander("Sources"):
            for i, chunk in enumerate(chunks, 1):
                meta = chunk.metadata
                filename = Path(meta.get("source", "Unknown")).name
                page = meta.get("page", 0)
                st.markdown(f"**[{i}] {filename} — Page {page + 1}**")
                st.caption(chunk.page_content)