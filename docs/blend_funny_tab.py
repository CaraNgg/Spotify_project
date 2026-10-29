import pandas as pd

#longest streak(days) played of an artist
#and longest streak(days) played of a song
#DONT ADD
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

#most back to back to back to back to back plays haha
#IDK KINDA IFFY
#DONT ADD
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

#DONT ADD
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

#Top song in each season! (INDIV)
def top_song_each_season(both_clean, person_a, person_b):
    real_plays = both_clean[both_clean["counted"]].copy()

    # turn each date into a number like 320 (March 20) or 1221 (December 21)
    month_day = real_plays["ts"].dt.month * 100 + real_plays["ts"].dt.day

    # each month belongs to one season
    seasons = {
        3: "Spring", 4: "Spring", 5: "Spring",  # Mar 1 – May 31
        6: "Summer", 7: "Summer", 8: "Summer",  # Jun 1 – Aug 31
        9: "Fall", 10: "Fall", 11: "Fall",  # Sep 1 – Nov 30
        12: "Winter", 1: "Winter", 2: "Winter",  # Dec 1 – Feb 28/29
    }
    real_plays["season"] = real_plays["ts"].dt.month.map(seasons)

    result = {}
    for person in [person_a, person_b]:
        p = real_plays[real_plays["person"] == person]
        result[person] = {}

        for season in ["Spring", "Summer", "Fall", "Winter"]:
            s = p[p["season"] == season]

            if s.empty:
                result[person][season] = None   # no plays that season
                continue

            counts = s.groupby(["track", "artist"]).size()
            track, artist = counts.idxmax()
            result[person][season] = {
                "track": track,
                "artist": artist,
                "plays": int(counts.max()),
            }

    return result


#======================================================================================================================

#songs that the other person hasnt rlly listened to that the other person loves
#songs that one person hella loves but the other has never listened to
#gives a list of 50? songs for each person
#ADD
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



#most consistent song through all the months they have actively listened on spotify
def ride_or_die(both_clean, person_a, person_b, min_hours=5):
    real_plays = both_clean[both_clean["counted"]].copy()
    real_plays["month"] = real_plays["ts"].dt.strftime("%Y-%m")   # e.g. "2024-03"

    result = {}
    for person in [person_a, person_b]:
        p = real_plays[real_plays["person"] == person]

        # this person's active months (at least min_hours of listening)
        monthly_hours = p.groupby("month")["ms_played"].sum() / 3_600_000
        active_months = monthly_hours[monthly_hours >= min_hours].index

        # only keep plays from active months
        p = p[p["month"].isin(active_months)]

        # for each song: how many different active months, first/last month, total plays
        songs = (
            p.groupby(["track", "artist"])
            .agg(
                months=("month", "nunique"),
                first_month=("month", "min"),
                last_month=("month", "max"),
                plays=("month", "size"),
            )
            .reset_index()
        )

        # most months first; if tied, more total plays wins
        best = songs.sort_values(["months", "plays"], ascending=False).iloc[0]

        result[person] = {
            "track": best["track"],
            "artist": best["artist"],
            "months": int(best["months"]),
            "active_months": len(active_months),   # the "out of Y"
            "first_month": best["first_month"],
            "last_month": best["last_month"],
            "plays": int(best["plays"]),
        }

    return result

#most number of plays in one day
#ADD
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
#ADD
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


