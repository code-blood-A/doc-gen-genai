import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from parser.java_parser import JavaFileParser
from llm.hf_client import HFClient
from llm.ollama_client import OllamaClient
from llm.prompts import METHOD_DOC_PROMPT

class JavadocWriter:
    def __init__(self, use_ollama=False):
        self.client = OllamaClient() if use_ollama else HFClient()

    def generate_javadoc(self, class_name, method_info):
        """
        Gathers context and calls LLM to generate Javadoc.
        """
        prompt = METHOD_DOC_PROMPT.format(
            class_name=class_name,
            method_name=method_info['name'],
            parameters=method_info['parameters'],
            return_type=method_info['return_type'],
            code_snippet=f"// Method: {method_info['name']}" # We can expand this
        )
        return self.client.generate(prompt)

    def process_file(self, file_path):
        """
        Parses file and injects Javadocs for all methods.
        """
        parser = JavaFileParser(file_path)
        classes = parser.get_classes()
        
        if not classes:
            return 0
        
        # We need to process from bottom to top to avoid shifting line numbers
        # OR we can reconstruct the file lines.
        lines = parser.lines.copy()
        
        modifications = []
        for cls in classes:
            for method in cls['methods']:
                # Skip if already has Javadoc (simple check)
                line_idx = method['line'] - 1
                if line_idx > 0 and "*/" in lines[line_idx - 1]:
                    continue
                
                print(f"Generating Javadoc for {cls['name']}.{method['name']}...")
                javadoc = self.generate_javadoc(cls['name'], method)
                if javadoc:
                    modifications.append((line_idx, javadoc))
        
        # Sort modifications in reverse order of line index
        modifications.sort(key=lambda x: x[0], reverse=True)
        
        for line_idx, javadoc in modifications:
            # Indent the javadoc correctly
            current_line = lines[line_idx]
            indent = current_line[:len(current_line) - len(current_line.lstrip())]
            formatted_javadoc = "\n".join([f"{indent}{l.strip()}" for l in javadoc.splitlines()])
            lines.insert(line_idx, formatted_javadoc)
            
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("\n".join(lines))
        
        return len(modifications)

if __name__ == "__main__":
    writer = JavadocWriter(use_ollama=config.OLLAMA_FALLBACK)
    # Test on a file
    # writer.process_file(r"path/to/test.java")
