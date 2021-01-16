from __future__ import unicode_literals
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


def singledl(url, dldir=path):
    global url_base, ydl_opts

    id = urllib.parse.urlparse(url).query.split("=")[1]
    txt = session.get(url).text
    title = txt[txt.find('<title>') + 7: txt.find('</title>')]

    getdeliv = session.get(url_base + "/Panopto/Pages/Viewer/DeliveryInfo.aspx",
                           **{"data": {"deliveryId": id, "responseType": "json"}})

    if not getdeliv:
        print('Your cookie file is likely outdated or invalid')
        print(getdeliv)
        exit()

    delivery_info = json.loads(getdeliv.text)
    creator = delivery_info["Delivery"]["OwnerDisplayName"]
    write_title = "{}".format(title)
    stream = delivery_info["Delivery"]["Streams"]
    dl = stream[0]["StreamUrl"]
    print("Downloading:", write_title, "by", creator, "\nFrom:",dl)

    ydl_opts["outtmpl"] = "{}/{}.%(ext)s".format(dldir, write_title)

    with youtube_dl.YoutubeDL(ydl_opts) as ydl:
        ydl.download([dl])


def jsonadapter(endpoint, base, params=None, post=False, paramtype="params"):
    if params is None:
        params = dict()
    if post:
        request = session.post(base + endpoint, **{paramtype: params})
    else:
        request = session.get(base + endpoint, **{paramtype: params})
    return json.loads(request.text)


def interop(url):
    folders = jsonadapter("/Panopto/Api/Folders", url_base, {"parentId": "null", "folderSet": 1})
    id = urllib.parse.urlparse(url).fragment.split("=")[1]
    for folder in folders:
        if folder["Id"] == id:
            return folder


def folderdl(folder, path=path, parent=""):
    global ydl_opts

    params = {"queryParameters": {"folderID": folder["Id"]}}
    sessions = jsonadapter("/Panopto/Services/Data.svc/GetSessions", url_base, params, True, "json")["d"]["Results"]
    print("Found videos:")
    for session in sessions:
        print("\t -", session["SessionName"])

    print("Starting folder download...")

    for session in sessions:
        folder_name = str(session["FolderName"]).replace("/", "-").replace(":", " ")
        name = session["SessionName"].replace("/", "-")
        dl = session["IosVideoUrl"]
        dldir = r"{}/{}".format(path, "/".join([parent.replace("/", "-"), folder_name]))
        os.makedirs(dldir, exist_ok=True)
        if params != "":
            print("\nDownloading: {}/{}\n".format(parent, name))
        else:
            print("\nDownloading: {}\n".format(name))
        ydl_opts["outtmpl"] = "{}/{}.%(ext)s".format(dldir, name)

        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            ydl.download([dl])

    folders = jsonadapter("/Panopto/Api/Folders", url_base, {"parentId": folder["Id"], "folderSet": 1})
    for folder in folders:
        print("Found a nested folder:", folder)
        folderdl(folder, parent=folder["Parent"]["Name"])


if "folder" in url:
    folderdl(interop(url), path)
elif "Viewer.aspx" in url:
    singledl(url, path)
else:
    print("invalid url")
