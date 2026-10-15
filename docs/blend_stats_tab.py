import pandas as pd

#most balanced artist (closest shared hours together)
#only consider artists that both actually listen to, not like an artist both people have listened to one song of
def most_balanced_artist(both_clean, person_a, person_b, top_n=20):
    real_plays = both_clean[both_clean["counted"]]

    hours = (
        real_plays.groupby(["artist", "person"])["ms_played"].sum()
        .unstack("person", fill_value=0) / 3_600_000
    )
    a, b = hours[person_a], hours[person_b]

    table = pd.DataFrame({f"{person_a}_hours": a, f"{person_b}_hours": b})

    # only shared artists
    table = table[(a > 0) & (b > 0)]

    # keep the top shared artists (by the smaller of the two hours)
    table["shared_hours"] = table[[f"{person_a}_hours", f"{person_b}_hours"]].min(axis=1)
    table = table.sort_values("shared_hours", ascending=False).head(top_n)

    # balance score: smaller / bigger (1.0 = perfectly even)
    table["balance"] = table["shared_hours"] / table[[f"{person_a}_hours", f"{person_b}_hours"]].max(axis=1)

    best = table["balance"].idxmax()   # the artist with the highest balance score

    return {
        "artist": best,
        person_a: table.loc[best, f"{person_a}_hours"],
        person_b: table.loc[best, f"{person_b}_hours"],
        "balance": table.loc[best, "balance"],
    }

#how many percent of caras listening match rubys artists, vv
def shared_taste_percent(both_clean, person_a, person_b, min_hours=1):
    real_plays = both_clean[both_clean["counted"]]
    hours = (
        real_plays.groupby(["artist", "person"])["ms_played"].sum()
        .unstack("person", fill_value=0) / 3_600_000
    )
    a, b = hours[person_a], hours[person_b]

    # % of each person's hours spent on artists the other has at least min_hours on
    a_shared = a[b >= min_hours].sum() / a.sum()
    b_shared = b[a >= min_hours].sum() / b.sum()

    return {person_a: a_shared, person_b: b_shared, "min_hours": min_hours}


#for the top 10 shared artists, what percentage of yalls top 5 songs match?
def top_songs_overlap(both_clean, person_a, person_b, n_artists=20, n_songs=5):
    real_plays = both_clean[both_clean["counted"]]

    # top shared artists (sorted by the person who listened less)
    hours = (
        real_plays.groupby(["artist", "person"])["ms_played"].sum()
        .unstack("person", fill_value=0)
    )

    shared = hours[(hours[person_a] > 0) & (hours[person_b] > 0)]
    top_artists = shared.min(axis=1).sort_values(ascending=False).head(n_artists).index

    per_artist = {}
    for artist in top_artists:
        plays = real_plays[real_plays["artist"] == artist]

        # each person's top 5 songs for this artist, sorted by most played
        top_a = list(plays[plays["person"] == person_a]["track"].value_counts().head(n_songs).index)
        top_b = list(plays[plays["person"] == person_b]["track"].value_counts().head(n_songs).index)

        # songs in both top lists (kept in person_a's order)
        shared_songs = [song for song in top_a if song in top_b]
        out_of = min(len(top_a), len(top_b))

        per_artist[artist] = {
            "matches": len(shared_songs),
            "out_of": out_of,
            "overlap": len(shared_songs) / out_of,
            "shared_songs": shared_songs,
            f"{person_a}_top": top_a,
            f"{person_b}_top": top_b,
        }

    # overall score: average overlap across artists
    score = sum(info["overlap"] for info in per_artist.values()) / len(per_artist)

    # the two extremes
    most_in_sync = max(per_artist, key=lambda artist: per_artist[artist]["overlap"])
    most_different = min(per_artist, key=lambda artist: per_artist[artist]["overlap"])

    return {
        "score": score,
        "per_artist": per_artist,
        "most_in_sync": most_in_sync,
        "most_different": most_different,
    }

#how yall discover music
def discovery_style(both_clean, person_a, person_b):
    all_plays = both_clean.sort_values("ts")
    real_plays = both_clean[both_clean["counted"]]

    # total hours per person per artist (to rank the examples)
    hours = (
            real_plays.groupby(["person", "artist"])["ms_played"].sum() / 3_600_000
    ).rename("hours").reset_index()

    # each person's top 100 artists by hours
    real = (
        hours.sort_values("hours", ascending=False)
        .groupby("person")
        .head(100)[["person", "artist"]]
    )

    # first play of every artist (including short plays), only real discoveries
    firsts = all_plays.drop_duplicates(subset=["person", "artist"], keep="first")
    firsts = firsts.merge(real, on=["person", "artist"])
    firsts = firsts.merge(hours, on=["person", "artist"]).copy()

    # group the reason codes into plain categories
    def how_found(reason):
        if reason in ["clickrow", "playbtn"]:
            return "You went looking"
        elif reason in ["trackdone", "fwdbtn"]:
            return "It came to you"
        else:
            return "Other"

    firsts["how"] = firsts["reason_start"].apply(how_found)

    result = {}
    for person in [person_a, person_b]:
        p = firsts[firsts["person"] == person]

        looking = p[p["how"] == "You went looking"].sort_values("hours", ascending=False)
        came = p[p["how"] == "It came to you"].sort_values("hours", ascending=False)

        result[person] = {
            "artists_found": len(p),
            "how": p["how"].value_counts(normalize=True).to_dict(),
            "shuffle_on": p["shuffle"].mean(),
            "top_looked_for": list(zip(looking["artist"].head(5), looking["hours"].head(5))),
            "top_came_to_you": list(zip(came["artist"].head(5), came["hours"].head(5))),
        }
    return result