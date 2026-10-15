#loading the shit
#holds the functions that every tab needs, usually loading the data


import zipfile
import pandas as pd

def load_history(zip_path, person):
    # Load all Audio JSOimport zipfile
    # import pandas as pdN files from the zip
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

#align data to the persons data who was saved the earliest
def align_end_dates(both):
    # the earlier of the two people's last play
    end = both.groupby("person")["ts"].max().min()
    # cut everyone's data off at that date
    return both[both["ts"] <= end].copy()

#choose the window u want (30d, 6month, 12month, year)
def filter_window(both, window="all", year=None):
    if window == "all":
        return both

    if window == "year":
        return both[both["ts"].dt.year == year]

    end = both["ts"].max()
    starts = {
        "30d": end - pd.Timedelta(days=30),
        "6m": end - pd.DateOffset(months=6),
        "12m": end - pd.DateOffset(months=12),
    }
    return both[both["ts"] > starts[window]]