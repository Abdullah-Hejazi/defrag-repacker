from dotenv import load_dotenv
import paramiko
import os
import sys
import shutil

load_dotenv()

DATATYPE = {
    'levelshots': ['jpg', 'tga', 'jpeg', 'png'],
    'models': ['md3', 'mdc', 'mdr', 'mds', 'mdx', 'md5mesh', 'md5anim'],
    'textures': ['tga', 'jpg', 'jpeg', 'png', 'dds', 'bmp'],
    'scripts': ['shader', 'cfg', 'menu', 'arena', 'bot'],
    'maps': ['bsp', 'arena'],
    'sound': ['wav', 'ogg', 'mp3']
}

START_AT = "z00mer_run2.pk3"
PK3_FOLDER = '/maps/missing'

GAMETYPES = [
    'run',
    'teamrun',
    'ctf',
    'freestyle',
    'fastcaps'
]

def init():
    global DATATYPES
    #download_data()
    separate_files()
    #generate_pk3()


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

            if file.endswith('.pk3'):
                log('download', '\x1b[6;30;44m Downloading \x1b[0m ' + file)
                sftp.get('/maps/missing/' + file, 'downloads/' + file)
                log('download', '\x1b[6;30;42m Finished \x1b[0m ' + file)
                print(' ')


    print("Finished downloading pk3 files")
    ssh.close()


def separate_files():
    global GAMETYPES
    maps = parse_sql()

    for file in os.listdir('downloads'):
        if file.endswith('.pk3'):
            mapname = file.replace('.pk3', '')

            if mapname in maps:
                extract_file(file)
                extract_data(maps[mapname])
                log('separate', '\x1b[6;30;42m Finished \x1b[0m ' + file)
            else:
                log('separate', '\x1b[6;30;41m Error \x1b[0m ' + file + ' not found in export.sql')
                print(' ')

            if os.path.exists('downloads/temp'):
                shutil.rmtree('downloads/temp')


def extract_file(file):
    log('separate', '\x1b[6;30;44m Extracting \x1b[0m ' + file)

    os.system('unzip downloads/' + file + ' -d downloads/temp')

    log('separate', '\x1b[6;30;42m Finished Extracting \x1b[0m ' + file)
    print(' ')


def extract_data(gametype):
    global DATATYPE
    global GAMETYPES

    for root, subdirs, files in os.walk('downloads/temp'):
        # print all files
        for file in files:
            # iterate datatype
            for datatype in DATATYPE:
                # iterate file extensions
                for extension in DATATYPE[datatype]:
                    if file.endswith('.' + extension):
                        # check if gametype is valid
                        if gametype in GAMETYPES:
                            # check if folder exists
                            if not os.path.exists('downloads/' + datatype + '/' + gametype):
                                os.makedirs('downloads/' + datatype + '/' + gametype)

                            # move file
                            shutil.move(os.path

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


def generate_pk3():
    global GAMETYPES
    print("generate pk3 files (sound, maps, ...etc) separate pk3")


def log(file, msg):
    print(msg)

    with open('logs/' + file + '.log', 'a') as f:
        cleared_msg = msg.replace('\x1b[6;30;42m', '').replace('\x1b[6;30;44m', '').replace('\x1b[0m', '').replace('\x1b[6;30;41m', '')
        f.write(cleared_msg + '\n')


if __name__ == "__main__":
    init()