#!/usr/bin/env python3
import os
import sys
import zipfile
import tempfile
import subprocess
import glob
import traceback
import site
import importlib.util


def main():
    # Find wheel files
    wheel_files = glob.glob("dist/*.whl")
    if not wheel_files:
        print("No wheel files found in dist/")
        return 1

    print(f"Found wheel files: {wheel_files}")

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        for wheel_file in wheel_files:
            print(f"\nExamining wheel: {wheel_file}")

            # Extract the wheel
            with zipfile.ZipFile(wheel_file, "r") as zip_ref:
                zip_ref.extractall(temp_dir)
                print(f"Extracted to: {temp_dir}")

                # List all files in the wheel
                print("\nFiles in the wheel:")
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        rel_path = os.path.relpath(file_path, temp_dir)
                        print(f"  {rel_path}")

            # Install the wheel
            print("\nInstalling wheel...")
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pip",
                    "install",
                    "--force-reinstall",
                    wheel_file,
                ],
                capture_output=True,
                text=True,
            )
            print(f"Installation stdout: {result.stdout}")
            print(f"Installation stderr: {result.stderr}")

            # Try to import the module
            print("\nTrying to import helixerlite...")
            try:
                import helixerlite

                print(
                    f"Successfully imported helixerlite version {helixerlite.__version__}"
                )
                print(f"helixerlite.__file__: {helixerlite.__file__}")
                print(f"helixerlite module contents: {dir(helixerlite)}")

                try:
                    import helixerpost

                    print(f"Successfully imported helixerpost")
                    print(f"helixerpost.__file__: {helixerpost.__file__}")
                    print(f"helixerpost module contents: {dir(helixerpost)}")
                except ImportError as e:
                    print(f"Error importing helixerpost: {e}")
            except ImportError as e:
                print(f"Error importing helixerlite: {e}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
