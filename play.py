import scrapetube


try:
    print("scrapping youtube..")
    videos = scrapetube.get_channel(
        channel_id="UCiCttfv2sjW7qjq7DD_Me2A",
        limit=5,
        content_type="videos",
    )
    for video in videos:
        print("video detected")
        print(video["videoId"], video["title"])
except Exception as e:
    print(e)
