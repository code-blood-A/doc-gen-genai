import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from llm.hf_client import HFClient
from llm.ollama_client import OllamaClient
from llm.prompts import PACKAGE_DOC_PROMPT

class PackageDocGenerator:
    def __init__(self, use_ollama=False):
        self.client = OllamaClient() if use_ollama else HFClient()

    def _generate_fallback_readme(self, package_name, class_list, class_docs):
        """
        Generates a README from existing class docs when LLM fails.
        """
        readme = f"# {package_name}\n\n"
        readme += f"This package contains **{len(class_list)}** file(s).\n\n"
        readme += "## Files\n\n"
        for cls in class_list:
            readme += f"- 📄 [{cls}.md](./{cls}.md)\n"
        readme += "\n"

        # Include first part of each class doc as summary
        if class_docs:
            readme += "## File Summaries\n\n"
            for cls_name, content in class_docs.items():
                # Extract the Purpose section if it exists
                lines = content.split('\n')
                summary_lines = []
                in_purpose = False
                for line in lines:
                    if '## Purpose' in line:
                        in_purpose = True
                        continue
                    elif line.startswith('## ') and in_purpose:
                        break
                    elif in_purpose and line.strip():
                        summary_lines.append(line.strip())
                
                summary = " ".join(summary_lines[:3]) if summary_lines else content[:200].replace('\n', ' ')
                readme += f"### {cls_name}\n{summary}\n\n"

        return readme

    def generate_package_doc(self, package_name, class_list, class_docs=None):
        """
        Calls LLM to summarize a package/folder.
        Falls back to metadata-based README if LLM fails.
        """
        # Build rich context from existing class docs
        if class_docs:
            summaries = []
            for name, content in class_docs.items():
                summaries.append(f"### {name}\n{content[:500]}")
            class_summaries = "\n\n".join(summaries)
        else:
            class_summaries = ", ".join(class_list)

        prompt = PACKAGE_DOC_PROMPT.format(
            package_name=package_name,
            class_summaries=class_summaries
        )
        result = self.client.generate(prompt)

        if result and len(result) > 50:
            return result

        print(f"[PackageDoc] LLM failed for {package_name}, using fallback.")
        return self._generate_fallback_readme(package_name, class_list, class_docs or {})

    def process_directory(self, docs_dir):
        """
        Walks the generated docs directory (which mirrors source structure)
        and creates README.md for each subfolder.
        """
        if not os.path.exists(docs_dir):
            print(f"[PackageDoc] Docs directory {docs_dir} does not exist yet.")
            return

        readme_count = 0
        for root, dirs, files in os.walk(docs_dir):
            # Get all markdown files (excluding existing READMEs)
            md_files = [f for f in files if f.endswith(".md") and f != "README.md"]

            if not md_files:
                continue

            package_name = os.path.relpath(root, docs_dir)
            if package_name == ".":
                package_name = os.path.basename(docs_dir)

            classes = [f.replace(".md", "") for f in md_files]

            # Read existing class docs for context
            class_docs = {}
            for f in md_files:
                try:
                    with open(os.path.join(root, f), 'r', encoding='utf-8') as fh:
                        class_docs[f.replace(".md", "")] = fh.read()
                except:
                    pass

            print(f"[PackageDoc] Generating README for: {package_name} ({len(classes)} files)...")
            readme_content = self.generate_package_doc(package_name, classes, class_docs)

            if readme_content:
                readme_path = os.path.join(root, "README.md")
                with open(readme_path, 'w', encoding='utf-8') as f:
                    f.write(readme_content)
                print(f"[PackageDoc] Written: {readme_path}")
                readme_count += 1

        print(f"[PackageDoc] Generated {readme_count} README files.")

if __name__ == "__main__":
    generator = PackageDocGenerator(use_ollama=config.OLLAMA_FALLBACK)
    # generator.process_directory(config.DOCS_DIR)
