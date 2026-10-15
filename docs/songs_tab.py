#tab with all songs
#tab with all shared songs
#All: each person's top songs (plays/hours toggle)
#Shared only: songs you both play, sorted by the person who played less, with plays for both
from fontTools.ttLib.tables.B_A_S_E_ import table_B_A_S_E_

import pandas as pd
import matplotlib.pyplot as plt

def individual_song_report(both_clean, person_a, person_b):
    # real plays (>30 seconds)
    real_plays = both_clean[both_clean["counted"]]

    plays = (
        real_plays.groupby(["track", "artist", "person"])
        .size()
        .unstack("person", fill_value=0)
    )

    table_A = pd.DataFrame({f"{person_a}_plays": plays[person_a]})
    table_B = pd.DataFrame({f"{person_b}_plays": plays[person_b]})

    # keep only songs each person actually played
    table_A = table_A[table_A[f"{person_a}_plays"] > 0]
    table_B = table_B[table_B[f"{person_b}_plays"] > 0]

    table_A = table_A.sort_values(f"{person_a}_plays", ascending=False)
    table_B = table_B.sort_values(f"{person_b}_plays", ascending=False)

    return table_A, table_B


def shared_song_report(both_clean, person_a, person_b):
    real_plays = both_clean[both_clean["counted"]]
    plays = (
        real_plays.groupby(["track", "artist", "person"])
        .size()
        .unstack("person", fill_value=0)
    )

    table = pd.DataFrame({f"{person_a}_plays": plays[person_a], f"{person_b}_plays": plays[person_b]})

    #keep only songs that each person played
    table = table[(table[f"{person_a}_plays"] > 0) & (table[f"{person_b}_plays"] > 0)]

    #shared plays column
    #need two closing brackets cuz we are selecting more than one column
    table["shared plays"] = table[[f"{person_a}_plays", f"{person_b}_plays"]].min(axis=1)

    #sort by shared plays
    table = table.sort_values("shared plays", ascending=False)

    return table