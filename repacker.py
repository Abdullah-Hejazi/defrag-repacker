from dotenv import load_dotenv
import paramiko
import os
import sys

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
    maps = parse_sql()

def parse_sql():
    # read files from export.sql to lines array
    result = {}
    with open('export.sql', 'r') as f:
        lines = f.readlines()

    i = 0
    for line in lines:
        linesplit = line.split(' ')
        gametypesplit = linesplit[1:]

        mapname = linesplit[0]
        gametype = ''.join(gametypesplit).replace(' ', '').replace('\n', '')

        result[mapname] = gametype

    return result

    

def generate_pk3():
    print("generate pk3 files (sound, maps, ...etc) separate pk3")

def log(file, msg):
    print(msg)

    with open('logs/' + file + '.log', 'a') as f:
        cleared_msg = msg.replace('\x1b[6;30;42m', '').replace('\x1b[6;30;44m', '').replace('\x1b[0m', '')
        f.write(cleared_msg + '\n')

if __name__ == "__main__":
    init()