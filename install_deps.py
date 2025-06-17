from dependencyfixer import fix
import importlib

# List of packages you need
dep = ['pillow', 'amazoncaptcha']

# Let dependency-fixer handle the installation
result, leftdep = fix(dep, auto=True, verbose=True)

if result == 1:
    # All modules installed successfully
    print("All dependencies installed successfully!")
    # Now you can import amazoncaptcha
    amazoncaptcha = importlib.import_module('amazoncaptcha')
    
elif result == -1:
    # Some modules couldn't be installed
    print(f"Some dependencies failed: {leftdep}")
    # Handle the failed dependencies
    
else:
    # No modules could be installed
    print(f"Installation failed for: {leftdep}")
