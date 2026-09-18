import base64
import os
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from app.core.config import settings

def encode_image(image_path: Path) -> str:
    """Encode une image en Base64."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode('utf-8')

def get_vision_llm():
    """Récupère l'instance du modèle configuré (qui doit être un modèle Vision)."""
    return ChatOpenAI(
        model=settings.lm_model,
        base_url=settings.lm_base_url,
        api_key=settings.lm_api_key,
        max_tokens=200,
        temperature=0.1
    )

def describe_image(image_path: Path) -> str:
    """
    Envoie l'image au modèle Vision pour obtenir une description textuelle.
    """
    base64_image = encode_image(image_path)
    llm = get_vision_llm()
    
    prompt = (
        "Analyse cette capture d'écran tirée d'un manuel utilisateur de la plateforme de l'ENT (TPE). "
        "Décris en une à deux phrases maximum l'action, le menu, le formulaire ou les boutons visibles "
        "qui pourraient être utiles à un utilisateur. Ne décris pas les éléments purement décoratifs."
    )
    
    mime_type = "image/jpeg" if image_path.suffix.lower() in [".jpg", ".jpeg"] else "image/png"
    
    message = HumanMessage(
        content=[
            {"type": "text", "text": prompt},
            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{base64_image}"}}
        ]
    )
    
    try:
        response = llm.invoke([message])
        return response.content.strip()
    except Exception as e:
        print(f"[Vision] Erreur lors de l'analyse de l'image {image_path.name} : {e}")
        return ""

def process_document_images(img_dir: Path) -> list[str]:
    """
    Parcourt toutes les images extraites dans img_dir et retourne une liste 
    contenant les descriptions générées pour chaque image.
    """
    if not img_dir.exists():
        return []
        
    image_files = sorted(img_dir.glob("*.*"))
    if not image_files:
        return []
        
    print(f"\n[Vision] Démarrage de l'analyse de {len(image_files)} images avec {settings.lm_model}...")
    
    descriptions = []
    
    for idx, img_path in enumerate(image_files):
        # Filtrer les extensions valides
        if img_path.suffix.lower() not in ['.png', '.jpg', '.jpeg']:
            continue
            
        print(f"  > Analyse de l'image {idx+1}/{len(image_files)} ({img_path.name})...")
        desc = describe_image(img_path)
        if desc:
            # On crée un document textuel autonome pour cette image
            descriptions.append(f"Capture d'écran (Image {img_path.name}) : {desc}")
            
    return descriptions

