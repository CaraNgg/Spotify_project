import json
import pandas as pd
from spotify_loading import load_history, align_end_dates, filter_window
from songs_tab import individual_song_report, shared_song_report
from artists_tab import show_individual_artists_ranking, show_shared_artists_ranking, artist_report

both_clean = None #initial dataframe with nothing

#LOAD THOSE TWO ZIPS
def load_both(name_a, name_b):
    global both_clean
    a = load_history("/a.zip", name_a)
    b = load_history("/b.zip", name_b)
    both_clean = align_end_dates(pd.concat([a, b], ignore_index=True))

def get_songs(name_a, name_b, window="all"):
    windowed_data = filter_window(both_clean, window)
    table_a, table_b = individual_song_report(windowed_data, name_a, name_b)

    result = {
        name_a: table_a.reset_index().head(50).to_dict("records"),
        name_b: table_b.reset_index().head(50).to_dict("records"),
    }
    return json.dumps(result) #cannot read python, so turn into json so javascript can read

def get_shared_songs(name_a, name_b, window="all"):
    windowed_data = filter_window(both_clean, window)
    table = shared_song_report(windowed_data, name_a, name_b)

    result = table.reset_index().head(50).to_dict("records")
    return json.dumps(result)

def get_artists(name_a, name_b, window="all"):
    windowed_data = filter_window(both_clean, window)
    table_a, table_b = show_individual_artists_ranking(windowed_data, name_a, name_b)

    result = {
        name_a: table_a.reset_index().head(50).to_dict("records"),
        name_b: table_b.reset_index().head(50).to_dict("records"),
    }
    return json.dumps(result)  # cannot read python, so turn into json so javascript can read

def get_shared_artists(name_a, name_b, window="all"):
    windowed_data = filter_window(both_clean, window)
    table = show_shared_artists_ranking(windowed_data, name_a, name_b)
    result = table.reset_index().head(50).to_dict("records")
    return json.dumps(result)  # cannot read python, so turn into json so javascript can read

def get_artist_report(name_a, name_b, artist_name):
    result = artist_report(both_clean, artist_name, name_a, name_b)
    return json.dumps(result, default=str)

def get_all_artists():
    real_plays = both_clean[both_clean["counted"]]                    # 1. only real plays (30+ sec)

    totals = real_plays.groupby("artist")["ms_played"].sum()          # 2. total time per artist, both people combined
    totals = totals.sort_values(ascending=False)                      # 3. most-listened first

    artist_names = list(totals.index)                                 # 4. just the names, as a list
    return json.dumps(artist_names)