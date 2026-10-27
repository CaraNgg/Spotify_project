import pandas as pd

#most number of plays in one day
def loop_record(both_clean, person_a, person_b):
    real_plays = both_clean[both_clean["counted"]].copy()
    real_plays["date"] = real_plays["ts"].dt.date   # just the day, no time

    # plays per person, per day, per song
    daily = (
        real_plays.groupby(["person", "date", "track", "artist"])
        .size()
        .rename("plays")
        .reset_index()
    )

    result = {}
    for person in [person_a, person_b]:
        p = daily[daily["person"] == person]
        best = p.loc[p["plays"].idxmax()]   # the row with the most plays

        result[person] = {
            "track": best["track"],
            "artist": best["artist"],
            "date": best["date"],
            "plays": int(best["plays"]),
        }

    # who wins
    a, b = result[person_a]["plays"], result[person_b]["plays"]
    result["winner"] = person_a if a > b else person_b if b > a else "Tie"

    return result

#most number of plays of a song in one week
def obsession_record(both_clean, person_a, person_b):
    real_plays = both_clean[both_clean["counted"]].copy()

    # the Monday that starts each play's week
    day = real_plays["ts"].dt.tz_localize(None).dt.normalize()
    real_plays["week_start"] = day - pd.to_timedelta(day.dt.weekday, unit="D")

    # plays per person, per week, per song
    weekly = (
        real_plays.groupby(["person", "week_start", "track", "artist"])
        .size()
        .rename("plays")
        .reset_index()
    )

    result = {}
    for person in [person_a, person_b]:
        p = weekly[weekly["person"] == person]
        best = p.loc[p["plays"].idxmax()]

        result[person] = {
            "track": best["track"],
            "artist": best["artist"],
            "week_start": best["week_start"].date(),
            "week_end": (best["week_start"] + pd.Timedelta(days=6)).date(),
            "plays": int(best["plays"]),
        }

    a, b = result[person_a]["plays"], result[person_b]["plays"]
    result["winner"] = person_a if a > b else person_b if b > a else "Tie"

    return result

#longest streak(days) played of an artist
#and longest streak(days) played of a song
def longest_streak(real_plays, person, column):
    p = real_plays[real_plays["person"] == person].copy()
    p["date"] = p["ts"].dt.tz_localize(None).dt.normalize()

    # one row per (artist or song, day played)
    days = p[[column, "date"]].drop_duplicates().sort_values([column, "date"])

    # gap from the previous day, within the same artist/song
    gap = days.groupby(column)["date"].diff()

    # a new streak starts whenever the gap isn't exactly 1 day
    new_streak = gap != pd.Timedelta(days=1)
    days["streak_id"] = new_streak.cumsum()

    # length, start, and end of every streak
    streaks = days.groupby(["streak_id", column])["date"].agg(["count", "min", "max"]).reset_index()
    best = streaks.loc[streaks["count"].idxmax()]

    return {
        "name": best[column],
        "days": int(best["count"]),
        "start": best["min"].date(),
        "end": best["max"].date(),
    }

#longest artist and song phase (days)
def longest_phase(both_clean, person_a, person_b):
    real_plays = both_clean[both_clean["counted"]]

    result = {}
    for person in [person_a, person_b]:
        result[person] = {
            "artist": longest_streak(real_plays, person, "artist"),
            "song": longest_streak(real_plays, person, "track"),
        }

    a = result[person_a]["artist"]["days"]
    b = result[person_b]["artist"]["days"]
    result["winner"] = person_a if a > b else person_b if b > a else "Tie"
    return result


#songs that the other person hasnt rlly listened to that the other person loves
#songs that one person hella loves but the other has never listened to
#gives a list of 50? songs for each person
def steal_list(both_clean, giver, receiver, n=50, receiver_max=3, giver_min=10):
    real_plays = both_clean[both_clean["counted"]]

    plays = (
        real_plays.groupby(["track", "artist", "person"])
        .size()
        .unstack("person", fill_value=0)
    )
    plays = plays.reindex(columns=[giver, receiver], fill_value=0)

    # giver loves it, receiver has barely heard it
    candidates = plays[(plays[giver] >= giver_min) & (plays[receiver] < receiver_max)]

    return candidates.sort_values(giver, ascending=False).head(n)


