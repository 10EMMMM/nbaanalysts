## Sorare Basketball Game Data – Handy Queries

All examples hit `https://api.sorare.com/graphql`. You can run them in the Sorare GraphQL playground or via `curl`/CLI clients. Replace placeholders (`<YourJWT>`, `<YourAud>`, `<playerSlug>`, `<gameUUID>`, etc.) accordingly.

### 1. Latest Sorare Scores (playerGameScores)
```graphql
query RecentScores($slug: String!, $limit: Int!) {
  anyPlayer(slug: $slug) {
    __typename
    ... on NBAPlayer {
      displayName
      playerGameScores(last: $limit, lowCoverage: true) {
        __typename
        ... on BasketballPlayerGameScore {
          score
          projectedScore
          basketballGame {
            uuid
            date
            homeTeam { code name }
            awayTeam { code name }
            statusTyped
            scoresByQuarter { quarter score }
          }
        }
      }
    }
  }
}
```

### 2. Detailed Box-Score Stats (PlayerGameStatsBasketball)
```graphql
query GameStats($slug: String!, $limit: Int!) {
  anyPlayer(slug: $slug) {
    __typename
    ... on NBAPlayer {
      playerGameScores(last: $limit) {
        __typename
        ... on BasketballPlayerGameScore {
          basketballGame { uuid date }
          basketballPlayerGameStats {
            minsPlayed
            points
            rebounds
            assists
            steals
            blocks
            turnovers
            threePointsMade
            doubleDouble
            tripleDouble
          }
        }
      }
    }
  }
}
```

### 3. Game-Level Pace/Defensive Rating (Team stats)
```graphql
query GameContext($slug: String!, $limit: Int!) {
  anyPlayer(slug: $slug) {
    __typename
    ... on NBAPlayer {
      playerGameScores(last: $limit) {
        __typename
        ... on BasketballPlayerGameScore {
          basketballGame {
            uuid
            date
            homeTeam { code name }
            awayTeam { code name }
            homeStats { stats { name value } }
            awayStats { stats { name value } }
          }
        }
      }
    }
  }
}
```
*Note:* Sorare returns pace/defensive rating as stat entries (e.g., `name: "pace"`). Filter client-side for the fields you need.

### 4. All Player Game Stats via `anyGameStats`
```graphql
query AnyGameStats($slug: String!, $limit: Int!) {
  anyPlayer(slug: $slug) {
    __typename
    ... on NBAPlayer {
      anyGameStats(last: $limit, lowCoverage: true) {
        __typename
        ... on PlayerGameStatsBasketball {
          anyGame { id date }
          points
          rebounds
          assists
          steals
          blocks
          minsPlayed
          turnovers
          threePointsMade
        }
      }
    }
  }
}
```

### 5. Game schedule + status (GameOfBasketball)
```graphql
query GameByUuid($uuid: ID!) {
  anyGame(id: $uuid) {
    __typename
    ... on GameOfBasketball {
      date
      statusTyped
      homeTeam { code name }
      awayTeam { code name }
      homeScore
      awayScore
      scoresByQuarter { quarter score }
      playerGameScores {
        __typename
        ... on BasketballPlayerGameScore {
          basketballPlayer { displayName slug }
          score
          basketballPlayerGameStats { points rebounds assists }
        }
      }
    }
  }
}
```

### 6. Player Trends (average stats / projections)
```graphql
query PlayerAverages($slug: String!) {
  anyPlayer(slug: $slug) {
    __typename
    ... on NBAPlayer {
      displayName
      averageStats(limit: LAST_10, type: POINTS)
      averageStats(limit: LAST_10, type: ASSISTS)
      averageStats(limit: LAST_10, type: REBOUNDS)
      nextClassicFixtureProjectedScore
      nextClassicFixtureProjectedGrade { grade score }
    }
  }
}
```

### 7. Future games (schedule lookahead)
```graphql
query FutureGames($slug: String!) {
  anyPlayer(slug: $slug) {
    __typename
    ... on NBAPlayer {
      anyFutureGames(first: 5) {
        nodes {
          ... on GameOfBasketball {
            uuid
            date
            homeTeam { code name }
            awayTeam { code name }
            so5Fixture { slug name deadline }
          }
        }
      }
    }
  }
}
```

### 8. Leaderboards / So5 appearances (context)
```graphql
query LeaderboardContext($slug: String!, $fixture: String!) {
  anyPlayer(slug: $slug) {
    __typename
    ... on NBAPlayer {
      so5AverageLastScore(
        competitionSlug: "nba-classic"
        position: basketball_forward
        span: LAST_10
      ) {
        score
        totalAppearances
      }
      mySo5LeaderboardContendersForFixture(so5FixtureSlug: $fixture) {
        so5Leaderboard { slug name }
        projectedScore
      }
    }
  }
}
```

### Authentication notes
- For public queries you can omit `Authorization`, but most NBA stats are rate-limited and require JWT auth.
- To authenticate:
  1. Fetch salt via `https://api.sorare.com/api/v1/users/<email>`
  2. Hash password with bcrypt
  3. Run the `signIn` mutation requesting `jwtToken(aud: "<YourAud>")`
  4. Send `Authorization: Bearer <token>` and `JWT-AUD: <YourAud>` headers on requests.

### Rate limits
- Unauthenticated: 20 req/min
- Authenticated (JWT/OAuth): 60 req/min (NBA endpoints have their own 150/min cap)
- API key (on request): 600 req/min

Use these snippets as building blocks; extend them with more fields (e.g., `basketballPlayerGameStats.projected*`) based on what you need. The Sorare schema is self-describing, so you can query the playground docs to discover additional stats (advanced metrics, injuries, fixtures, etc.).
