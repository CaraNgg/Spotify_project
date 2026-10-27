import json
import pandas as pd
from spotify_loading import load_history, align_end_dates
from songs_tab import individual_song_report, shared_song_report

both_clean = None #initial dataframe with nothing

#LOAD THOSE TWO ZIPS
def load_both(name_a, name_b):
    global both_clean
    a = load_history("/a.zip", name_a)
    b = load_history("/b.zip", name_b)
    both_clean = align_end_dates(pd.concat([a, b], ignore_index=True))

def get_songs(name_a, name_b):
    table_a, table_b = individual_song_report(both_clean, name_a, name_b)

    result = {
        name_a: table_a.reset_index().head(50).to_dict("records"),
        name_b: table_b.reset_index().head(50).to_dict("records"),
    }
    return json.dumps(result) #cannot read python, so turn into json so javascript can read