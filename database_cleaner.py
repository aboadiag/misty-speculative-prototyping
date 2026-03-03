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
    unique_people = {}

    print(f"--- Starting Pruning on {len(files)} files ---")

    for filename in files:
        path = os.path.join(KNOWN_FACES, filename)
        # Identify person (e.g., 'kyle_1.jpg' -> 'kyle')
        name = filename.split('_')[0].split('.')[0].lower()
        blur_score = get_blur_score(path)

        if name not in unique_people:
            unique_people[name] = {'filename': filename, 'score': blur_score}
        else:
            old_best = unique_people[name]
            if blur_score > old_best['score']:
                shutil.move(os.path.join(KNOWN_FACES, old_best['filename']), 
                            os.path.join(PRUNED_FOLDER, old_best['filename']))
                print(f"Replacing {old_best['filename']} with sharper version: {filename}")
                unique_people[name] = {'filename': filename, 'score': blur_score}
            else:
                shutil.move(path, os.path.join(PRUNED_FOLDER, filename))
                print(f"Removing low-quality/duplicate: {filename} (Score: {blur_score:.2f})")

    # --- THE CACHE WIPE ---
    print("Wiping DeepFace representation cache...")
    for f in os.listdir(KNOWN_FACES):
        if f.endswith(".pkl"):
            os.remove(os.path.join(KNOWN_FACES, f))
            print(f"Deleted cache file: {f}")

    print("--- Maintenance Complete ---")

if __name__ == "__main__":
    prune_database()