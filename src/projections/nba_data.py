"""
Static NBA metadata used when Sorare endpoints omit team queries.
"""

NBA_CLUBS = [
    {"slug": "atlanta-hawks", "name": "Atlanta Hawks", "code": "ATL"},
    {"slug": "boston-celtics", "name": "Boston Celtics", "code": "BOS"},
    {"slug": "brooklyn-nets", "name": "Brooklyn Nets", "code": "BKN"},
    {"slug": "charlotte-hornets", "name": "Charlotte Hornets", "code": "CHA"},
    {"slug": "chicago-bulls", "name": "Chicago Bulls", "code": "CHI"},
    {"slug": "cleveland-cavaliers", "name": "Cleveland Cavaliers", "code": "CLE"},
    {"slug": "dallas-mavericks", "name": "Dallas Mavericks", "code": "DAL"},
    {"slug": "denver-nuggets", "name": "Denver Nuggets", "code": "DEN"},
    {"slug": "detroit-pistons", "name": "Detroit Pistons", "code": "DET"},
    {"slug": "golden-state-warriors", "name": "Golden State Warriors", "code": "GSW"},
    {"slug": "houston-rockets", "name": "Houston Rockets", "code": "HOU"},
    {"slug": "indiana-pacers", "name": "Indiana Pacers", "code": "IND"},
    {"slug": "los-angeles-clippers", "name": "Los Angeles Clippers", "code": "LAC"},
    {"slug": "los-angeles-lakers", "name": "Los Angeles Lakers", "code": "LAL"},
    {"slug": "memphis-grizzlies", "name": "Memphis Grizzlies", "code": "MEM"},
    {"slug": "miami-heat", "name": "Miami Heat", "code": "MIA"},
    {"slug": "milwaukee-bucks", "name": "Milwaukee Bucks", "code": "MIL"},
    {"slug": "minnesota-timberwolves", "name": "Minnesota Timberwolves", "code": "MIN"},
    {"slug": "new-orleans-pelicans", "name": "New Orleans Pelicans", "code": "NOP"},
    {"slug": "new-york-knicks", "name": "New York Knicks", "code": "NYK"},
    {"slug": "oklahoma-city-thunder", "name": "Oklahoma City Thunder", "code": "OKC"},
    {"slug": "orlando-magic", "name": "Orlando Magic", "code": "ORL"},
    {"slug": "philadelphia-76ers", "name": "Philadelphia 76ers", "code": "PHI"},
    {"slug": "phoenix-suns", "name": "Phoenix Suns", "code": "PHX"},
    {"slug": "portland-trail-blazers", "name": "Portland Trail Blazers", "code": "POR"},
    {"slug": "sacramento-kings", "name": "Sacramento Kings", "code": "SAC"},
    {"slug": "san-antonio-spurs", "name": "San Antonio Spurs", "code": "SAS"},
    {"slug": "toronto-raptors", "name": "Toronto Raptors", "code": "TOR"},
    {"slug": "utah-jazz", "name": "Utah Jazz", "code": "UTA"},
    {"slug": "washington-wizards", "name": "Washington Wizards", "code": "WAS"},
]

