# Voulgaris‑Style NBA Betting Model — Implementation Checklist
_A build guide modeled on Haralabos “Bob” Voulgaris’s public descriptions of **Ewing** (core simulator), **Van Gundy** (minutes/lineups), and **Morey** (roster DB)._
  
Key sources:
- ESPN Magazine profile (Ewing, Van Gundy, Morey; possession‑level sim; player offense/defense values; matchup & aging; fouls → shooter FT%). citeturn5view0
- Washington Post (early edge on halftime totals; Ewing as a simulator). citeturn2view0
- Nate Silver, _The Signal and the Noise_ (edge thresholds ≈54% to beat vig; ~57% long‑run ceiling even for elite bettors). citeturn3view0

---

## 0) Architecture at a Glance
- **Ewing (Core Game Simulator)** → possession‑level sim; runs tens of thousands of trials; discards outliers; outputs projected score & confidence. Also models who gets fouled and uses **that player’s FT%**; maintains **offense/defense values per player**, adjusts by **matchups**, and includes **aging curves**. citeturn1view0
- **Van Gundy (Minutes/Lineups Model)** → forecasts **which lineups play** and **minutes per player**; feeds Ewing. citeturn5view0
- **Morey (Roster/Transactions DB)** → tracks **roster patterns**, trades, signings; feeds Van Gundy. citeturn5view0

---

## 1) Data Inputs — Checklist
- [ ] **Schedules & games** (dates, home/away, rest days, back‑to‑back flags).  
- [ ] **Rosters & eligibility** (active/inactive, injuries, new signings/trades). citeturn5view0  
- [ ] **Minutes history** (last ~30 games; rotation patterns by coach & game context). citeturn5view0  
- [ ] **Play‑by‑play & player game scores** (scoring events, fouls drawn, shot types; use for possession outcomes). citeturn1view0  
- [ ] **Player baselines**: offense/defense values; on/off splits; positional matchup tables (e.g., bigs vs elite centers). citeturn1view0  
- [ ] **Free‑throw data**: player FT%; fouls‑drawn rates to identify likely foulee per possession. citeturn1view0  
- [ ] **Aging curves** by position/size archetype. citeturn1view0  
- [ ] **Market lines** (open & close for spread/total) for calibration and edge measurement. citeturn1view0  

---

## 2) Feature Engineering — Checklist
- [ ] **Pace model**: possessions = f(minutes, lineups, opponent style, rest).  
- [ ] **Possession outcome model**: P(0/1/2/3 points, FTs, turnover, ORB) as a function of on‑court 10‑man lineup.  
- [ ] **Foul model**: who gets fouled on a given possession; use that **player’s FT%**. citeturn1view0  
- [ ] **Matchup adjustments**: per‑player offense/defense values vary by opponent and assignment. citeturn1view0  
- [ ] **Aging/trajectory adjustments** to player values over season & career horizon. citeturn1view0  
- [ ] **Late‑game heuristics**: end‑game fouling, timeouts, 3‑point rate changes, substitution tightening.  
- [ ] **Coach tendencies**: rotation length, pace preferences; integrates via Van Gundy. citeturn2view0

---

## 3) Van Gundy — Minutes & Lineups Model
**Goal:** Predict minutes per player and common lineup combinations for the target game.  
**Inputs:** Injuries/eligibility, last‑N minutes trend, matchup, rest/B2B, coach patterns, blowout risk.  
**Targets:** `minutes_i`, and lineup sequences (top K five‑man units with probabilities).  
**Approach:**  
- [ ] Train a gradient model / HMM / sequence model on historical rotations to estimate minutes & lineup usage.  
- [ ] Constrain outputs to roster/injury/position limits; normalize to team minutes.  
- [ ] Emit uncertainty bands (e.g., 5–95% for minutes_i) for Monte Carlo sampling in Ewing. citeturn5view0

---

## 4) Morey — Roster & Transactions DB
- [ ] Ingest transactions, G‑League call‑ups, two‑ways, trades, 10‑day contracts.  
- [ ] Maintain per‑coach rotation priors; update when personnel changes.  
- [ ] Expose a fast lookup for Van Gundy and Ewing (e.g., materialized views). citeturn5view0

---

## 5) Ewing — Minimal Possession Simulator (MVP Design)
**Loop (per simulation):**
1. [ ] **Sample minutes** per player and **lineup timeline** from Van Gundy (with uncertainty).  
2. [ ] **Advance time by possession**; determine unit on floor; draw outcome using possession model.  
3. [ ] Apply **foul model** to route FT attempts to the **actual fouled shooter’s FT%**. citeturn1view0  
4. [ ] Update score/rebound/turnover; handle substitutions according to timeline and fatigue/foul trouble.  
5. [ ] **Late‑game logic**: intentional fouls, pace/shot selection shifts, timeout effects, garbage‑time subs.  
6. [ ] Repeat to end of regulation (and OT).  

**Run size & post‑processing:** Simulate **tens of thousands** of games and **discard outliers**; compute mean & quantiles → projected spread/total with confidence. citeturn5view0

---

## 6) Calibration & Validation Loop
- [ ] **Backtest** vs **closing lines** (spread/total) over large samples; track MAE, calibration curves. citeturn1view0  
- [ ] **Market viability test:** only act when win‑probability/edge **exceeds vig** (≈ **54%+**). citeturn3view0  
- [ ] Expect elite long‑run hit rates around **~57%**; design risk & bankroll management accordingly. citeturn3view0  
- [ ] Monitor drift: if ROI narrows season‑to‑season, **increase sample size cautiously** and iterate features. citeturn1view0

---

## 7) Betting & Risk Management
- [ ] Compute EV per bet from sim distribution vs market price.  
- [ ] Use fractional Kelly or capped‑staking; enforce daily & season VAR drawdown limits.  
- [ ] Auto‑hedge or reduce exposure if live‑market contradicts pregame signals after material new info.

---

## 8) Engineering Checklist
- [ ] **Pipelines**: reproducible ETL for PBP, injuries, transactions, markets.  
- [ ] **Versioning**: feature & parameter snapshots for every simulation batch.  
- [ ] **Monitoring**: dashboards for edge distribution, calibration, ROI by market & team.  
- [ ] **Repro**: deterministic seeds; unit tests for event chains (fouls→FT shooter mapping, OT rules).  
- [ ] **Speed**: vectorize sim core; cache per‑lineup probabilities; parallelize trials.  

---

## 9) Acceptance Criteria
- [ ] Out‑of‑sample MAE on totals/spreads beats naive baselines and matches **closing line** skill. citeturn1view0  
- [ ] Probability forecasts pass calibration (Brier / reliability).  
- [ ] Live/halftime modules add incremental edge beyond pregame (historically a Voulgaris strength). citeturn2view0

---

## References
- ESPN Magazine profile detailing **Ewing/Van Gundy/Morey**, possession sim, fouls→shooter FT%, player offense/defense, matchup/aging; sim scale and outlier handling. citeturn5view0  
- Washington Post on early **halftime‑totals** edge and Ewing as simulator. citeturn2view0  
- Nate Silver excerpt on **edge thresholds (≈54%)** and practical **~57%** hit‑rate ceiling. citeturn3view0
