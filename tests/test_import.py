import unittest
import sys
import os
import subprocess


class TestImport(unittest.TestCase):
    def test_import(self):
        """Test that the module can be imported."""
        print(f"Python version: {sys.version}")
        print(f"Python path: {sys.path}")
        print(f"Current directory: {os.getcwd()}")

        # List installed packages
        print("\nInstalled packages:")
        subprocess.run([sys.executable, "-m", "pip", "list"], check=False)

        # List files in site-packages
        site_packages = [p for p in sys.path if "site-packages" in p][0]
        print(f"\nContents of {site_packages}:")
        for item in sorted(os.listdir(site_packages)):
            if "helixer" in item.lower():
                print(f"  {item}")

        try:
            import helixerlite

            print(
                f"\nSuccessfully imported helixerlite version {helixerlite.__version__}"
            )
            print(f"helixerlite.__file__: {helixerlite.__file__}")
            print(f"helixerlite module contents: {dir(helixerlite)}")
            self.assertTrue(hasattr(helixerlite, "__version__"))

            try:
                import helixerpost

                print(f"\nSuccessfully imported helixerpost")
                print(f"helixerpost.__file__: {helixerpost.__file__}")
                print(f"helixerpost module contents: {dir(helixerpost)}")
            except ImportError as e:
                print(f"\nError importing helixerpost: {e}")
        except ImportError as e:
            print(f"\nError importing helixerlite: {e}")
            raise


if __name__ == "__main__":
    unittest.main()
