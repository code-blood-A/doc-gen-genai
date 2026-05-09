import javalang
import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from parser.spring_annotation import detect_layer, get_annotations

class JavaFileParser:
    def __init__(self, file_path):
        self.file_path = file_path
        with open(file_path, 'r', encoding='utf-8') as f:
            self.code = f.read()
        try:
            self.tree = javalang.parse.parse(self.code)
        except Exception:
            # Silence error here, handle fallback in get_classes
            self.tree = None
        self.lines = self.code.splitlines()

    def get_classes(self):
        if not self.tree:
            # Fallback for Records (Java 14+)
            import re
            record_match = re.search(r"(?:public\s+)?record\s+(\w+)\s*\(([^)]*)\)", self.code)
            if record_match:
                name = record_match.group(1)
                return [{
                    "name": name,
                    "annotations": get_annotations(self.code),
                    "layer": detect_layer(self.code),
                    "line": 1,
                    "methods": [],
                    "fields": []
                }]
            
            # If everything fails, try to at least find a class/interface name via regex
            gen_match = re.search(r"(?:class|interface|record|enum)\s+(\w+)", self.code)
            if gen_match:
                 return [{
                    "name": gen_match.group(1),
                    "annotations": get_annotations(self.code),
                    "layer": detect_layer(self.code),
                    "line": 1,
                    "methods": [],
                    "fields": []
                }]
            return []
        classes = []
        for path, node in self.tree.filter(javalang.tree.ClassDeclaration):
            class_info = {
                "name": node.name,
                "annotations": [anno.name for anno in node.annotations],
                "layer": detect_layer(self.code),
                "line": node.position.line if node.position else None,
                "methods": self.get_methods_for_class(node),
                "fields": self.get_fields_for_class(node)
            }
            classes.append(class_info)
        return classes

    def get_methods_for_class(self, class_node):
        methods = []
        for method in class_node.methods:
            methods.append({
                "name": method.name,
                "return_type": method.return_type.name if method.return_type else "void",
                "parameters": [(p.type.name, p.name) for p in method.parameters],
                "line": method.position.line if method.position else None,
                "annotations": [anno.name for anno in method.annotations]
            })
        return methods

    def get_fields_for_class(self, class_node):
        fields = []
        for field in class_node.fields:
            for declarator in field.declarators:
                fields.append({
                    "name": declarator.name,
                    "type": field.type.name,
                    "annotations": [anno.name for anno in field.annotations]
                })
        return fields

    def extract_method_code(self, method_name, class_name=None):
        """
        Heuristic to extract the actual code block for a method.
        Useful for chunking and LLM analysis.
        """
        # This is a simplified version; real robust extraction needs more complex logic
        # OR we use the line numbers from javalang and search for the closing brace.
        return f"// Code for {method_name} will be extracted here."

if __name__ == "__main__":
    # Test with a local file if available
    pass
