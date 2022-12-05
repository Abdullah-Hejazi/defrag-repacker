import sys
from PIL import Image, ImageFilter
import os

def blur_folder(input, output):
    for subdir, dirs, files in os.walk(sys.argv[1]):
        for file in files:
            filePath = os.path.join(subdir, file)
            outputPath = filePath.split('/')
            outputPath[0] = sys.argv[2]

            output = '/'.join(outputPath)
            
            print("Processing: " + filePath)

            OriImage = Image.open(filePath)
            blurImage = OriImage.filter(ImageFilter.GaussianBlur(radius=40))
            
            os.makedirs(os.path.dirname(output), exist_ok=True)
            
            blurImage.save(output)

if __name__ == "__main__":
    n = len(sys.argv)

    if n < 3:
        print("Usage: python blur.py <input-folder> <output-folder>")
        sys.exit(1)

    blur_folder(sys.argv[1], sys.argv[2])
