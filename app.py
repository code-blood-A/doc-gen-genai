import streamlit as st
import os
import sys
import time

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
import config
from parser.java_crawler import get_java_files
from embeddings.embedder import CodeEmbedder
from generator.javadoc_writer import JavadocWriter
from generator.class_doc import ClassDocGenerator
from generator.package_doc import PackageDocGenerator
from generator.project_overview import ProjectOverviewGenerator
from visualizer.spring_layer_graph import SpringLayerVisualizer

st.set_page_config(page_title="GenAI Java Documenter", layout="wide")

st.title("🏗️ GenAI Java Spring Documenter")
st.markdown("Automated Javadoc injection and documentation generation for Java projects.")

with st.sidebar:
    st.header("⚙️ Settings")
    
    if "target_repo" not in st.session_state:
        st.session_state.target_repo = config.TARGET_REPO if config.TARGET_REPO else ""
        
    def browse_directory():
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.attributes('-topmost', True)
        folder_path = filedialog.askdirectory(master=root)
        root.destroy()
        if folder_path:
            st.session_state.target_repo = folder_path

    repo_col, btn_col = st.columns([4, 1])
    with repo_col:
        st.text_input("Target Repo", key="target_repo")
    with btn_col:
        st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
        st.button("📁", on_click=browse_directory, help="Browse for directory")

    config.TARGET_REPO = st.session_state.target_repo
    config.DOCS_DIR = os.path.join(config.TARGET_REPO if config.TARGET_REPO else ".", "docs")

    use_ollama = st.checkbox("Use Local Ollama (Fallback)", value=config.OLLAMA_FALLBACK)
    
    st.divider()
    st.subheader("📂 Repository Info")
    if st.button("🔄 Refresh File List"):
        files = get_java_files()
        st.success(f"Found {len(files)} Java files.")
        for f in files:
            st.text(f"  📄 {os.path.relpath(f, config.TARGET_REPO)}")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Step 1: Indexing")
    if st.button("🧠 Index Repository into ChromaDB"):
        with st.spinner("Parsing and embedding code..."):
            embedder = CodeEmbedder()
            embedder.index_repository()
            st.success("Indexing complete!")

    st.subheader("Step 2: Documentation")
    if st.button("📝 Generate Everything"):
        files = get_java_files()

        if not files:
            st.error(f"No .java files found in: {config.TARGET_REPO}")
        else:
            progress_bar = st.progress(0)
            status_text = st.empty()
            log_area = st.empty()
            total_steps = len(files) * 2 + 2  # javadoc + class docs + package + overview
            current_step = 0

            # 1. Javadoc Injection
            status_text.text("📝 Step 1/4: Injecting Javadocs into source files...")
            writer = JavadocWriter(use_ollama=use_ollama)
            javadoc_count = 0
            for i, f in enumerate(files):
                fname = os.path.relpath(f, config.TARGET_REPO)
                log_area.text(f"Processing: {fname}")
                count = writer.process_file(f)
                javadoc_count += count
                current_step += 1
                progress_bar.progress(current_step / total_steps)

            st.info(f"✅ Javadocs injected: {javadoc_count} methods across {len(files)} files")

            # 2. Class/File Docs (mirrors source structure)
            status_text.text("📄 Step 2/4: Generating per-file documentation...")
            class_gen = ClassDocGenerator(use_ollama=use_ollama)
            docs_count = 0
            for i, f in enumerate(files):
                fname = os.path.relpath(f, config.TARGET_REPO)
                log_area.text(f"Documenting: {fname}")
                count = class_gen.process_file(f)
                docs_count += count
                current_step += 1
                progress_bar.progress(current_step / total_steps)

            st.info(f"✅ File docs generated: {docs_count} files")

            # 3. Package READMEs
            status_text.text("📁 Step 3/4: Generating folder READMEs...")
            log_area.text("Summarizing packages...")
            pkg_gen = PackageDocGenerator(use_ollama=use_ollama)
            pkg_gen.process_directory(config.DOCS_DIR)
            current_step += 1
            progress_bar.progress(current_step / total_steps)

            # 4. Project Overview
            status_text.text("🏗️ Step 4/4: Generating project overview...")
            log_area.text("Creating master README...")
            proj_gen = ProjectOverviewGenerator(use_ollama=use_ollama)
            proj_gen.process_project()
            current_step += 1
            progress_bar.progress(1.0)

            log_area.empty()
            status_text.empty()
            st.success(f"🎉 Documentation generation complete! Check: `{config.DOCS_DIR}`")

with col2:
    st.subheader("Step 3: Visualization")
    if st.button("📊 Generate Architecture Diagrams"):
        with st.spinner("Drawing diagrams..."):
            os.makedirs(config.DOCS_DIR, exist_ok=True)
            vis = SpringLayerVisualizer()
            vis.generate_all()

            proj_path   = os.path.join(config.DOCS_DIR, "architecture_graph.png")
            method_path = os.path.join(config.DOCS_DIR, "method_diagram.png")

            if os.path.exists(proj_path):
                st.markdown("#### Project-Level Architecture")
                st.image(proj_path, caption="Layer Flow: Client → Controller → Service → Repository → DB", use_column_width=True)

            if os.path.exists(method_path):
                st.markdown("#### Method-Level Class Diagram")
                st.image(method_path, caption="UML Class Diagram — Fields, Methods & Dependencies", use_column_width=True)


st.divider()
st.subheader("📁 Generated Documentation Viewer")
if os.path.exists(config.DOCS_DIR):
    has_docs = False
    for root, dirs, files_in_dir in os.walk(config.DOCS_DIR):
        rel_path = os.path.relpath(root, config.DOCS_DIR)
        md_files = [f for f in files_in_dir if f.endswith(".md")]

        if not md_files:
            continue

        has_docs = True
        folder_label = rel_path if rel_path != "." else "📦 Project Root"
        with st.expander(f"📂 {folder_label} ({len(md_files)} docs)", expanded=(rel_path == ".")):
            for f in sorted(md_files):
                if st.button(f"📄 {f}", key=f"{rel_path}_{f}"):
                    with open(os.path.join(root, f), 'r', encoding='utf-8') as file:
                        st.markdown(file.read())

    if not has_docs:
        st.info("No documentation generated yet. Run Step 2 above.")
else:
    st.info("No documentation generated yet. Run Step 2 above.")
