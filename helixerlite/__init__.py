import importlib.metadata
import sys

# Re-export helixerpost functions at the helixerlite level
try:
    import helixerpost

    # Make helixerpost available as helixerlite.helixerpost
    sys.modules["helixerlite.helixerpost"] = helixerpost
    # Re-export helixerpost functions
    from helixerpost import *
except ImportError as e:
    print(f"Error importing helixerpost module: {e}")

__version__ = importlib.metadata.version("helixerlite")
