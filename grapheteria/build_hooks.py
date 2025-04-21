import shutil
import subprocess
from pathlib import Path
from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class UIBuildHook(BuildHookInterface):
    def initialize(self, version, build_data):
        """Build the UI before packaging"""
        # Get the project root directory
        root = Path(__file__).parent
        ui_dir = root / "ui"

        # Create the static directory if it doesn't exist
        static_dir = root / "server" / "static"
        static_dir.mkdir(exist_ok=True, parents=True)

        # Build the UI
        print("Building UI...")
        try:
            subprocess.run(["npm", "install"], cwd=ui_dir, check=True)
            subprocess.run(["npm", "run", "build"], cwd=ui_dir, check=True)

            # Copy the built files to the static directory
            ui_build_dir = (
                ui_dir / "dist"
            )  # Adjust if your output directory is different
            ui_dest_dir = static_dir / "ui"

            # Clear destination if it exists
            if ui_dest_dir.exists():
                shutil.rmtree(ui_dest_dir)

            # Copy built UI files
            shutil.copytree(ui_build_dir, ui_dest_dir)

            print(f"UI built and copied to {ui_dest_dir}")

        except subprocess.CalledProcessError as e:
            print(f"Error building UI: {e}")
            # Don't fail the build if UI build fails
            # Comment the line below if you want to fail the build on UI build failure
            # raise
