# Dynasty Draft Lottery

This function will ask you for the 8 teams who need lottery odds, as well as their point totals. It will then order the teams by the points, and generate the final list.

## To Run on Linux of Mac
`make run-dynasty-lottery-odds` \
`make demo-dynasty-lottery-odds` \

The demo command uses dummy values just in case you want to see how it works.

## To Run on Windows
`python .\dynasty_draft_lottery.py` \

## Sample result
```
Rank  Team                               Points    Tickets   Odds (top pick)
------------------------------------------------------------------------------
1     team d                             1         35        35.0%
2     team e                             5         22        22.0%
3     team a                             15        15        15.0%
4     team h                             15        10        10.0%
5     team b                             16        7         7.0%
6     team c                             23        5         5.0%
7     team g                             23        4         4.0%
8     team f                             32        2         2.0%

=== DRAWING FULL DRAFT ORDER ===
Pick #    Team
----------------------------------------
1         team d
2         team a
3         team e
4         team c
5         team h
6         team g
7         team b
8         team f
```

