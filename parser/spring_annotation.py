import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config

def detect_layer(java_code: str) -> str:
    """
    Detects the Spring layer of a class based on its annotations.
    """
    for annotation, description in config.SPRING_ANNOTATIONS.items():
        if annotation in java_code:
            return description
    return "Utility/Helper class"

def get_annotations(java_code: str):
    """
    Returns a list of all detected Spring annotations in the code.
    """
    detected = []
    for annotation in config.SPRING_ANNOTATIONS.keys():
        if annotation in java_code:
            detected.append(annotation)
    return detected
