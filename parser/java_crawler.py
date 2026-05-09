import os
import sys

# Add the project root to sys.path to allow importing config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def get_java_files(repo_path=None):
    """
    Crawls the repository and returns a list of absolute paths to .java files.
    Excludes directories specified in config.EXCLUDED_DIRS.
    """
    if not repo_path:
        repo_path = config.TARGET_REPO
        
    if not repo_path or not os.path.exists(repo_path):
        print(f"Error: Repository path '{repo_path}' does not exist.")
        return []

    java_files = []
    for root, dirs, files in os.walk(repo_path):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in config.EXCLUDED_DIRS]
        
        for file in files:
            if file.endswith(config.JAVA_EXT):
                java_files.append(os.path.join(root, file))
                
    return java_files

if __name__ == "__main__":
    files = get_java_files()
    print(f"Found {len(files)} Java files.")
    for f in files[:5]:
        print(f" - {f}")
    if len(files) > 5:
        print("   ...")
