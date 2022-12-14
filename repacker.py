from dotenv import load_dotenv
import paramiko
import os
import sys
import shutil
import mysql.connector
import zipfile
import json

load_dotenv()

DATATYPES = {
    'models': ['.md3', '.mdc', '.mdr', '.mds', '.mdx', '.md5mesh', '.md5anim'],
    'textures': ['.tga', '.jpg', '.jpeg', '.png', '.dds', '.bmp'],
    'scripts': ['.shader', '.cfg', '.menu', '.arena', '.bot', '.defi', '.shaderx'],
    'maps': ['.bsp', '.arena'],
    'sound': ['.wav', '.ogg', '.mp3']
}

START_AT = ""
PK3_FOLDER = '/maps/pk3/'

OUTPUT_SIZE_THRESHHOLD = 1.5

FILE_DATABASE = {
    'run': {
        'models': [],
        'textures': [],
        'scripts': [],
        'maps': [],
        'sound': []
    },
    'team': {
        'models': [],
        'textures': [],
        'scripts': [],
        'maps': [],
        'sound': []
    },
    'ctf': {
        'models': [],
        'textures': [],
        'scripts': [],
        'maps': [],
        'sound': []
    },
    'freestyle': {
        'models': [],
        'textures': [],
        'scripts': [],
        'maps': [],
        'sound': []
    },
    'fastcaps': {
        'models': [],
        'textures': [],
        'scripts': [],
        'maps': [],
        'sound': []
    },
    'unknown': {
        'models': [],
        'textures': [],
        'scripts': [],
        'maps': [],
        'sound': []
    }
}

repacks_index = {}

GAMETYPES = [
    'run',
    'team',
    'ctf',
    'freestyle',
    'fastcaps',
    'unknown'
]

FINISHED_FILES = []

def init():
    global DATATYPES
    global FINISHED_FILES
    global FILE_DATABASE
    global repacks_index

    if len(sys.argv) > 1 and sys.argv[1] == '--no-download':
        print("Skipping download")
    else:
        download_data()

    for datatype in DATATYPES:
        if os.path.exists('stores/database.json'):
            with open('stores/database.json', 'r', encoding="utf-8") as f:
                FILE_DATABASE = json.load(f)

    if os.path.exists('stores/finished.txt'):
        with open('stores/finished.txt', 'r', encoding="utf-8") as f:
            FINISHED_FILES = f.read().splitlines()

    if os.path.exists('stores/repacks_index.json'):
        with open('stores/repacks_index.json', 'r', encoding="utf-8") as f:
            repacks_index = json.load(f)

    print("Starting Point:")
    print("Finished Files: " + str(len(FINISHED_FILES)))

    print("\n\n")

    separate_files()

def download_data():
    global START_AT
    global PK3_FOLDER
    global DATATYPES
    global FINISHED_FILES
    global FILE_DATABASE
    global repacks_index

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
    global DATATYPES
    global FINISHED_FILES
    global FILE_DATABASE
    global repacks_index

    maps = parse_sql3()

    for file in os.listdir('downloads'):
        if file.endswith('.pk3') and os.path.getsize('downloads/' + file) > 0:
            if not search_db(maps, 'pk3_file', file):
                log('separate', 'File doesnt exist in the database (skipping): ' + file)
                continue

            if extract_file(file) == False:
                if os.path.exists('downloads/temp'):
                    shutil.rmtree('downloads/temp')

                continue

            extract_data(search_db(maps, 'pk3_file', file)['gametype'])

            log('separate', 'Finished  ' + file)
            print(' ')

            if os.path.exists('downloads/temp'):
                shutil.rmtree('downloads/temp')

def extract_file(file):
    global DATATYPES
    global FINISHED_FILES
    global FILE_DATABASE
    global repacks_index

    if file in FINISHED_FILES:
        log('separate', 'File already extracted (skipping)  ' + file)
        print(' ')
        return False

    log('separate', 'Extracting  ' + file)

    FINISHED_FILES.append(file)

    with open('stores/finished.txt', 'a', encoding="utf-8") as f:
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
    global FINISHED_FILES
    global FILE_DATABASE
    global repacks_index

    for root, subdirs, files in os.walk('downloads/temp'):
        for file in files:
            path = os.path.join(root, file).replace('\\', '/').replace('downloads/temp/', '')
            for datatype in DATATYPES:
                if file.endswith(tuple(DATATYPES[datatype])) and path not in FILE_DATABASE[gametype][datatype]:

                    FILE_DATABASE[gametype][datatype].append(path)

                    with open('stores/database.json', 'w', encoding="utf-8") as f:
                        json.dump(FILE_DATABASE, f)

                    with open('stores/' + datatype + '.txt', 'a', encoding="utf-8") as f:
                        f.write(path + '\n')

                    repack(gametype, datatype, path)

def repack(gametype, datatype, path):
    global DATATYPES
    global FINISHED_FILES
    global FILE_DATABASE
    global repacks_index

    repack_index = 1
    if gametype + '-' + datatype in repacks_index:
        repack_index = repacks_index[gametype + '-' + datatype]
    else:
        repacks_index[gametype + '-' + datatype] = 1
        save_index()

    zipname = 'repack/' + gametype + '-' + datatype + '-' + str(repack_index) + '.pk3'
    append_zip(zipname, 'downloads/temp/' + path)

    if os.path.getsize(zipname) > (OUTPUT_SIZE_THRESHHOLD * 1024 * 1024 * 1024):
        repack_index += 1
        repacks_index[gametype + '-' + datatype] = repack_index
        save_index()

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

def parse_sql3():
    result = []
    with open('file3.sql', 'r') as f:
        lines = f.readlines()

    for line in lines:
        row = line.split('|')

        result.append({
            'mapname': row[1].strip(),
            'gametype': row[4].strip(),
            'pk3_file': row[2].strip().split('/')[-1],
            'pk3_file_size': int(row[3].strip()),
            'release_date': row[5].strip()
        })

    return result

def search_db(db, key, value):
    for row in db:
        if row[key] == value:
            return row

    return False

def log(file, msg):
    print(msg)

    with open('logs/' + file + '.log', 'a', encoding="utf-8") as f:
        cleared_msg = msg
        f.write(cleared_msg + '\n')

def save_index():
    with open('stores/repacks_index.json', 'w') as f:
        json.dump(repacks_index, f)

def append_zip(zip_name, file):
    if not os.path.exists(zip_name):
        with zipfile.ZipFile(zip_name, 'w', zipfile.ZIP_DEFLATED) as zip:
            zip.write(file, file.replace('downloads/temp', ''))
            return

    with zipfile.ZipFile(zip_name, 'a', zipfile.ZIP_DEFLATED) as zip:
        zip.write(file, file.replace('downloads/temp', ''))

if __name__ == "__main__":
    init()