#An artist they really like but ive never touched (SHARED)
#An artist they really like but the other has never touched (SHARED)
def one_person_likes_other_doesnt_touch(both_clean, person_a, person_b):
    real_plays = both_clean[both_clean["counted"]]

    # hours per artist per person (real plays only)
    hours = (
        real_plays.groupby(["artist", "person"])["ms_played"].sum()
        .unstack("person", fill_value=0)
        .reindex(columns=[person_a, person_b], fill_value=0) / 3_600_000
    )

    # number of plays per artist per person (ALL plays, so any play counts as "touched")
    any_plays = (
        both_clean.groupby(["artist", "person"]).size()
        .unstack("person", fill_value=0)
        .reindex(columns=[person_a, person_b], fill_value=0)
    )

    result = {}
    for lover, other in [(person_a, person_b), (person_b, person_a)]:
        # artists the other person has never played even once
        never_played = any_plays.index[any_plays[other] == 0]

        # this person's hours on those artists
        candidates = hours.loc[hours.index.intersection(never_played), lover]
        candidates = candidates[candidates > 0]

        if candidates.empty:
            result[lover] = None   # every artist they love, the other has touched
            continue

        artist = candidates.idxmax()
        rank = hours[lover].rank(ascending=False, method="min")[artist]

        result[lover] = {
            "artist": artist,
            "hours": round(float(candidates.max()), 1),
            "rank": int(rank),
        }

    return result

#What three songs does each person play the most after 12am? (INDIV)
def most_plays_after_twelve(both_clean, person_a, person_b, n=3):
    real_plays = both_clean[both_clean["counted"]]
    late = real_plays[real_plays["ts"].dt.hour < 5]   # 12:00am – 4:59am

    result = {}
    for person in [person_a, person_b]:
        p = late[late["person"] == person]

        if p.empty:
            result[person] = []   # empty list = no late-night listening
            continue

        top = (
            p.groupby(["track", "artist"]).size()
            .sort_values(ascending=False)
            .head(n)
        )

        result[person] = [
            {"track": track, "artist": artist, "plays": int(plays)}
            for (track, artist), plays in top.items()
        ]

    return result

#Whats the top three shared songs after 12am HAHA (SHARED)
def top_shared_after_twelve(both_clean, person_a, person_b, n=3):
    real_plays = both_clean[both_clean["counted"]]
    late = real_plays[real_plays["ts"].dt.hour < 5]

    counts = (
        late.groupby(["track", "artist", "person"]).size()
        .unstack("person", fill_value=0)
        .reindex(columns=[person_a, person_b], fill_value=0)
    )

    # only songs you've both played after midnight
    shared = counts[(counts[person_a] > 0) & (counts[person_b] > 0)].copy()

    if shared.empty:
        return []

    # rank by whoever played it less, then keep the top n
    shared["score"] = shared[[person_a, person_b]].min(axis=1)
    top = shared.sort_values("score", ascending=False).head(n)

    return [
        {"track": track, "artist": artist,
         person_a: int(row[person_a]), person_b: int(row[person_b])}
        for (track, artist), row in top.iterrows()
    ]

#Which season shares the most listening, and top 5 indiv and shared songs in the season (SHARED & INDIV)
#What season do you both listen to the most, and your top songs in it (SHARED)
def top_shared_season_songs(both_clean, person_a, person_b, n=5):
    real_plays = both_clean[both_clean["counted"]].copy()

    seasons = {
        3: "Spring", 4: "Spring", 5: "Spring",
        6: "Summer", 7: "Summer", 8: "Summer",
        9: "Fall", 10: "Fall", 11: "Fall",
        12: "Winter", 1: "Winter", 2: "Winter",
    }
    real_plays["season"] = real_plays["ts"].dt.month.map(seasons)

    # 1. each person's share of their listening in each season
    season_hours = (
        real_plays.groupby(["season", "person"])["ms_played"].sum()
        .unstack("person", fill_value=0)
        .reindex(columns=[person_a, person_b], fill_value=0)
    )
    shares = season_hours / season_hours.sum()

    # the season where both shares are highest
    best_season = shares.min(axis=1).idxmax()
    in_season = real_plays[real_plays["season"] == best_season]

    result = {
        "season": best_season,
        "shares": {person_a: round(float(shares.loc[best_season, person_a]), 3),
                   person_b: round(float(shares.loc[best_season, person_b]), 3)},
    }

    # 2. each person's top n songs in that season
    for person in [person_a, person_b]:
        top = (
            in_season[in_season["person"] == person]
            .groupby(["track", "artist"]).size()
            .sort_values(ascending=False)
            .head(n)
        )
        result[person] = [
            {"track": t, "artist": a, "plays": int(c)}
            for (t, a), c in top.items()
        ]

    # 3. your top n shared songs in that season
    counts = (
        in_season.groupby(["track", "artist", "person"]).size()
        .unstack("person", fill_value=0)
        .reindex(columns=[person_a, person_b], fill_value=0)
    )
    shared = counts[(counts[person_a] > 0) & (counts[person_b] > 0)].copy()
    shared["score"] = shared[[person_a, person_b]].min(axis=1)
    top_shared = shared.sort_values("score", ascending=False).head(n)

    result["shared"] = [
        {"track": t, "artist": a, person_a: int(row[person_a]), person_b: int(row[person_b])}
        for (t, a), row in top_shared.iterrows()
    ]

    return result

