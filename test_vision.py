import base64
import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from dotenv import load_dotenv

load_dotenv()

def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

llm = ChatOpenAI(
    model="qwen/qwen2.5-vl-7b",
    base_url="http://localhost:1234/v1",
    api_key="lm-studio",
    max_tokens=300
)

# Créer une image factice pour le test (un carré rouge)
img_path = "test_red_square.png"
if not os.path.exists(img_path):
    from PIL import Image
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save(img_path)

base64_image = encode_image(img_path)

message = HumanMessage(
    content=[
        {"type": "text", "text": "De quelle couleur est cette image ?"},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{base64_image}"}}
    ]
)

try:
    print("Appel du modèle Vision...")
    response = llm.invoke([message])
    print("Réponse:", response.content)
except Exception as e:
    print("Erreur:", e)
