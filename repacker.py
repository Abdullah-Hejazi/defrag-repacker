from dotenv import load_dotenv
import paramiko
import os
import sys
import shutil
import mysql.connector

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

OUTPUT_SIZE_THRESHHOLD = 3

FILE_DATABASE = {
    'models': [],
    'textures': [],
    'scripts': [],
    'maps': [],
    'sound': []
}

repacks_index = {}

GAMETYPES = [
    'run',
    'team',
    'ctf',
    'freestyle',
    'fastcaps'
]

MAP_EXCEPTIONS = []

FINISHED_FILES = []

def init():
    global DATATYPES

    if len(sys.argv) > 1 and sys.argv[1] == '--no-download':
        print("Skipping download")
    else:
        download_data()

    for datatype in DATATYPES:
        if os.path.exists('stores/' + datatype + '.txt'):
            with open('stores/' + datatype + '.txt', 'r') as f:
                FILE_DATABASE[datatype] = f.read().splitlines()

    if os.path.exists('stores/finished.txt'):
        with open('stores/finished.txt', 'r') as f:
            FINISHED_FILES = f.read().splitlines()

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
                log('download', 'Downloading  ' + file)
                sftp.get(PK3_FOLDER + file, 'downloads/' + file)
                log('download', 'Finished  ' + file)
                print(' ')


    print("Finished downloading pk3 files")
    ssh.close()

def separate_files():
    maps = parse_sql2()

    for file in os.listdir('downloads'):
        if file in MAP_EXCEPTIONS:
            continue

        if file.endswith('.pk3') and os.path.getsize('downloads/' + file) > 0:
            mapname = file.replace('.pk3', '')

            if mapname in maps:
                if extract_file(file) == False:
                    continue

                extract_data(maps[mapname])
                log('separate', 'Finished  ' + file)
                print(' ')

                package_file(maps[mapname])
            else:
                log('separate', 'Error  ' + file + ' not found in export.sql')
                print(' ')

            if os.path.exists('downloads/temp'):
                shutil.rmtree('downloads/temp')

    for gametype in GAMETYPES:
        package_file(gametype, True)


def extract_file(file):
    log('separate', 'Extracting  ' + file)

    if file in FINISHED_FILES:
        log('separate', 'File already extracted  ' + file)
        print(' ')
        return False

    FINISHED_FILES.append(file)
    # write FINISHED_FILES to file
    with open('stores/finished.txt', 'a') as f:
        f.write(file + '\n')


    try:
        shutil.unpack_archive('downloads/' + file, 'downloads/temp', 'zip')
    except:
        log('separate', 'Error  with unpacking ' + file)
        print(' ')
        return False

    log('separate', 'Finished Extracting  ' + file)
    return True

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
                    if file.endswith('.' + extension) and file not in FILE_DATABASE[datatype]:
                        path = os.path.join(root, file).replace('\\', '/').replace('downloads/temp/', '')

                        FILE_DATABASE[datatype].append(path)

                        with open('stores/' + datatype + '.txt', 'a') as f:
                            f.write(path + '\n')

                        _output = 'output/' + gametype + '/' + datatype + '/' + path
                        _input = 'downloads/temp/' + path

                        os.makedirs(os.path.dirname(_output), exist_ok=True)
                        shutil.copy(_input, _output)

def package_file(file, finalRound=False):
    global OUTPUT_SIZE_THRESHHOLD
    global repacks_index

    if not os.path.exists('output/' + file):
        return

    for folder in os.listdir('output/' + file):
        size = get_file_size('output/' + file + '/' + folder)

        if finalRound or size > (OUTPUT_SIZE_THRESHHOLD * 1024 * 1024 * 1024):
            log('repack', 'Packaging  ' + file + '/' + folder)
            if folder not in repacks_index:
                repacks_index[folder] = 0

            repacks_index[folder] += 1

            zip_name = 'repack/' + file + '/' + file + '-' + folder + '-' + str(repacks_index[folder])
            shutil.make_archive(zip_name, 'zip', 'output/' + file + '/' + folder)

            shutil.rmtree('output/' + file + '/' + folder)

            log('repack', 'Finished Packaging  ' + file + '/' + folder)

def parse_sql():
    dbconnection = mysql.connector.connect(
        host=os.getenv('DB_HOST'),
        user=os.getenv('DB_USER'),
        passwd=os.getenv('DB_PASS'),
        database=os.getenv('DB_NAME')
    )

    dbcursor = dbconnection.cursor()

    dbcursor.execute("SELECT name,gametype FROM defrag_racing.maps_map ORDER BY date_added_ws DESC")

    dbresult = dbcursor.fetchall()

    result = {}

    for row in dbresult:
        result[row[0]] = row[1]

    return result

def parse_sql2():
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
        cleared_msg = msg
        f.write(cleared_msg + '\n')


if __name__ == "__main__":
    init()
