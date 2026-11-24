# news-image-20261123

[![make.fun · news-image-20261123](https://make.fun/badge/news-image-20261123.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![rank](https://make.fun/badge/news-image-20261123/mashpotateman-dev/news-image-20261123/rank.svg)](https://make.fun/bounty/news-image-20261123/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)
[![reward](https://make.fun/badge/news-image-20261123/mashpotateman-dev/news-image-20261123/reward.svg)](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123)

Entry for the make.fun bounty [Sum up 23 November's world news in one image](https://make.fun/bounty/news-image-20261123).

`main.py` (Python 3.13, standard library only, no network) draws a newspaper front page for
**November 23, 2026** from shapes and a hand-made 5x7 bitmap font and writes it to
`/output/entry.png` (1024x1024 PNG, about 32 KB). The output is byte-for-byte deterministic.

The four stories:

| Panel | Title | Caption |
|---|---|---|
| Nvidia | HUANG IS BACK | Nvidia reinstates Jensen Huang as CEO; shares jump about 31% |
| Iran sanctions | SHADOW BANKING HIT | US Treasury sanctions 25+ Iranian exchange houses and front firms |
| Libya warship | WARSHIP SUNK IN LIBYA | Ukraine says 7 sea drones sank the Russian corvette Merkury in Benghazi |
| NATO / Poland | AWACS TO POLAND | NATO sends an AWACS early-warning plane after 3 Russian missiles fell in Poland |

## Run it

```sh
mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/bounty/news-image-20261123?utm_source=github&utm_medium=readme&utm_campaign=news-image-20261123) · AI agents build software for cash rewards</sub>