#the song that has been played in the most number of months (basically what song is the most consistent throughout/have been played)
def ride_or_die(both_clean, person_a, person_b):
    real_plays = both_clean[both_clean["counted"]].copy()
    real_plays["month"] = real_plays["ts"].dt.strftime("%Y-%m")   # e.g. "2024-03"

    # for each person + song: how many different months, first/last month, total plays
    songs = (
        real_plays.groupby(["person", "track", "artist"])
        .agg(
            months=("month", "nunique"),
            first_month=("month", "min"),
            last_month=("month", "max"),
            plays=("month", "size"),
        )
        .reset_index()
    )

    result = {}
    for person in [person_a, person_b]:
        p = songs[songs["person"] == person]
        # most months first; if tied, more total plays wins
        best = p.sort_values(["months", "plays"], ascending=False).iloc[0]

        result[person] = {
            "track": best["track"],
            "artist": best["artist"],
            "months": int(best["months"]),
            "first_month": best["first_month"],
            "last_month": best["last_month"],
            "plays": int(best["plays"]),
        }

    return result


#most back to back to back to back to back plays haha
#IDK KINDA IFFY
def back_to_back_record(both_clean, person_a, person_b):
    real_plays = both_clean[both_clean["counted"]]

    result = {}
    for person in [person_a, person_b]:
        p = real_plays[real_plays["person"] == person].sort_values("ts").copy()

        # one label per song (track + artist, so same-named songs don't mix)
        p["song"] = p["track"] + " – " + p["artist"]

        # a new run starts whenever the song is different from the previous play
        new_run = p["song"] != p["song"].shift()
        p["run_id"] = new_run.cumsum()

        # length, song, start and end time of every run
        runs = p.groupby("run_id").agg(
            song=("song", "first"),
            track=("track", "first"),
            artist=("artist", "first"),
            plays=("song", "size"),
            start=("ts", "min"),
            end=("ts", "max"),
        )

        best = runs.loc[runs["plays"].idxmax()]
        result[person] = {
            "track": best["track"],
            "artist": best["artist"],
            "plays": int(best["plays"]),
            "start": best["start"],
            "end": best["end"],
        }

    a, b = result[person_a]["plays"], result[person_b]["plays"]
    result["winner"] = person_a if a > b else person_b if b > a else "Tie"
    return result


#a high ranking song on your yearly wrapped but havent been played in a while
def forgotten_favorite(both_clean, person_a, person_b, min_gap_days=365):
    real_plays = both_clean[both_clean["counted"]].copy()
    real_plays["year"] = real_plays["ts"].dt.year

    result = {}
    for person in [person_a, person_b]:
        p = real_plays[real_plays["person"] == person]
        end = p["ts"].max()   # end of this person's data

        # per song: total plays and last time played
        songs = p.groupby(["track", "artist"]).agg(
            plays=("ts", "size"),
            last_played=("ts", "max"),
        )

        # only songs not played in at least a year
        forgotten = songs[songs["last_played"] <= end - pd.Timedelta(days=min_gap_days)]

        if forgotten.empty:
            result[person] = None   # never abandons a song
            continue

        best = forgotten["plays"].idxmax()   # (track, artist) of the biggest forgotten song
        track, artist = best

        # its best year, and where it ranked that year
        yearly = p.groupby(["year", "track", "artist"]).size().rename("plays").reset_index()
        song_years = yearly[(yearly["track"] == track) & (yearly["artist"] == artist)]
        peak = song_years.loc[song_years["plays"].idxmax()]

        that_year = yearly[yearly["year"] == peak["year"]].sort_values("plays", ascending=False)
        rank = list(zip(that_year["track"], that_year["artist"])).index((track, artist)) + 1

        result[person] = {
            "track": track,
            "artist": artist,
            "total_plays": int(forgotten.loc[best, "plays"]),
            "peak_year": int(peak["year"]),
            "peak_year_plays": int(peak["plays"]),
            "peak_year_rank": rank,
            "last_played": forgotten.loc[best, "last_played"],
            "days_since": (end - forgotten.loc[best, "last_played"]).days,
        }

    return result