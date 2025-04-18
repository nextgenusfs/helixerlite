import unittest
import sys
import os

class TestImport(unittest.TestCase):
    def test_import(self):
        """Test that the module can be imported."""
        print(f"Python version: {sys.version}")
        print(f"Python path: {sys.path}")
        print(f"Current directory: {os.getcwd()}")
        
        try:
            import helixerlite
            print(f"Successfully imported helixerlite version {helixerlite.__version__}")
            self.assertTrue(hasattr(helixerlite, "__version__"))
        except ImportError as e:
            print(f"Error importing helixerlite: {e}")
            raise

if __name__ == "__main__":
    unittest.main()
