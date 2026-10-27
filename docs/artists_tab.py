#the artists tab

#needed
#top songs for both people table
    #sorted by hours for each artists

#top shared songs for both people table
    #sorted by the lesser hours for each artist

#when clicking an artist
    #Who listened first? (each person's first song by this artist, with date)
    #Total hours of this artist in the timeframe, for both
    #Rank of this artist for each person (by hours)
    #Listening over time chart for both (ooh like rank of this artist for you overtime)
    #Side-by-side top songs from this artist for each person, with shared songs highlighted


import pandas as pd
import matplotlib.pyplot as plt

#makes a report of first date listened, first song listened, top 5 songs listened (for each person)
def artist_report(both_clean, artist_name, person_a, person_b):
    #make a dataframe where only the real plays (>30 seconds) are in it
    real_plays = both_clean[both_clean["counted"]]

    # case-insensitive match
    #hits is a dataframe of only the matching rows of the artist inputted
    hits = real_plays[real_plays["artist"].str.lower() == artist_name.strip().lower()]
    if hits.empty:
        return None   # nobody has listened to this artist

    #takes the first name of the "artist" column, so if someone inputes taylor swift, the actual artist name is Taylor Swift
    artist = hits["artist"].iloc[0]
    result = {"artist": artist}

    for person in [person_a, person_b]:
        person_all = real_plays[real_plays["person"] == person]
        p_hits = hits[hits["person"] == person].sort_values("ts")

        if p_hits.empty:
            result[person] = None   # this person never listened
            continue

        first = p_hits.iloc[0]
        top_songs = p_hits["track"].value_counts()

        # rank: where this artist sits in the person's list by hours
        artist_hours = person_all.groupby("artist")["ms_played"].sum().sort_values(ascending=False)
        rank = list(artist_hours.index).index(artist) + 1

        result[person] = {
            "first_date": first["ts"],
            "first_song": first["track"],
            "hours": p_hits["ms_played"].sum() / 3_600_000,
            "rank": rank,
            "top_songs": top_songs.head(5).to_dict(),   # {song: plays}
        }

    # comparisons, only if both listened
    a, b = result[person_a], result[person_b]
    if a and b:
        result["listened_first"] = person_a if a["first_date"] < b["first_date"] else person_b
        result["gap_days"] = abs((a["first_date"] - b["first_date"]).days)
        result["bigger_fan"] = person_a if a["hours"] > b["hours"] else person_b

    # listening over time chart: hours per month for each person
    timeline = (
            hits.groupby([hits["ts"].dt.strftime("%Y-%m"), "person"])["ms_played"].sum()
            .unstack("person", fill_value=0) / 3_600_000
    )
    # make sure both people have a column, even if one person has never listened
    timeline = timeline.reindex(columns=[person_a, person_b], fill_value=0)

    # fill in every month (from first play of this artist to the end of the data) with 0 for months nobody listened
    first_month = timeline.index.min()
    last_month = both_clean["ts"].max().strftime("%Y-%m")
    all_months = pd.period_range(first_month, last_month, freq="M").astype(str)
    timeline = timeline.reindex(index=all_months, fill_value=0)

    result["timeline"] = timeline.to_dict()

    return result


#make a dataframe with each persons individual artists
def show_individual_artists_ranking(both_clean, person_a, person_b):
    #real plays (>30 seconds)
    real_plays = both_clean[both_clean["counted"]]

    # hours per artist per person (one column per person)
    hours = (
            real_plays.groupby(["artist", "person"])["ms_played"].sum()
            .unstack("person", fill_value=0) / 3_600_000
    )

    table_A = pd.DataFrame({f"{person_a}_hours": hours[person_a]})
    table_B = pd.DataFrame({f"{person_b}_hours": hours[person_b]})

    # sort so the biggest artists overall are at the top
    table_A = table_A.sort_values(f"{person_a}_hours", ascending=False)
    table_B = table_B.sort_values(f"{person_b}_hours", ascending=False)

    return table_A, table_B

#make a dataframe with the shared artists
def show_shared_artists_ranking(both_clean, person_a, person_b):
    real_plays = both_clean[both_clean["counted"]]

    hours = (
            real_plays.groupby(["artist", "person"])["ms_played"].sum()
            .unstack("person", fill_value=0) / 3_600_000
    )

    table = pd.DataFrame({f"{person_a}_hours": hours[person_a], f"{person_b}_hours": hours[person_b]})

    # keep only shared artists (both people listened)
    table = table[(table[f"{person_a}_hours"] > 0) & (table[f"{person_b}_hours"] > 0)]

    # the smaller of the two hours for each artist
    table["shared_score"] = table[[f"{person_a}_hours", f"{person_b}_hours"]].min(axis=1)

    # sort by that, biggest first
    table = table.sort_values("shared_score", ascending=False)

    return table