NBA_ROSTERS = {
    "atlanta-hawks": [
        {"slug": "trae-young", "displayName": "Trae Young"},
        {"slug": "dejounte-murray", "displayName": "Dejounte Murray"},
        {"slug": "clint-capela", "displayName": "Clint Capela"},
    ],
    "boston-celtics": [
        {"slug": "jayson-tatum", "displayName": "Jayson Tatum"},
        {"slug": "jaylen-brown", "displayName": "Jaylen Brown"},
        {"slug": "jrue-holiday", "displayName": "Jrue Holiday"},
    ],
    "brooklyn-nets": [
        {"slug": "mikal-bridges", "displayName": "Mikal Bridges"},
        {"slug": "cam-johnson", "displayName": "Cameron Johnson"},
        {"slug": "nic-claxton", "displayName": "Nic Claxton"},
    ],
    "charlotte-hornets": [
        {"slug": "lamelo-ball", "displayName": "LaMelo Ball"},
        {"slug": "terry-rozier", "displayName": "Terry Rozier"},
        {"slug": "gordon-hayward", "displayName": "Gordon Hayward"},
    ],
    "chicago-bulls": [
        {"slug": "zach-lavine", "displayName": "Zach LaVine"},
        {"slug": "demar-derozan", "displayName": "DeMar DeRozan"},
        {"slug": "nikola-vucevic", "displayName": "Nikola Vučević"},
    ],
    "cleveland-cavaliers": [
        {"slug": "donovan-mitchell", "displayName": "Donovan Mitchell"},
        {"slug": "darius-garland", "displayName": "Darius Garland"},
        {"slug": "evan-mobley", "displayName": "Evan Mobley"},
    ],
    "dallas-mavericks": [
        {"slug": "luka-doncic", "displayName": "Luka Dončić"},
        {"slug": "kyrie-irving", "displayName": "Kyrie Irving"},
        {"slug": "tim-hardaway-jr", "displayName": "Tim Hardaway Jr."},
    ],
    "denver-nuggets": [
        {"slug": "nikola-jokic", "displayName": "Nikola Jokić"},
        {"slug": "jamal-murray", "displayName": "Jamal Murray"},
        {"slug": "michael-porter-jr", "displayName": "Michael Porter Jr."},
    ],
    "detroit-pistons": [
        {"slug": "cade-cunningham", "displayName": "Cade Cunningham"},
        {"slug": "jaden-ivey", "displayName": "Jaden Ivey"},
        {"slug": "bojan-bogdanovic", "displayName": "Bojan Bogdanović"},
    ],
    "golden-state-warriors": [
        {"slug": "stephen-curry", "displayName": "Stephen Curry"},
        {"slug": "klay-thompson", "displayName": "Klay Thompson"},
        {"slug": "draymond-green", "displayName": "Draymond Green"},
    ],
    "houston-rockets": [
        {"slug": "jalen-green", "displayName": "Jalen Green"},
        {"slug": "fred-vanvleet", "displayName": "Fred VanVleet"},
        {"slug": "alperen-sengun", "displayName": "Alperen Şengün"},
    ],
    "indiana-pacers": [
        {"slug": "tyrese-haliburton", "displayName": "Tyrese Haliburton"},
        {"slug": "myles-turner", "displayName": "Myles Turner"},
        {"slug": "buddy-hield", "displayName": "Buddy Hield"},
    ],
    "los-angeles-clippers": [
        {"slug": "kawhi-leonard", "displayName": "Kawhi Leonard"},
        {"slug": "paul-george", "displayName": "Paul George"},
        {"slug": "james-harden", "displayName": "James Harden"},
    ],
    "los-angeles-lakers": [
        {"slug": "lebron-james", "displayName": "LeBron James"},
        {"slug": "anthony-davis", "displayName": "Anthony Davis"},
        {"slug": "dangelo-russell", "displayName": "D'Angelo Russell"},
    ],
    "memphis-grizzlies": [
        {"slug": "ja-morant", "displayName": "Ja Morant"},
        {"slug": "desmond-bane", "displayName": "Desmond Bane"},
        {"slug": "jaren-jackson-jr", "displayName": "Jaren Jackson Jr."},
    ],
    "miami-heat": [
        {"slug": "jimmy-butler", "displayName": "Jimmy Butler"},
        {"slug": "bam-adebayo", "displayName": "Bam Adebayo"},
        {"slug": "tyler-herro", "displayName": "Tyler Herro"},
    ],
    "milwaukee-bucks": [
        {"slug": "giannis-antetokounmpo", "displayName": "Giannis Antetokounmpo"},
        {"slug": "damian-lillard", "displayName": "Damian Lillard"},
        {"slug": "khris-middleton", "displayName": "Khris Middleton"},
    ],
    "minnesota-timberwolves": [
        {"slug": "anthony-edwards", "displayName": "Anthony Edwards"},
        {"slug": "karl-anthony-towns", "displayName": "Karl-Anthony Towns"},
        {"slug": "rudy-gobert", "displayName": "Rudy Gobert"},
    ],
    "new-orleans-pelicans": [
        {"slug": "zion-williamson", "displayName": "Zion Williamson"},
        {"slug": "brandon-ingram", "displayName": "Brandon Ingram"},
        {"slug": "cj-mccollum", "displayName": "CJ McCollum"},
    ],
    "new-york-knicks": [
        {"slug": "jalen-brunson", "displayName": "Jalen Brunson"},
        {"slug": "julius-randle", "displayName": "Julius Randle"},
        {"slug": "rj-barrett", "displayName": "RJ Barrett"},
    ],
    "oklahoma-city-thunder": [
        {"slug": "shai-gilgeous-alexander", "displayName": "Shai Gilgeous-Alexander"},
        {"slug": "chet-holmgren", "displayName": "Chet Holmgren"},
        {"slug": "josh-giddey", "displayName": "Josh Giddey"},
    ],
    "orlando-magic": [
        {"slug": "paolo-banchero", "displayName": "Paolo Banchero"},
        {"slug": "franz-wagner", "displayName": "Franz Wagner"},
        {"slug": "jalen-suggs", "displayName": "Jalen Suggs"},
    ],
    "philadelphia-76ers": [
        {"slug": "joel-embiid", "displayName": "Joel Embiid"},
        {"slug": "tyrese-maxey", "displayName": "Tyrese Maxey"},
        {"slug": "tobias-harris", "displayName": "Tobias Harris"},
    ],
    "phoenix-suns": [
        {"slug": "kevin-durant", "displayName": "Kevin Durant"},
        {"slug": "devin-booker", "displayName": "Devin Booker"},
        {"slug": "bradley-beal", "displayName": "Bradley Beal"},
    ],
    "portland-trail-blazers": [
        {"slug": "scoot-henderson", "displayName": "Scoot Henderson"},
        {"slug": "anfernee-simons", "displayName": "Anfernee Simons"},
        {"slug": "jerami-grant", "displayName": "Jerami Grant"},
    ],
    "sacramento-kings": [
        {"slug": "deaaron-fox", "displayName": "De'Aaron Fox"},
        {"slug": "domantas-sabonis", "displayName": "Domantas Sabonis"},
        {"slug": "keegan-murray", "displayName": "Keegan Murray"},
    ],
    "san-antonio-spurs": [
        {"slug": "victor-wembanyama", "displayName": "Victor Wembanyama"},
        {"slug": "devin-vassell", "displayName": "Devin Vassell"},
        {"slug": "keldon-johnson", "displayName": "Keldon Johnson"},
    ],
    "toronto-raptors": [
        {"slug": "scottie-barnes", "displayName": "Scottie Barnes"},
        {"slug": "pascal-siakam", "displayName": "Pascal Siakam"},
        {"slug": "jakob-poeltl", "displayName": "Jakob Pöltl"},
    ],
    "utah-jazz": [
        {"slug": "lauri-markkanen", "displayName": "Lauri Markkanen"},
        {"slug": "jordan-clarkson", "displayName": "Jordan Clarkson"},
        {"slug": "walker-kessler", "displayName": "Walker Kessler"},
    ],
    "washington-wizards": [
        {"slug": "kyle-kuzma", "displayName": "Kyle Kuzma"},
        {"slug": "jordan-poole", "displayName": "Jordan Poole"},
        {"slug": "tyus-jones", "displayName": "Tyus Jones"},
    ],
}
