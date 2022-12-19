import sys, os, pathlib
import time
import argparse
import zipfile
import io

from torchvision import transforms
import numpy as np
from PIL import Image
import onnxruntime as rt
from tqdm import tqdm

parser = argparse.ArgumentParser(description="Find nudity in PK3 files.", usage="find_naughty_images.py --dir <dir_with_pk3s> --out <output_dir>")
parser.add_argument("-d", "--dir", metavar='<path>', type=str, required=True, help="directory with pk3s")
parser.add_argument("-o", "--out", metavar='<path>', type=str, required=True, help="output directory")
parser.add_argument("-s", "--sensitivity", metavar='[0, 1, 2]', type=int, default=1, help="how sensitive you want the script to be. [min] 0 = less sensitive (more false positives). [max] 3 = more sensitive (less false positives)")

model_path = 'ResNet50_nsfw_model_finetuned.onnx'
labels_bin = ['naughty', 'nice']

test_transforms = transforms.Compose([
    transforms.Resize((224,224)),
    # transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
])

def softmax(X, theta = 1.0, axis = None):
    """
    Compute the softmax of each element along an axis of X.

    Parameters
    ----------
    X: ND-Array. Probably should be floats.
    theta (optional): float parameter, used as a multiplier
        prior to exponentiation. Default = 1.0
    axis (optional): axis to compute values along. Default is the
        first non-singleton axis.

    Returns an array the same size as X. The result will sum to 1
    along the specified axis.
    """

    # make X at least 2d
    y = np.atleast_2d(X)

    # find axis
    if axis is None:
        axis = next(j[0] for j in enumerate(y.shape) if j[1] > 1)

    # multiply y against the theta parameter,
    y = y * float(theta)

    # subtract the max for numerical stability
    y = y - np.expand_dims(np.max(y, axis = axis), axis)

    # exponentiate y
    y = np.exp(y)

    # take the sum along the specified axis
    ax_sum = np.expand_dims(np.sum(y, axis = axis), axis)

    # finally: divide elementwise
    p = y / ax_sum

    # flatten if X was 1D
    if len(X.shape) == 1: p = p.flatten()

    return p

# if True = prefix exists
def check_prefix(needle, stack):
    for row in stack:
        if needle.startswith(row):
            return True
    return False

def format_results(result):
    if result is None:
        return None

    if len(result) == 0:
        return None

    result = result[0].squeeze()
    result = softmax(result) # 1/(1 + np.exp(-result))

    out = {
        'naughty': 0.0,
        'nice': 0.0,
    }
    for i, label in enumerate(labels_bin):
        out[label] = result[i]

    return out


# ----------------------------------------------------

def main(arg_dir, arg_out, arg_sensitivity):
    naughty_images = [
        'textures/aminions/nude.tga',
        'textures/gvn/papanoelll.jpg',
        'textures/ged/chien.jpg',
        'textures/firma/blonde-girl-28.jpg',
        'textures/ghost-textures/tubgirl002.jpg',
        'textures/funy/apple_sweet_as.jpg',
        'textures/frag_misc/plakat2.tga',
        'textures/bbb/yuhu!.jpg',
        'textures/thd-life/d.jpg',
        'textures/thd-systems/s1.jpg',
        'textures/pornstar/vida.jpg',
        'textures/rush/lithiumpicnic_nude2.jpg',
        'textures/viral-danika/danika0507.jpg',
        'textures/csu2/boobs_17.jpg',
        'levelshots/4kabcorp-ok-ok.jpg',
    ]
    ok_suffixes = ['.jpg', '.jpeg', '.png', '.tga']
    notok_prefixes = ['models/players']
    notok_pk3s = [
        'pak0.pk3',
        'pak1.pk3',
        'pak2.pk3',
        'pak3.pk3',
        'pak4.pk3',
        'pak5.pk3',
        'pak6.pk3',
        'pak7.pk3',
        'pak8.pk3',
        'pak9.pk3',
        'zz-defrag_fix_mapscripts_190.pk3',
        'zz-defrag_fix_shaders_190.pk3',
        'zz-defrag_media_190.pk3',
        'zz-defrag_media_191.pk3',
        'zz-defrag_vm_191.pk3',

    ]
    out_path = pathlib.Path(arg_out)
    sess = rt.InferenceSession(model_path)
    input_name = sess.get_inputs()[0].name

    pk3_files = list(pathlib.Path(arg_dir).glob('*.pk3'))
    for pk3file in tqdm(pk3_files, desc='Overall progress'):

        if pk3file.name in notok_pk3s:
            continue

        try:
            with zipfile.ZipFile(str(pk3file)) as pk3:
                files = pk3.namelist()

                for filepath_str in tqdm(files, desc=pk3file.name, leave=False):
                    filepath = pathlib.Path(filepath_str)
                    destination = out_path / filepath

                    if destination.exists():
                        continue

                    # check for known naughty images
                    if filepath_str in naughty_images:
                        pathlib.Path(destination.parent).mkdir(parents=True, exist_ok=True)
                        pk3.extract(filepath_str, path=str(destination))
                        continue
                    
                    # check file suffix
                    if filepath.suffix not in ok_suffixes:
                        continue

                    # check file prefix
                    if check_prefix(filepath_str, notok_prefixes):
                        continue

                    try:
                        with pk3.open(filepath_str) as myfile:
                            image = Image.open(io.BytesIO(myfile.read()))

                            if image.size[0] < 100 and image.size[1] < 100:
                                continue

                            image = image.convert('RGB')
                            image_tensor = test_transforms(image)
                            image_tensor = image_tensor.unsqueeze_(0)

                            result = sess.run(None, {input_name: image_tensor.numpy()})
                            prob = format_results(result)

                            if arg_sensitivity == 0:
                                if prob['naughty'] > 0.15:
                                    pathlib.Path(destination.parent).mkdir(parents=True, exist_ok=True)
                                    image.save(str(destination), quality=99)
                            elif arg_sensitivity == 1:
                                if prob['naughty'] > prob['nice'] and prob['naughty'] < 0.75:
                                    pathlib.Path(destination.parent).mkdir(parents=True, exist_ok=True)
                                    image.save(str(destination), quality=99)
                            else:
                                if prob['naughty'] > 0.75:
                                    pathlib.Path(destination.parent).mkdir(parents=True, exist_ok=True)
                                    image.save(str(destination), quality=99)

                    except Exception as e:
                        print('ERROR', filepath, e)

        except Exception as e:
            print('ERROR:', str(pk3file), e)

# ----------------------------------------------------

if __name__ == "__main__":
    args = parser.parse_args()
    main(args.out, args.dir, args.sensitivity)