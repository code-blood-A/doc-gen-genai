import os
import sys
import chromadb
from chromadb.utils import embedding_functions
from sentence_transformers import SentenceTransformer

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from parser.java_crawler import get_java_files
from parser.java_parser import JavaFileParser

class CodeEmbedder:
    def __init__(self, db_path="chroma_db"):
        self.client = chromadb.PersistentClient(path=db_path)
        # Use a high-quality, relatively small model for code/text
        self.embedding_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-miniLM-L6-v2"
        )
        self.collection = self.client.get_or_create_collection(
            name="java_code_base",
            embedding_function=self.embedding_fn
        )

    def index_repository(self, repo_path=None):
        """
        Walks the repo, parses files, and indexes methods/classes into ChromaDB.
        """
        java_files = get_java_files(repo_path)
        print(f"Indexing {len(java_files)} files...")

        for file_path in java_files:
            try:
                parser = JavaFileParser(file_path)
                classes = parser.get_classes()
                
                for cls in classes:
                    # Index the class itself
                    class_id = f"{file_path}_{cls['name']}"
                    class_metadata = {
                        "type": "class",
                        "file": file_path,
                        "name": cls['name'],
                        "layer": cls['layer']
                    }
                    class_text = f"Class: {cls['name']}\nLayer: {cls['layer']}\nAnnotations: {', '.join(cls['annotations'])}"
                    
                    self.collection.upsert(
                        documents=[class_text],
                        metadatas=[class_metadata],
                        ids=[class_id]
                    )

                    # Index each method
                    for method in cls['methods']:
                        method_id = f"{class_id}_{method['name']}"
                        method_metadata = {
                            "type": "method",
                            "file": file_path,
                            "class": cls['name'],
                            "name": method['name'],
                            "return_type": method['return_type']
                        }
                        method_text = f"Method: {method['name']} in Class {cls['name']}\n"
                        method_text += f"Returns: {method['return_type']}\n"
                        method_text += f"Parameters: {method['parameters']}\n"
                        method_text += f"Annotations: {method['annotations']}"
                        
                        self.collection.upsert(
                            documents=[method_text],
                            metadatas=[method_metadata],
                            ids=[method_id]
                        )
            except Exception as e:
                print(f"Warning: Could not parse {file_path}: {e}")

    def search(self, query, n_results=3):
        """
        Queries the vector database for relevant code chunks.
        """
        return self.collection.query(
            query_texts=[query],
            n_results=n_results
        )

if __name__ == "__main__":
    embedder = CodeEmbedder()
    # Test indexing
    # embedder.index_repository()
    # print("Searching for 'User'...")
    # results = embedder.search("UserController")
    # print(results)
