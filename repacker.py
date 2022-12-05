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

def init():
    global DATATYPES
    #download_data()
    #db_connect()
    #generate_pk3()

def download_data():
    print("Downloading pk3 files")
    global START_AT

    ssh = paramiko.client.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
 
    ssh.connect(
        os.getenv('FTP_SERVER'),
        username=os.getenv('FTP_USER'),
        password=os.getenv('FTP_PASS')
    )

    start = START_AT == ""

    with ssh.open_sftp() as sftp:
        files = sftp.listdir(path='/maps/missing')
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


def db_connect():
    print("connect to database and separate the downloaded files")

def generate_pk3():
    print("generate pk3 files (sound, maps, ...etc) separate pk3")

def log(file, msg):
    print(msg)

    with open('logs/' + file + '.log', 'a') as f:
        cleared_msg = msg.replace('\x1b[6;30;42m', '').replace('\x1b[6;30;44m', '').replace('\x1b[0m', '')
        f.write(cleared_msg + '\n')

if __name__ == "__main__":
    init()