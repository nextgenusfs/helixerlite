import importlib.metadata
import sys

# Make helixerpost available at the package level
try:
    import helixerpost

    sys.modules["helixerlite.helixerpost"] = helixerpost
except ImportError as e:
    print(f"Error importing helixerpost module: {e}")

__version__ = importlib.metadata.version("helixerlite")
