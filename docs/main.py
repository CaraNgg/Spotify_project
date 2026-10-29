import json
import pandas as pd
from spotify_loading import load_history, align_end_dates, filter_window
from songs_tab import individual_song_report, shared_song_report
from artists_tab import show_individual_artists_ranking, show_shared_artists_ranking, artist_report
from blend_funny_tab import loop_record, one_person_likes_other_doesnt_touch, ride_or_die, most_plays_after_twelve, top_shared_after_twelve, top_shared_season_songs

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

def get_game(name_a, name_b):
    questions = []

    # Q1: top played song in a day
    loop = loop_record(both_clean, name_a, name_b)
    cards = []
    for name in [name_a, name_b]:
        cards.append({
            "prompt": f"The song {name} listened to the most in one day:",
            "answer": f"{loop[name]['track']} by {loop[name]['artist']}",
            "detail": f"{loop[name]['plays']} plays on {loop[name]['date']}",
        })
    questions.append({"title": "Top played song in a day", "cards": cards})

    # Q2: artists unique to each other
    blind = one_person_likes_other_doesnt_touch(both_clean, name_a, name_b)
    cards = []
    for name, other in [(name_a, name_b), (name_b, name_a)]:
        x = blind[name]
        cards.append({
            "prompt": f"The artist {name} loves but {other} has never listened to:",
            "answer": x["artist"] if x else "None!",
            "detail": f"{name}'s #{x['rank']} artist · {x['hours']} hours" if x
                      else f"{other} has listened to every artist {name} loves",
        })
    questions.append({"title": "Artists unique to each other", "cards": cards})

    # Q3: the song played most consistently out of the months they were on spotify
    rideordie = ride_or_die(both_clean, name_a, name_b)
    cards = []
    for name in [name_a, name_b]:
        x = rideordie[name]
        cards.append({
            "prompt": f"The song {name} keeps coming back to:",
            "answer": f"{x['track']} by {x['artist']}",
            "detail": f"Played in {x['months']} of {x['active_months']} active months on Spotify",
        })
    questions.append({"title": "Most consistently played song", "cards": cards})

    # Q4: top songs played after midnight (individual + shared)
    after_twelve = most_plays_after_twelve(both_clean, name_a, name_b)
    cards = []

    # cards 1 and 2: each person's top 3
    for name in [name_a, name_b]:
        songs = after_twelve[name]
        lines = []
        for i, song in enumerate(songs, start=1):
            lines.append(f"{i}. {song['track']} by {song['artist']} ({song['plays']} plays)")

        cards.append({
            "prompt": f"{name}'s top three songs after midnight:",
            "answer": "<br>".join(lines) if lines else "No late-night listening!",
            "detail": "Played between 12am and 5am",
        })

    # card 3: your shared top 3
    shared = top_shared_after_twelve(both_clean, name_a, name_b)
    lines = []
    for i, song in enumerate(shared, start=1):
        lines.append(f"{i}. {song['track']} by {song['artist']} "
                     f"({name_a}: {song[name_a]} · {name_b}: {song[name_b]})")

    cards.append({
        "prompt": "Your top three shared songs after midnight:",
        "answer": "<br>".join(lines) if lines else "No shared late-night songs!",
        "detail": "Songs you've both played between 12am and 5am",
    })

    questions.append({"title": "After midnight", "cards": cards})

    # Q5: top shared season + top songs in it
    season = top_shared_season_songs(both_clean, name_a, name_b)
    s = season["season"]
    cards = []

    emojis = {"Spring": "🌸", "Summer": "☀️", "Fall": "🍂", "Winter": "❄️"}

    info = {
        "main": f"Your top season is: {s} {emojis[s]}",
        "detail": f"{season['shares'][name_a]:.0%} of {name_a}'s and "
                  f"{season['shares'][name_b]:.0%} of {name_b}'s listening happens in {s}",
    }

    # cards 1 and 2: each person's top songs that season
    for name in [name_a, name_b]:
        lines = []
        for i, song in enumerate(season[name], start=1):
            lines.append(f"{i}. {song['track']} by {song['artist']} ({song['plays']} plays)")

        cards.append({
            "prompt": f"{name}'s top songs in {s}:",
            "answer": "<br>".join(lines) if lines else "No songs found!",
            "detail": f"Most played during {s}",
        })

    # card 3: shared top songs that season
    lines = []
    for i, song in enumerate(season["shared"], start=1):
        lines.append(f"{i}. {song['track']} by {song['artist']} "
                     f"({name_a}: {song[name_a]} · {name_b}: {song[name_b]})")

    cards.append({
        "prompt": f"Your top shared songs in {s}:",
        "answer": "<br>".join(lines) if lines else "No shared songs this season!",
        "detail": f"Songs you've both played during {s}",
    })

    questions.append({"title": "Your season", "info": info, "cards": cards})






    return json.dumps(questions, default=str)