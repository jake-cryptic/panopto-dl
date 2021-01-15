# panopto-dl

simple script that downloads videos/folders from a given url 


## FFmpeg

youtube-dl requires FFmpeg, you can get it here for windows: [Windows FFmpeg builds](https://www.gyan.dev/ffmpeg/builds/)

Place them in your PATH directory, this can be: /Appdata/Local/Programs/Python/Python39/Scripts/

## --cookies argument

If you're running Chrome, you can use this extension to generate a cookies.txt file: [Get cookies.txt](https://chrome.google.com/webstore/detail/get-cookiestxt/bgaddhkoddajcdgocldbbfleckgcbcid/related)

## Sample usage

`py panopto-dl.py --url https://university.cloud.panopto.eu/Panopto/Pages/Viewer.aspx?id=abce-dfef-anqw --path videos/ --cookies cloud.panopto.eu_cookies.txt