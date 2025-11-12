# Historical Voulgaris-Inspired Model

This document outlines a sophisticated analytical model for evaluating NBA player performance, inspired by the data-driven methodologies of professional gambler and analyst Haralabos Voulgaris. This model goes beyond simple averages by incorporating several contextual factors and historical data to provide a more nuanced and predictive assessment of a player's All-Around Score (AAS).

## Core Enhancements and Factors:

The model integrates the following factors to refine the calculation of a player's performance:

### 1. Long-Term Player Profile (3-Season Analysis)

*   **Reasoning:** To build a robust and reliable "prior belief" about a player's abilities, we need to analyze their performance over a significant period. A three-season sample size provides a strong baseline and helps to smooth out short-term fluctuations.
*   **Implementation:**
    *   The script will fetch game logs for the current season and the two previous seasons.
    *   A **Baseline AAS** will be calculated for each player over this entire period, serving as their long-term "player rating."
    *   The **Standard Deviation** of their AAS will also be calculated to measure their consistency and volatility.

### 2. Short-Term Trend Analysis

*   **Reasoning:** While a long-term baseline is crucial, a player's current form is also highly predictive of their immediate future performance. We need to identify if a player is on a hot streak, in a slump, or playing at their usual level.
*   **Implementation:**
    *   The model will calculate the player's **L10 (last 10 games), L30, and L50 AAS**.
    *   These short-term trends will be compared to the player's long-term Baseline AAS to identify significant deviations and performance trajectories.

### 3. Deepened Contextual Analysis (3-Season Data)

*   **Reasoning:** With three seasons of data, we can perform a much more robust analysis of how a player performs in different situations, leading to more reliable pattern recognition.
*   **Implementation:**
    *   **Opponent Quality:** The model will analyze a player's performance against different tiers of opponents (e.g., top 10 teams, bottom 10 teams) over the past three seasons.
    *   **Situational Performance:** The model will analyze a player's performance in specific situations, such as home vs. away games and on the second night of a back-to-back, over the entire three-season period.

### 4. Pace of Play Adjustment

*   **Reasoning:** A player's raw statistics can be inflated in high-possession, fast-paced games and deflated in slow-paced games. Normalizing for pace provides a more accurate measure of a player's per-possession efficiency.
*   **Implementation:**
    *   The "Pace" statistic for each game will be retrieved from the `nba_api`.
    *   Player statistics will be adjusted to a "per 100 possessions" basis before calculating the AAS, ensuring comparability across games with varying tempos.

### 5. Player Usage Rate Context

*   **Reasoning:** A player's usage rate indicates their role and opportunity within the offense. This context is crucial for interpreting their performance.
*   **Implementation:** The player's Usage Rate (USG%) for each game will be fetched and included in the output.

### 6. Back-to-Back Games Adjustment

*   **Reasoning:** Playing on consecutive nights often leads to increased player fatigue and can result in a dip in performance.
*   **Implementation:**
    *   The model will identify games that are part of a back-to-back set.
    *   A small, predefined negative adjustment will be applied to the AAS for the second game of a back-to-back.

## Output and Metrics:

The enhanced script will provide a comprehensive player profile that includes:

*   **Long-Term Player Rating:** Baseline AAS and consistency score over the past three seasons.
*   **Short-Term Performance Trends:** L10, L30, and L50 AAS compared to their baseline.
*   **Contextual Performance Profile:** A summary of how they perform against different types of opponents and in different situations.
*   **A Composite "Predictive AAS":** A final, single score that blends all of these factors to provide a more holistic and predictive measure of a player's expected performance.
*   Detailed individual game statistics for the last 10 games, including `MATCHUP`, `Team`, `Date`, `PTS`, `REB`, `AST`, `STL`, `BLK`, `TOV`, `FG3M`, and `USG%`.

This model aims to provide a robust and insightful evaluation of player performance, moving closer to the sophisticated analytical approaches used by top sports analysts.
