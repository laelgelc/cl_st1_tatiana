import os
import shutil
import numpy as np
import pandas as pd
from PIL import Image
from concurrent.futures import ProcessPoolExecutor
from functools import partial

def calculate_dhash(filename, directory, hash_size=8):
    """Worker function to generate a 64-bit difference hash for an image."""
    image_path = os.path.join(directory, filename)
    try:
        with Image.open(image_path) as img:
            img = img.convert('L').resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
            pixels = np.asarray(img)
            diff = pixels[:, 1:] > pixels[:, :-1]
            p_hash = "".join(f"{int(b)}" for b in diff.flatten())
            return {'filename': filename, 'perceptual_hash': p_hash}
    except Exception:
        return {'filename': filename, 'perceptual_hash': None}

def run_near_duplicate_sort(source_dir, unique_dir, duplicates_dir, num_workers=None):
    # 1. Ensure output directories exist
    os.makedirs(unique_dir, exist_ok=True)
    os.makedirs(duplicates_dir, exist_ok=True)

    # 2. Gather files from source
    files = [f for f in os.listdir(source_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    print(f"Analyzing {len(files)} images for similarity using parallel workers...")

    # 3. Parallel Hash Calculation
    worker_with_path = partial(calculate_dhash, directory=source_dir)
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = list(executor.map(worker_with_path, files))

    df = pd.DataFrame(results)

    # 4. Identify Near-Duplicates
    # keep='first' means the first time we see a hash, it's marked False (not a dupe)
    # Every subsequent time we see that same hash, it's marked True (is a dupe)
    df['is_extra_copy'] = df.duplicated(subset=['perceptual_hash'], keep='first') & df['perceptual_hash'].notnull()

    print(f"Analysis complete. Sorting files...")

    # 5. Copy files to respective directories
    for _, row in df.iterrows():
        src_path = os.path.join(source_dir, row['filename'])

        if row['is_extra_copy']:
            # Create a subdirectory named after the hash to group similar images
            hash_subdir = os.path.join(duplicates_dir, row['perceptual_hash'])
            os.makedirs(hash_subdir, exist_ok=True)
            dest_path = os.path.join(hash_subdir, row['filename'])
        else:
            dest_path = os.path.join(unique_dir, row['filename'])

        shutil.copy2(src_path, dest_path)

    return df

if __name__ == '__main__':
    # Configuration
    input_folder = 'corpus/deduplicated_1'
    clean_folder = 'corpus/deduplicated_2'
    near_dupes_folder = 'corpus/near_duplicates'

    df_final = run_near_duplicate_sort(input_folder, clean_folder, near_dupes_folder)

    # Export to a file
    df_final.to_json("corpus/df_images_perceptual_hash.jsonl", orient='records', lines=True)
    df_final.to_excel("corpus/df_images_perceptual_hash.xlsx", index=False)

    # Summary
    total = len(df_final)
    unique_count = len(df_final[~df_final['is_extra_copy']])
    dupe_count = df_final['is_extra_copy'].sum()

    print("\n--- Summary ---")
    print(f"Processed: {total} files")
    print(f"Unique images moved to '{clean_folder}': {unique_count}")
    print(f"Near-duplicates moved to '{near_dupes_folder}': {dupe_count}")