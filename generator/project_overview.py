import os
import sys

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from llm.hf_client import HFClient
from llm.ollama_client import OllamaClient
from llm.prompts import ARCHITECTURE_PROMPT

class ProjectOverviewGenerator:
    def __init__(self, use_ollama=False):
        self.client = OllamaClient() if use_ollama else HFClient()

    def _generate_fallback_overview(self, summaries):
        """
        Generates a basic project overview from package summaries when LLM fails.
        """
        overview = "# Project Overview\n\n"
        overview += "## Architecture Summary\n\n"
        overview += "This project contains the following layers/packages:\n\n"
        for s in summaries:
            overview += f"---\n\n{s}\n\n"
        return overview

    def generate_overview(self, module_summaries):
        """
        Calls LLM to generate master README.
        Falls back to metadata-based overview if LLM fails.
        """
        prompt = ARCHITECTURE_PROMPT.format(
            module_summaries=module_summaries
        )
        result = self.client.generate(prompt)

        if result:
            return result

        print(f"[ProjectOverview] LLM failed, using fallback.")
        return None

    def process_project(self):
        """
        Gathers summaries from all packages and generates master doc.
        """
        if not os.path.exists(config.DOCS_DIR):
            print(f"[ProjectOverview] Docs directory does not exist: {config.DOCS_DIR}")
            return

        summaries = []
        for root, dirs, files in os.walk(config.DOCS_DIR):
            if "README.md" in files:
                with open(os.path.join(root, "README.md"), 'r', encoding='utf-8') as f:
                    content = f.read()
                    summaries.append(f"Package {os.path.basename(root)} Summary:\n{content[:500]}...")
        
        if summaries:
            print(f"[ProjectOverview] Generating master project overview from {len(summaries)} packages...")
            overview = self.generate_overview("\n\n".join(summaries))
            
            if overview:
                with open(os.path.join(config.DOCS_DIR, "README.md"), 'w', encoding='utf-8') as f:
                    f.write(overview)
                print(f"[ProjectOverview] Written: {os.path.join(config.DOCS_DIR, 'README.md')}")
            else:
                # Fallback
                fallback = self._generate_fallback_overview(summaries)
                with open(os.path.join(config.DOCS_DIR, "README.md"), 'w', encoding='utf-8') as f:
                    f.write(fallback)
                print(f"[ProjectOverview] Written fallback: {os.path.join(config.DOCS_DIR, 'README.md')}")
        else:
            print("[ProjectOverview] No package READMEs found to summarize.")

if __name__ == "__main__":
    generator = ProjectOverviewGenerator(use_ollama=config.OLLAMA_FALLBACK)
    # generator.process_project()
