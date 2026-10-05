import zipfile
import pandas as pd


def load_history(zip_path, person):
    # Load all Audio JSON files from the zip
    zf = zipfile.ZipFile(zip_path)
    dfs = []
    for name in zf.namelist():
        if "Streaming_History_Audio" in name and name.endswith(".json"):
            dfs.append(pd.read_json(zf.open(name)))
    df = pd.concat(dfs, ignore_index=True)

    # Keep only music rows
    df = df[df["master_metadata_track_name"].notna()]

    # Keep and rename columns
    df = df[[
        "ts",
        "master_metadata_track_name",
        "master_metadata_album_artist_name",
        "master_metadata_album_album_name",
        "ms_played",
        "spotify_track_uri",
        "reason_start",
        "reason_end",
        "skipped",
        "shuffle",
    ]].rename(columns={
        "master_metadata_track_name": "track",
        "master_metadata_album_artist_name": "artist",
        "master_metadata_album_album_name": "album",
        "spotify_track_uri": "uri",
    }).copy()

    # Timestamps to Toronto time
    df["ts"] = pd.to_datetime(df["ts"], utc=True).dt.tz_convert("America/Toronto")

    # Helper columns
    df["counted"] = df["ms_played"] >= 30000
    df["person"] = person

    return df.sort_values("ts").reset_index(drop=True)


def steal_list(plays, giver, receiver, n=50, max_plays=5):
    # songs the receiver has played fewer than 5 times (includes 0 = never)
    candidates = plays[plays[receiver] < max_plays]
    # rank by how much the giver loves them, keep the top n
    return candidates.sort_values(giver, ascending=False).head(n)


def run(name_a, name_b):
    a = load_history("/a.zip", name_a)
    b = load_history("/b.zip", name_b)
    both = pd.concat([a, b], ignore_index=True)

    real_plays = both[both["counted"]]
    plays = (
        real_plays.groupby(["track", "artist", "person"])
        .size()
        .unstack("person", fill_value=0)
    )

    for_a = steal_list(plays, giver=name_b, receiver=name_a).reset_index()
    for_b = steal_list(plays, giver=name_a, receiver=name_b).reset_index()
    return for_a.to_html(index=False), for_b.to_html(index=False)