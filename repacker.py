from dotenv import load_dotenv
import paramiko
import os
import sys
import shutil

load_dotenv()

DATATYPES = {
    'models': ['md3', 'mdc', 'mdr', 'mds', 'mdx', 'md5mesh', 'md5anim'],
    'textures': ['tga', 'jpg', 'jpeg', 'png', 'dds', 'bmp'],
    'scripts': ['shader', 'cfg', 'menu', 'arena', 'bot', 'defi', 'shaderx'],
    'maps': ['bsp', 'arena'],
    'sound': ['wav', 'ogg', 'mp3']
}

START_AT = ""
PK3_FOLDER = '/maps/pk3/'

OUTPUT_SIZE_THRESHHOLD = 0

repacks_index = {}

GAMETYPES = [
    'run',
    'teamrun',
    'ctf',
    'freestyle',
    'fastcaps'
]

def init():
    global DATATYPES
    download_data()
    separate_files()


def download_data():
    global START_AT
    global PK3_FOLDER

    print("Downloading pk3 files")

    ssh = paramiko.client.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
 
    ssh.connect(
        os.getenv('FTP_SERVER'),
        username=os.getenv('FTP_USER'),
        password=os.getenv('FTP_PASS')
    )

    start = START_AT == ""

    with ssh.open_sftp() as sftp:
        files = sftp.listdir(path=PK3_FOLDER)
        files.sort()

        for file in files:
            if file == START_AT:
                start = True

            if not start:
                continue

            if file.endswith('.pk3') and file not in os.listdir('downloads'):
                log('download', '\x1b[6;30;44m Downloading \x1b[0m ' + file)
                sftp.get(PK3_FOLDER + file, 'downloads/' + file)
                log('download', '\x1b[6;30;42m Finished \x1b[0m ' + file)
                print(' ')


    print("Finished downloading pk3 files")
    ssh.close()

def separate_files():
    maps = parse_sql()

    for file in os.listdir('downloads'):
        if file.endswith('.pk3'):
            mapname = file.replace('.pk3', '')

            if mapname in maps:
                extract_file(file)
                extract_data(maps[mapname])
                log('separate', '\x1b[6;30;42m Finished \x1b[0m ' + file)

                package_file(maps[mapname])
            else:
                log('separate', '\x1b[6;30;41m Error \x1b[0m ' + file + ' not found in export.sql')
                print(' ')

            if os.path.exists('downloads/temp'):
                shutil.rmtree('downloads/temp')

def extract_file(file):
    log('separate', '\x1b[6;30;44m Extracting \x1b[0m ' + file)

    shutil.unpack_archive('downloads/' + file, 'downloads/temp', 'zip')

    log('separate', '\x1b[6;30;42m Finished Extracting \x1b[0m ' + file)
    print(' ')

def get_file_size(start_path = '.'):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(start_path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)

    return total_size

def extract_data(gametype):
    global DATATYPES

    for root, subdirs, files in os.walk('downloads/temp'):
        for file in files:
            for datatype in DATATYPES:
                for extension in DATATYPES[datatype]:
                    if file.endswith('.' + extension):
                        path = os.path.join(root, file).replace('downloads/temp/', '')
                        _output = 'output/' + gametype + '/' + datatype + '/' + path
                        _input = 'downloads/temp/' + path

                        os.makedirs(os.path.dirname(_output), exist_ok=True)
                        shutil.copy(_input, _output)

def package_file(file):
    global OUTPUT_SIZE_THRESHHOLD
    global repacks_index

    for folder in os.listdir('output/' + file):
        size = get_file_size('output/' + file + '/' + folder)

        if size > (OUTPUT_SIZE_THRESHHOLD * 1024 * 1024):
            log('repack', '\x1b[6;30;44m Packaging \x1b[0m ' + file + '/' + folder)
            if folder not in repacks_index:
                repacks_index[folder] = 0

            repacks_index[folder] += 1

            zip_name = 'repack/' + file + '/' + file + '-' + folder + '-' + str(repacks_index[folder])
            shutil.make_archive(zip_name, 'zip', 'output/' + file + '/' + folder)

            shutil.rmtree('output/' + file + '/' + folder)

            log('repack', '\x1b[6;30;42m Finished Packaging \x1b[0m ' + file + '/' + folder)

def parse_sql():
    # read files from export.sql to lines array
    result = {}
    with open('export.sql', 'r') as f:
        lines = f.readlines()

    for line in lines:
        linesplit = line.split(' ')
        gametypesplit = linesplit[1:]

        mapname = linesplit[0]
        gametype = ''.join(gametypesplit).replace(' ', '').replace('\n', '')

        result[mapname] = gametype

    return result

def log(file, msg):
    print(msg)

    with open('logs/' + file + '.log', 'a') as f:
        cleared_msg = msg.replace('\x1b[6;30;42m', '').replace('\x1b[6;30;44m', '').replace('\x1b[0m', '').replace('\x1b[6;30;41m', '')
        f.write(cleared_msg + '\n')


if __name__ == "__main__":
    init()