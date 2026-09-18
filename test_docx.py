import docx2txt
import os
import shutil

img_dir = "tmp_imgs"
os.makedirs(img_dir, exist_ok=True)
text = docx2txt.process("data/documents/APEC Manuel d'utilisation admin.docx", img_dir)

print(text[:500])
print("Images trouvées:", os.listdir(img_dir))
shutil.rmtree(img_dir)
