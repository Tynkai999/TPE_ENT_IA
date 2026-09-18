import docx2txt
import tempfile
import shutil
from pathlib import Path
from app.rag.vision import process_document_images

path = Path("data/documents/APec Manuel d'utilisation agent.docx")
img_dir = Path(tempfile.mkdtemp(prefix="tpe_vision_"))
try:
    print("Extracting...")
    text = docx2txt.process(str(path), str(img_dir))
    print("Files found:", list(img_dir.glob("*.*")))
    vision_text = process_document_images(img_dir)
    print("Vision text length:", len(vision_text))
finally:
    shutil.rmtree(img_dir, ignore_errors=True)
