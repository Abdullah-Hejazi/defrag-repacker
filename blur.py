import sys
from PIL import Image, ImageFilter
import os
import shutil
import find_naughty_images
import zipfile

SENSITIVITY = 3

def blur_folder(input, output):
    for subdir, dirs, files in os.walk(input):
        for file in files:
            filePath = os.path.join(subdir, file)

            outputPath = filePath.replace(input, output)

            print("Processing: " + filePath)

            OriImage = Image.open(filePath)
            blurImage = OriImage.filter(ImageFilter.GaussianBlur(radius=40))

            if not os.path.exists(os.path.dirname(outputPath)):
                os.makedirs(os.path.dirname(outputPath))

            blurImage.save(outputPath)

def copy_files():
    if not os.path.exists('repack-safe/pk3'):
        os.makedirs('repack-safe/pk3')

    files = os.listdir('repack')

    for file in files:
        if file.endswith('.pk3') and 'textures' in file:
            print('Copying: ' + file)
            shutil.copy('repack/' + file, 'repack-safe/pk3/' + file.replace('.pk3', '-safe.pk3'))

if __name__ == "__main__":
    copy_files()

    if not os.path.exists('repack-safe/nude-textures'):
        os.makedirs('repack-safe/nude-textures')

    if not os.path.exists('repack-safe/safe-textures'):
        os.makedirs('repack-safe/safe-textures')

    find_naughty_images.main('repack-safe/pk3', 'repack-safe/nude-textures', SENSITIVITY)

    blur_folder('repack-safe/nude-textures', 'repack-safe/safe-textures')

    with zipfile.ZipFile('repack/zzz-safe-textures.pk3', 'w') as zip:
        for subdir, dirs, files in os.walk('repack-safe/safe-textures'):
            for file in files:
                filePath = os.path.join(subdir, file)
                zip.write(filePath, filePath.replace('\\', '/').replace('repack-safe/safe-textures/', ''))
