# database_cleaner.py
# prune database and stored images to ensure high quality data collection

import os
import cv2
import shutil

# Paths
KNOWN_FACES = "known_faces"
PRUNED_FOLDER = "pruned_backups"

def get_blur_score(image_path):
    """Higher score means sharper image. Under 100 is usually blurry."""
    image = cv2.imread(image_path)
    if image is None: return 0
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return cv2.Laplacian(gray, cv2.CV_64F).var()

def prune_database():
    if not os.path.exists(PRUNED_FOLDER):
        os.makedirs(PRUNED_FOLDER)

    files = [f for f in os.listdir(KNOWN_FACES) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    people_collections = {}

    print(f"--- Maintenance Starting ---")

    for filename in files:
        path = os.path.join(KNOWN_FACES, filename)
        name = filename.split('_')[0].split('.')[0].lower()
        score = get_blur_score(path)

        if name not in people_collections:
            people_collections[name] = []
        people_collections[name].append({'filename': filename, 'score': score})

    for name, images in people_collections.items():
        # Sort images by blur score (sharpest first)
        images.sort(key=lambda x: x['score'], reverse=True)
        
        # Keep the top 5 sharpest images, move the rest to pruned
        to_keep = images[:5] 
        to_prune = images[5:]

        for item in to_prune:
            shutil.move(os.path.join(KNOWN_FACES, item['filename']), 
                        os.path.join(PRUNED_FOLDER, item['filename']))
            print(f"Pruned extra/blurry image for {name}: {item['filename']}")

    # Wipe the .pkl cache so DeepFace sees the new gallery
    for f in os.listdir(KNOWN_FACES):
        if f.endswith(".pkl"):
            os.remove(os.path.join(KNOWN_FACES, f))

if __name__ == "__main__":
    prune_database()