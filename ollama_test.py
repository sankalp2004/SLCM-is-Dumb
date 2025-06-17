# ollama_test.py - Test Ollama installation and vision models
import ollama
import os

def test_ollama_installation():
    """Test if Ollama is properly installed and has vision models"""
    try:
        print("Testing Ollama installation...")
        
        # List available models
        models = ollama.list()
        print(f"Available models: {len(models.get('models', []))}")
        
        vision_models = []
        for model in models.get('models', []):
            model_name = model['name']
            print(f"- {model_name}")
            if any(vm in model_name.lower() for vm in ['llava', 'vision', 'llama3.2-vision']):
                vision_models.append(model_name)
        
        if vision_models:
            print(f"\n✓ Found {len(vision_models)} vision models:")
            for vm in vision_models:
                print(f"  - {vm}")
            
            # Test a simple vision model call
            print(f"\nTesting vision model: {vision_models[0]}")
            
            # Create a simple test (you'll need a test image)
            if os.path.exists("test_image.png"):
                response = ollama.chat(
                    model=vision_models[0],
                    messages=[{
                        'role': 'user',
                        'content': 'What do you see in this image?',
                        'images': ['test_image.png']
                    }]
                )
                print(f"✓ Vision model test successful!")
                print(f"Response: {response['message']['content']}")
            else:
                print("Create a test_image.png file to test vision capabilities")
                
        else:
            print("\n✗ No vision models found!")
            print("Install a vision model with: ollama pull llava:13b")
            
        return len(vision_models) > 0
        
    except Exception as e:
        print(f"✗ Ollama test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_ollama_installation()
    if success:
        print("\n✓ Ollama is ready for captcha solving!")
    else:
        print("\n✗ Ollama setup incomplete. Please follow installation instructions.")