#Which artist took over a users life in one month(biggest percentage of listening was one artist) (INDIV)
#only count months with over 20 hours of listening
#Which artist took over a users life in one month (biggest % of listening was one artist) (INDIV)
def biggest_percent_of_month_artist(both_clean, person_a, person_b, min_month_hours=20):
    real_plays = both_clean[both_clean["counted"]].copy()
    real_plays["month"] = real_plays["ts"].dt.strftime("%Y-%m")   # e.g. "2024-03"

    result = {}
    for person in [person_a, person_b]:
        p = real_plays[real_plays["person"] == person]

        # hours per month per artist
        artist_hours = p.groupby(["month", "artist"])["ms_played"].sum() / 3_600_000

        # total hours per month (repeated for each artist row, so we can divide)
        month_total = artist_hours.groupby(level="month").transform("sum")

        # each artist's share of their month
        share = artist_hours / month_total

        # ignore months with too little listening
        share = share[month_total >= min_month_hours]

        # ignore the first and last month (probably partial)
        months = sorted(p["month"].unique())
        share = share[~share.index.get_level_values("month").isin([months[0], months[-1]])]

        if share.empty:
            result[person] = None
            continue

        month, artist = share.idxmax()

        result[person] = {
            "artist": artist,
            "month": month,
            "share": round(float(share.max()), 3),                 # e.g. 0.61 = 61%
            "artist_hours": round(float(artist_hours[(month, artist)]), 1),
            "month_hours": round(float(month_total[(month, artist)]), 1),
        }

    return result

#Shared obsession song (song that both people have played the most in one day) (SHARED)
#Shared obsession song (song that both people have played the most in one day) (SHARED)
def top_shared_song_one_day(both_clean, person_a, person_b):
    real_plays = both_clean[both_clean["counted"]].copy()
    real_plays["date"] = real_plays["ts"].dt.date

    # plays per person, per song, per day
    daily = (
        real_plays.groupby(["person", "track", "artist", "date"])
        .size()
        .rename("plays")
        .reset_index()
    )

    # each person's best day for each song
    best_days = daily.loc[daily.groupby(["person", "track", "artist"])["plays"].idxmax()]

    # one row per song, with each person's best plays and date side by side
    table = best_days.pivot(index=["track", "artist"], columns="person", values=["plays", "date"])
    table = table.dropna()   # keep only songs both people played

    if table.empty:
        return None

    # winner: the song whose smaller best-day count is highest
    score = table["plays"][[person_a, person_b]].min(axis=1).astype(int)
    track, artist = score.idxmax()

    return {
        "track": track,
        "artist": artist,
        person_a: {"plays": int(table.loc[(track, artist), ("plays", person_a)]),
                   "date": str(table.loc[(track, artist), ("date", person_a)])},
        person_b: {"plays": int(table.loc[(track, artist), ("plays", person_b)]),
                   "date": str(table.loc[(track, artist), ("date", person_b)])},
    }

