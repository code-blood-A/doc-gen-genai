import os
import sys
import re

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from parser.java_parser import JavaFileParser
from llm.hf_client import HFClient
from llm.ollama_client import OllamaClient
from llm.prompts import FILE_DOC_PROMPT

class ClassDocGenerator:
    def __init__(self, use_ollama=False):
        self.client = OllamaClient() if use_ollama else HFClient()

    def _read_source_file(self, file_path):
        """Reads the full source code of a Java file."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"[ClassDoc] Could not read {file_path}: {e}")
            return ""

    def _extract_imports(self, source_code):
        """Extracts import statements from Java source."""
        imports = re.findall(r'^import\s+(.+?);', source_code, re.MULTILINE)
        return imports

    def _get_relative_path(self, file_path):
        """Gets the path relative to TARGET_REPO."""
        try:
            return os.path.relpath(file_path, config.TARGET_REPO)
        except ValueError:
            return os.path.basename(file_path)

    def _generate_fallback_doc(self, file_path, source_code, classes):
        """
        Generates comprehensive documentation from parsed metadata when LLM fails.
        """
        file_name = os.path.basename(file_path)
        rel_path = self._get_relative_path(file_path)
        imports = self._extract_imports(source_code)

        doc = f"# {file_name}\n\n"
        doc += f"**File Path**: `{rel_path}`\n\n"

        # Purpose section
        doc += "## Purpose\n\n"
        if classes:
            cls = classes[0]
            doc += f"This file defines the `{cls['name']}` class"
            if cls['layer'] != "Utility/Helper class":
                doc += f", which serves as part of the **{cls['layer']}**"
            doc += ".\n\n"
            if cls['annotations']:
                doc += f"**Annotations**: `{'`, `'.join(cls['annotations'])}`\n\n"
        else:
            doc += f"This file is part of the project source code.\n\n"

        # Imports section
        doc += "## Imports & Dependencies\n\n"
        if imports:
            # Categorize imports
            java_std = [i for i in imports if i.startswith('java.') or i.startswith('javax.')]
            spring = [i for i in imports if 'springframework' in i or 'spring' in i.lower()]
            third_party = [i for i in imports if i not in java_std and i not in spring and not i.startswith(self._get_project_package(imports))]
            project = [i for i in imports if i not in java_std and i not in spring and i not in third_party]

            if java_std:
                doc += "### Java Standard Library\n"
                for imp in java_std:
                    doc += f"- `{imp}`\n"
                doc += "\n"
            if spring:
                doc += "### Spring Framework\n"
                for imp in spring:
                    doc += f"- `{imp}`\n"
                doc += "\n"
            if third_party:
                doc += "### Third-Party Libraries\n"
                for imp in third_party:
                    doc += f"- `{imp}`\n"
                doc += "\n"
            if project:
                doc += "### Project Internal\n"
                for imp in project:
                    doc += f"- `{imp}`\n"
                doc += "\n"
        else:
            doc += "No imports found.\n\n"

        # Class/Interface overview
        for cls in classes:
            doc += f"## Class: `{cls['name']}`\n\n"
            doc += f"- **Layer**: {cls['layer']}\n"
            if cls['annotations']:
                doc += f"- **Annotations**: {', '.join([f'`{a}`' for a in cls['annotations']])}\n"
            doc += "\n"

            # Fields
            if cls.get('fields'):
                doc += "### Fields\n\n"
                doc += "| Field | Type | Annotations |\n"
                doc += "|-------|------|-------------|\n"
                for field in cls['fields']:
                    annos = ", ".join([f"`{a}`" for a in field['annotations']]) if field['annotations'] else "—"
                    doc += f"| `{field['name']}` | `{field['type']}` | {annos} |\n"
                doc += "\n"

            # Methods
            if cls.get('methods'):
                doc += "### Methods\n\n"
                for m in cls['methods']:
                    params = ", ".join([f"`{t} {n}`" for t, n in m['parameters']]) if m['parameters'] else "none"
                    doc += f"#### `{m['name']}({', '.join([n for _, n in m['parameters']])})`\n\n"
                    doc += f"- **Returns**: `{m['return_type']}`\n"
                    doc += f"- **Parameters**: {params}\n"
                    if m['annotations']:
                        doc += f"- **Annotations**: {', '.join([f'`{a}`' for a in m['annotations']])}\n"
                    doc += "\n"

        # Source code section
        doc += "## Source Code\n\n"
        doc += f"```java\n{source_code}\n```\n"

        return doc

    def _get_project_package(self, imports):
        """Tries to guess the base project package from imports."""
        if not imports:
            return ""
        # Find the most common top-level package
        packages = [imp.split('.')[0] for imp in imports if not imp.startswith('java') and 'springframework' not in imp]
        if packages:
            from collections import Counter
            most_common = Counter(packages).most_common(1)
            if most_common:
                return most_common[0][0]
        return ""

    def generate_file_doc(self, file_path, source_code, classes):
        """
        Sends the full source code to the LLM for comprehensive documentation.
        Falls back to structured metadata-based docs if LLM fails.
        """
        file_name = os.path.basename(file_path)
        rel_path = self._get_relative_path(file_path)

        # Truncate very large files for the LLM (keep first 200 lines)
        lines = source_code.splitlines()
        if len(lines) > 200:
            truncated = "\n".join(lines[:200]) + f"\n// ... ({len(lines) - 200} more lines truncated)"
        else:
            truncated = source_code

        prompt = FILE_DOC_PROMPT.format(
            file_path=rel_path,
            file_name=file_name,
            source_code=truncated
        )

        result = self.client.generate(prompt, max_new_tokens=2048)

        if result and len(result) > 100:  # Ensure meaningful response
            return result

        # Fallback: generate docs from parsed metadata
        print(f"[ClassDoc] LLM failed for {file_name}, using fallback doc generation.")
        return self._generate_fallback_doc(file_path, source_code, classes)

    def process_file(self, file_path):
        """
        Parses a Java file and generates a comprehensive markdown doc
        that mirrors the source directory structure.
        """
        source_code = self._read_source_file(file_path)
        if not source_code:
            return 0

        parser = JavaFileParser(file_path)
        classes = parser.get_classes()

        file_name = os.path.basename(file_path)
        rel_path = self._get_relative_path(file_path)
        rel_dir = os.path.dirname(rel_path)

        print(f"[ClassDoc] Generating docs for {rel_path}...")
        doc_content = self.generate_file_doc(file_path, source_code, classes)

        if doc_content:
            # Mirror the source folder structure inside docs/
            output_dir = os.path.join(config.DOCS_DIR, rel_dir) if rel_dir else config.DOCS_DIR
            os.makedirs(output_dir, exist_ok=True)

            # Save as .md with same name as .java file
            doc_filename = file_name.replace(".java", ".md")
            output_file = os.path.join(output_dir, doc_filename)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            print(f"[ClassDoc] Written: {output_file}")
            return 1

        return 0

if __name__ == "__main__":
    generator = ClassDocGenerator(use_ollama=config.OLLAMA_FALLBACK)
    # Test on a file
    # generator.process_file(r"path/to/test.java")
