import os
import requests
from tqdm import tqdm

def download_file(url: str, filename: str):
    """Download a file with progress bar"""
    response = requests.get(url, stream=True)
    total_size = int(response.headers.get('content-length', 0))
    
    # Create models directory if it doesn't exist
    os.makedirs('models', exist_ok=True)
    
    filepath = os.path.join('models', filename)
    
    with open(filepath, 'wb') as file, tqdm(
        desc=filename,
        total=total_size,
        unit='iB',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for data in response.iter_content(chunk_size=1024):
            size = file.write(data)
            pbar.update(size)

def main():
    # URL for a quantized Llama 2 model (Q4_K_M version - smaller and more efficient)
    model_url = "https://huggingface.co/TheBloke/Llama-2-7B-Chat-GGUF/resolve/main/llama-2-7b-chat.Q4_K_M.gguf"
    model_filename = "llama-2-7b-chat.Q4_K_M.gguf"
    
    print(f"Downloading {model_filename}...")
    download_file(model_url, model_filename)
    print(f"Model downloaded successfully to models/{model_filename}")

if __name__ == "__main__":
    main() 