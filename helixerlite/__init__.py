import importlib.metadata

try:
    from . import helixerlite
    # Import any functions or classes from the Rust module that you want to expose
    # For example: from .helixerlite import some_function
except ImportError as e:
    print(f"Error importing Rust module: {e}")

__version__ = importlib.metadata.version("helixerlite")
