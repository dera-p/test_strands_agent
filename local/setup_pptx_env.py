import subprocess
import sys
import shutil
import os

def check_command(command):
    return shutil.which(command) is not None

def run_command(command, shell=False):
    print(f"Running: {' '.join(command) if isinstance(command, list) else command}")
    try:
        subprocess.check_call(command, shell=shell)
        return True
    except subprocess.CalledProcessError:
        print(f"Error running: {command}")
        return False

def main():
    print("--- Setting up PPTX Skill Environment ---")

    # 1. Install current package (agentskills) in editable mode
    print("\n[1/4] Installing agentskills package...")
    if not run_command([sys.executable, "-m", "pip", "install", "-e", "."]):
        print("Failed to install agentskills.")
        return

    # 2. Python Dependencies for pptx skill
    print("\n[2/4] Installing Python dependencies for pptx skill...")
    requirements = ["markitdown[pptx]", "defusedxml", "strands-agents", "strands-agents-tools"]
    if not run_command([sys.executable, "-m", "pip", "install"] + requirements):
        print("Failed to install Python dependencies.")
        return

    # 3. Node.js Dependencies
    print("\n[3/4] Installing Node.js dependencies...")
    if not check_command("npm"):
        print("Error: 'npm' not found. Please install Node.js from https://nodejs.org/")
        return
    
    # Install packages locally to avoid permission issues and for better containment
    # We use 'npm install' without -g. 
    # Note: agentskills pptx scripts might assume global binaries or locally resolvable ones.
    # We will verify if `npx` can find them.
    node_packages = ["pptxgenjs", "playwright", "react-icons", "sharp"]
    if not run_command(["npm", "install"] + node_packages, shell=True):
         print("Failed to install Node.js packages.")
         return

    # Install Playwright browsers (chromium)
    print("Installing Playwright browsers (chromium)...")
    # Using explicit chromium install with dependencies as requested
    command = "npx playwright install --with-deps chromium"
    if not run_command(command, shell=True):
        print("Warning: Failed to install Playwright dependencies with --with-deps. Trying without...")
        if not run_command("npx playwright install chromium", shell=True):
            print("Failed to install Playwright chromium.")

    # 4. System Tools check
    print("\n[4/4] Checking System Tools...")
    
    missing_manual = []
    
    # Check for LibreOffice
    # Common paths on Windows? shutil.which might not find it if not in PATH.
    # We can try to give a hint.
    if check_command("soffice"):
        print(" [OK] LibreOffice (soffice) found.")
    else:
        print(" [MISSING] LibreOffice (soffice) not found in PATH.")
        missing_manual.append("LibreOffice")

    # Check for Poppler
    if check_command("pdftoppm"):
        print(" [OK] Poppler (pdftoppm) found.")
    else:
        print(" [MISSING] Poppler (pdftoppm) not found in PATH.")
        missing_manual.append("Poppler")

    print("\n--- Setup Complete ---")
    if missing_manual:
        print("\nWARNING: The following tools need manual installation for full functionality (PDF/Image conversion):")
        for tool in missing_manual:
            print(f" - {tool}")
            if tool == "LibreOffice":
                print("   Download: https://www.libreoffice.org/download/")
                print("   * Add the installation 'bin' folder to your System PATH.")
            elif tool == "Poppler":
                print("   Windows: Download binary from https://github.com/oschwartz10612/poppler-windows/releases/")
                print("   * Extract and add 'bin' folder to your System PATH.")

if __name__ == "__main__":
    main()
