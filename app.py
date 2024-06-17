from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import eyed3
import random
import os

import aiohttp

app = Flask(__name__, template_folder='templates')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/download', methods=['POST'])
async def download():
    spotify_url = request.form.get('spotify_url')
    print(f"Received Spotify URL: {spotify_url}")

    track = spotify_url.split('open.spotify.com/track/')[1]
    if '?' in track:
        track = track.split('?')[0]

    spotify = Spotify()
    download_link, title, artist, album, cover = await spotify.scrape_song(track)
    await spotify.download_file(download_link, title, artist, album, cover)

    response_data = {
        'title': title,
        'artist': artist,
        'album': album,
        'cover': cover,
        'file_name': title + '.mp3'
    }

    return jsonify(response_data)

@app.route('/download_file', methods=['POST'])
def download_file():
    song_title = request.form.get('song_title')
    print(f"Received request to download file: {song_title}")
    file_path = f"Temp/{song_title}.mp3"
    print(f"File path: {file_path}")

    return send_file(file_path, as_attachment=True)
    

class Utils:

    def generate_random_resolution():
        width = random.randint(800, 1920)
        height = random.randint(1000, 1080)
        return width, height

class Spotify(object):
    def __init__(self):
        super(Spotify, self).__init__()

        self.playlist_tracks = []

    async def scrape_song(self, track_url):

        headers = {
            'authority': 'api.spotifydown.com',
            'accept': '*/*',
            'accept-language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'dnt': '1',
            'origin': 'https://spotifydown.com',
            'referer': 'https://spotifydown.com/',
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Google Chrome";v="122"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"macOS"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get('https://api.spotifydown.com/download/'+track_url, headers=headers, timeout=90) as response:
                response_json = await response.json()
                print(response_json)

                _id = response_json["metadata"]["id"]
                artist = response_json["metadata"]["artists"]
                title = response_json["metadata"]["title"]
                album = response_json["metadata"]["album"]
                cover = response_json["metadata"]["cover"]
                isrc = response_json["metadata"]["isrc"]
                release_date = response_json["metadata"]["releaseDate"]

                download_link = response_json["link"]

                return download_link, title, artist, album, cover

    async def download_file(self, url, title, artist, album, cover):
        running = True
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:

                    if running:
                        content = await response.read()

                        with open("Temp/"+title+".mp3", 'wb') as file:
                            file.write(content)

                            audiofile = eyed3.load("Temp/"+title+".mp3")

                            audiofile.tag.title = title
                            audiofile.tag.artist = artist
                            audiofile.tag.album = album

                            async with aiohttp.ClientSession() as session:
                                async with session.get(cover) as response:

                                    content = await response.read()
                            
                                    with open("Temp/"+title+".jpg", 'wb') as file:
                                        file.write(content)

                                    with open("Temp/"+title+".jpg", "rb") as image_file:
                                        image_data = image_file.read()
                                        audiofile.tag.images.set(3, image_data, "image/jpeg", u"Cover")

                                    audiofile.tag.save()
                                    os.remove("Temp/"+title+".jpg")

                        print(f" Downloaded: {title}")
                    else:
                        print(f" Failed: {title}")

        except Exception as e:
            print(f" An error occurred: {e}")

if __name__ == '__main__':
    app.run(debug=True)
