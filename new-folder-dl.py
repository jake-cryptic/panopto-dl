import youtube_dl
import urllib.parse
import requests
import json
import os
import argparse
import sys


parser = argparse.ArgumentParser(description='downloads videos from panopto')

parser.add_argument('--cookies', metavar='cookies', type=str, help='path to a netscape cookie file')
parser.add_argument("--url", metavar="url", type=str, help="url to download from")
parser.add_argument("--path", metavar="path", type=str, help="path to download videos to", default=os.getcwd())

args = parser.parse_args()
url = args.url
path = args.path
if len(sys.argv) == 1:
    parser.print_help(sys.stderr)
    sys.exit(1)

url_base = "https://{}".format(urllib.parse.urlparse(url).netloc)
ydl_opts = {
    'format': 'bestaudio/best',
    'quiet': True
}


def parsecookies(path):
    with open(path) as f:
        cookies = f.readlines()
        for i in cookies:
            if ".ASPXAUTH" in i.split():
                return i.split()[6]


session = requests.session()
session.cookies = requests.utils.cookiejar_from_dict({".ASPXAUTH": parsecookies(args.cookies)})


def jsonadapter(endpoint, base, params=None, post=False, paramtype="params"):
    if params is None:
        params = dict()
    if post:
        request = session.post(base + endpoint, **{paramtype: params})
    else:
        request = session.get(base + endpoint, **{paramtype: params})
    return json.loads(request.text)


def check_folder_exists(folder_id: str) -> None:
    folders = jsonadapter("/Panopto/Api/Folders", url_base, {"parentId": "null", "folderSet": 1})

    for folder in folders:
        print(f'Found [{folder["Id"]}] -> {folder["Name"]}')
        if folder["Id"] == folder_id:
            return folder
    
    print('Error! I could not find that FolderID, check it is in the list above!')
    exit(1)


def make_file_name_safe(name):
    return str(name).replace("/", "-").replace(":", " ").replace('?', '')


file_dl_list = {}


def folder_query(folder):
    file_dl_list = []

    file_dl_list = file_dl_list + get_sessions_for_folder(folder)

    folders = jsonadapter("/Panopto/Api/Folders", url_base, {"parentId": folder, "folderSet": 1})
    for folder in folders:
        print("Found a nested folder:", folder)
        file_dl_list = file_dl_list + get_sessions_for_folder(folder['Id'])

    print(file_dl_list)
    do_folder_dl(file_dl_list)


def get_sessions_for_folder(folder):
    print(f'get_sessions_for_folder({folder})')
    sessions_list = []
    params = {
        "queryParameters": {
            "folderID": folder
        }
    }

    sessions = jsonadapter("/Panopto/Services/Data.svc/GetSessions", url_base, params, True, "json")["d"]["Results"]

    print("Found videos:")
    print(sessions)
    for s in sessions:
        print("\t -", folder, s["SessionName"])
        sessions_list.append({
            'f': folder,
            'folderName': s["FolderName"],
            'sessionName': s["SessionName"],
            'videoUrl': s["IosVideoUrl"]
        })

    return sessions_list


def do_folder_dl(big_list):
    global ydl_opts

    for file in big_list:
        print(f'\t-Downloading: {file}\n')
        folder_name = make_file_name_safe(file['folderName'])
        name = make_file_name_safe(file['sessionName'])
        dldir = f'{path}/{folder_name}/{name}'
        print(dldir)
        os.makedirs(dldir, exist_ok=True)
        ydl_opts["outtmpl"] = "{}/{}.%(ext)s".format(dldir, name)

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([file['videoUrl']])


folder_query(urllib.parse.urlparse(url).fragment.split("=")[1])
