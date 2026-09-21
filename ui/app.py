"""ChatGPT-style Streamlit client for the analytics engine.

Run this file separately from FastAPI. It stores only the current conversation
in Streamlit session state and sends questions to the engine over HTTP.
"""

from __future__ import annotations

import os

import streamlit as st
from dotenv import load_dotenv

from ui.api_client import EngineClient, EngineUnavailableError
from ui.renderers import build_figure

load_dotenv()

st.set_page_config(page_title="Omnichannel Analytics", page_icon="📊", layout="wide")


def _render_assistant(result: dict[str, object]) -> None:
    st.markdown(str(result.get("answer", "")))
    figure = build_figure(result)
    if figure is not None:
        st.plotly_chart(figure, use_container_width=True)
    rows = result.get("rows", [])
    if rows:
        st.dataframe(rows, use_container_width=True, hide_index=True)
    warnings = result.get("warnings", [])
    for warning in warnings if isinstance(warnings, list) else []:
        st.warning(str(warning))
    with st.expander("Show SQL and provenance"):
        st.code(str(result.get("sql", "")), language="sql")
        st.caption(f"Tables: {', '.join(result.get('tables_used', []))}")
        st.caption(f"Execution: {result.get('execution_ms', '?')} ms")


def main() -> None:
    st.title("Omnichannel Retail Analytics")
    st.caption("Ask questions about the Gold layer. The engine generates safe read-only SQL and chooses a chart when useful.")

    if "messages" not in st.session_state:
        st.session_state.messages = []

    with st.sidebar:
        st.header("Conversation")
        if st.button("New conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()
        max_rows = st.slider("Maximum rows", min_value=10, max_value=500, value=100, step=10)
        visualization = st.selectbox("Visualization", ["auto", "table_only", "chart_only"])
        engine_url = st.text_input("Engine URL", os.getenv("ENGINE_URL", "http://localhost:8000"))

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            if message["role"] == "user":
                st.markdown(message["content"])
            else:
                _render_assistant(message["result"])

    question = st.chat_input("Ask about revenue, customers, products, inventory, or campaigns")
    if not question:
        return

    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    history = [
        {"role": message["role"], "content": message["content"]}
        for message in st.session_state.messages[:-1]
        if message["role"] in {"user", "assistant"}
    ]
    client = EngineClient(engine_url)
    with st.chat_message("assistant"):
        with st.spinner("Analyzing the Gold layer…"):
            try:
                result = client.analyze(question, history, max_rows, visualization)
            except EngineUnavailableError as exc:
                st.error(str(exc))
                return
        _render_assistant(result)
    st.session_state.messages.append({"role": "assistant", "content": result.get("answer", ""), "result": result})


if __name__ == "__main__":
    main()
