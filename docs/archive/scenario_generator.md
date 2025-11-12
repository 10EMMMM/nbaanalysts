# Sorare Scenario Generator CLI

Follow these steps to build a Sorare scenario JSON for any NBA player.

1. **Open a terminal in the project root.**
   ```bash
   cd /path/to/nbaanalysts
   ```
2. **(Optional) Activate your Python environment.** Make sure the environment has the repo dependencies installed.
3. **Inspect the available arguments.**
   ```bash
   python -m src.projections.scenario_generator --help
   ```
4. **Run the generator with the player and context you need.** Replace the placeholders below with the game-specific details you collected.
   ```bash
   python -m src.projections.scenario_generator \
     --player "LeBron James" \
     --team "Los Angeles Lakers" \
     --opponent "Golden State Warriors" \
     --primary-teammate "Anthony Davis" \
     --secondary-handler "D'Angelo Russell" \
     --bench-guard "Austin Reaves" \
     --value-wing "Rui Hachimura" \
     --lock-time "11:30 AM"
   ```
5. **Copy the JSON output.** The command writes 10 mutually exclusive scenarios to `stdout`; paste them wherever you build lineups or automation.
6. **Adjust for late news.** Re-run the command with updated inputs whenever injuries or rotations change.

> Tip: Any optional flag can be omitted if you do not need that context; the script falls back to neutral placeholders.