#What hour you guys are most likely to be listening at the same time, and what is each persons top song (find the top shared hour, and then top song for that hour) (SHARED)
#What hour you guys are most likely to be listening at the same time,
#and what is each persons top song (SHARED)
def top_shared_hour_top_song(both_clean, person_a, person_b):
    real_plays = both_clean[both_clean["counted"]].copy()
    real_plays["hour"] = real_plays["ts"].dt.hour   # 0 = 12am, 23 = 11pm

    # listening time per hour, one column per person
    hours = (
        real_plays.groupby(["hour", "person"])["ms_played"].sum()
        .unstack("person", fill_value=0)
        .reindex(columns=[person_a, person_b], fill_value=0)
    )

    # each person's share of their own listening in each hour
    shares = hours / hours.sum()

    # the hour where both shares are highest
    best_hour = shares.min(axis=1).idxmax()

    # each person's top song in that hour
    in_hour = real_plays[real_plays["hour"] == best_hour]
    result = {"hour": int(best_hour)}

    for person in [person_a, person_b]:
        p = in_hour[in_hour["person"] == person]
        counts = p.groupby(["track", "artist"]).size()
        track, artist = counts.idxmax()

        result[person] = {
            "track": track,
            "artist": artist,
            "plays": int(counts.max()),
            "share": round(float(shares.loc[best_hour, person]), 3),   # e.g. 0.09 = 9%
        }

    return result


#The song each person goes out of their way to click on the most (INDIV)
def top_clicked_song(both_clean, person_a, person_b):
    # plays that started because the person tapped the song directly
    clicks = both_clean[both_clean["reason_start"] == "clickrow"]

    result = {}
    for person in [person_a, person_b]:
        p = clicks[clicks["person"] == person]

        if p.empty:
            result[person] = None   # no clicked songs found
            continue

        counts = p.groupby(["track", "artist"]).size()
        track, artist = counts.idxmax()

        result[person] = {
            "track": track,
            "artist": artist,
            "clicks": int(counts.max()),
        }

    return result

#What month of the year do you both listen to the most, and your top songs in it (SHARED)
def top_shared_month_songs(both_clean, person_a, person_b, n=5):
    real_plays = both_clean[both_clean["counted"]].copy()

    # label each play with its month name, across all years ("January", "February"...)
    real_plays["month_name"] = real_plays["ts"].dt.strftime("%B")

    # 1. each person's share of their listening in each month
    month_hours = (
        real_plays.groupby(["month_name", "person"])["ms_played"].sum()
        .unstack("person", fill_value=0)
        .reindex(columns=[person_a, person_b], fill_value=0)
    )
    shares = month_hours / month_hours.sum()

    # the month where both shares are highest
    best_month = shares.min(axis=1).idxmax()
    in_month = real_plays[real_plays["month_name"] == best_month]

    result = {
        "month": best_month,
        "shares": {person_a: round(float(shares.loc[best_month, person_a]), 3),
                   person_b: round(float(shares.loc[best_month, person_b]), 3)},
    }

    # 2. each person's top n songs in that month
    for person in [person_a, person_b]:
        top = (
            in_month[in_month["person"] == person]
            .groupby(["track", "artist"]).size()
            .sort_values(ascending=False)
            .head(n)
        )
        result[person] = [
            {"track": t, "artist": a, "plays": int(c)}
            for (t, a), c in top.items()
        ]

    # 3. your top n shared songs in that month
    counts = (
        in_month.groupby(["track", "artist", "person"]).size()
        .unstack("person", fill_value=0)
        .reindex(columns=[person_a, person_b], fill_value=0)
    )
    shared = counts[(counts[person_a] > 0) & (counts[person_b] > 0)].copy()
    shared["score"] = shared[[person_a, person_b]].min(axis=1)
    top_shared = shared.sort_values("score", ascending=False).head(n)

    result["shared"] = [
        {"track": t, "artist": a, person_a: int(row[person_a]), person_b: int(row[person_b])}
        for (t, a), row in top_shared.iterrows()
    ]

    return result
