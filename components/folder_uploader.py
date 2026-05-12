import os
import base64
import tempfile
import streamlit.components.v1 as components

# Path to the HTML component directory
_COMPONENT_DIR = os.path.join(os.path.dirname(__file__), "folder_uploader_html")

# Declare the Streamlit custom component
_folder_uploader_func = components.declare_component(
    "folder_uploader",
    path=_COMPONENT_DIR,
)


def folder_uploader(key: str = "folder_uploader") -> str | None:
    """
    Renders a folder-picker component.

    The user selects a local project folder in the browser.
    All .java files are read client-side (preserving relative paths),
    base64-encoded, and sent to Python.

    Returns
    -------
    str | None
        Absolute path to a temporary directory containing the extracted
        .java files (with the original folder structure preserved), or
        None if no folder has been selected yet.
    """
    raw = _folder_uploader_func(key=key, default=None)

    if not raw:
        return None

    # Check session state so we don't re-extract on every Streamlit rerun
    import streamlit as st
    cache_key = f"_folder_uploader_tmpdir_{key}"

    # raw is a list of {path: str, content: str (base64)}
    # Use first file path as a simple fingerprint
    fingerprint = raw[0]["path"] if raw else ""
    fingerprint_key = f"_folder_uploader_fp_{key}"

    if (
        cache_key in st.session_state
        and st.session_state.get(fingerprint_key) == fingerprint
        and os.path.exists(st.session_state[cache_key])
    ):
        # Same folder already extracted — reuse temp dir
        return st.session_state[cache_key]

    # Create a fresh temp directory
    tmp_dir = tempfile.mkdtemp(prefix="genai_java_")

    for file_info in raw:
        rel_path: str = file_info["path"]        # e.g. "MyProject/src/main/java/Foo.java"
        b64_content: str = file_info["content"]  # base64-encoded file content

        # Build the full destination path inside the temp dir
        dest_path = os.path.join(tmp_dir, rel_path.replace("/", os.sep))
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)

        # Decode and write the file
        with open(dest_path, "wb") as f:
            f.write(base64.b64decode(b64_content))

    # Cache so subsequent reruns don't re-extract
    st.session_state[cache_key] = tmp_dir
    st.session_state[fingerprint_key] = fingerprint

    return tmp_dir
