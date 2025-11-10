"""Scenario generation helper for Sorare lineup planning."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ScenarioTemplate:
    scenario_title: str
    trigger_conditions: str
    mechanism_of_change: str
    projection_minutes: str
    projection_floor: str
    projection_median: str
    projection_ceiling: str
    probability: int
    risk_flags: List[str]
    lineup_fit: str
    late_swap_note: str

    def render(self, context: Dict[str, str]) -> Dict[str, object]:
        mapping = {key: value for key, value in context.items()}
        rendered = {
            "scenario_title": self.scenario_title.format(**mapping),
            "trigger_conditions": self.trigger_conditions.format(**mapping),
            "mechanism_of_change": self.mechanism_of_change.format(**mapping),
            "projection_band": {
                "minutes": self.projection_minutes.format(**mapping),
                "sorare_points": {
                    "floor": self.projection_floor.format(**mapping),
                    "median": self.projection_median.format(**mapping),
                    "ceiling": self.projection_ceiling.format(**mapping),
                },
            },
            "probability": self.probability,
            "risk_flags": self.risk_flags,
            "lineup_fit": self.lineup_fit.format(**mapping),
            "late_swap_note": self.late_swap_note.format(**mapping),
        }
        return rendered


def _build_context(args: argparse.Namespace) -> Dict[str, str]:
    first_name = args.player.split()[0]
    opponent_short = args.opponent.split()[-1] if args.opponent else "Opponent"
    secondary_handler = args.secondary_handler or "the secondary creator"
    context = {
        "player": args.player,
        "first_name": first_name,
        "team": args.team,
        "opponent": args.opponent,
        "opponent_short": opponent_short,
        "lock_time": args.lock_time,
        "primary_teammate": args.primary_teammate or "the primary co-star",
        "secondary_handler": secondary_handler,
        "secondary_handler_title": secondary_handler.title(),
        "bench_guard": args.bench_guard or "bench guard options",
        "value_wing": args.value_wing or "value wing teammates",
    }
    return context


def _templates() -> List[ScenarioTemplate]:
    return [
        ScenarioTemplate(
            scenario_title="Steady Load vs {opponent_short} Schemes",
            trigger_conditions="All current {team} statuses hold and the game stays within two possessions most of the night.",
            mechanism_of_change="The coaching staff leans on {player} for his standard role in a competitive game, keeping usage balanced against {opponent} coverages.",
            projection_minutes="33-36",
            projection_floor="44-48",
            projection_median="50-54",
            projection_ceiling="58-62",
            probability=26,
            risk_flags=["none elevated"],
            lineup_fit="Cash/Safe anchor; pair with {primary_teammate} in Single-Entry for correlated assist chains; avoid stacking with {secondary_handler}-heavy builds.",
            late_swap_note="If unexpected {team} starter changes surface before the {lock_time} Asia/Manila lock, confirm {player} still active and projected for 34+ minutes; otherwise pivot to later-tip studs.",
        ),
        ScenarioTemplate(
            scenario_title="Lead Ballhandler Spike if Creator Scratched",
            trigger_conditions="{secondary_handler_title} downgraded or ruled out after shootaround.",
            mechanism_of_change="Without the secondary creator, {player} handles primary initiation, sees usage climb, and racks up more drives and pick-and-rolls, boosting scoring and assist volume.",
            projection_minutes="34-37",
            projection_floor="48-52",
            projection_median="54-58",
            projection_ceiling="62-68",
            probability=12,
            risk_flags=["minutes load", "late news volatility"],
            lineup_fit="Premium spend in Single-Entry/GPP; correlate with {primary_teammate} for assist upside; fade alongside {bench_guard} if they gain minutes.",
            late_swap_note="If creator news hits pre-lock, immediately upgrade {player} exposure and shift value toward guards replacing that usage; if unexpectedly active, revert to baseline projections.",
        ),
        ScenarioTemplate(
            scenario_title="Perimeter Heater at {opponent_short}",
            trigger_conditions="Early rhythm from deep (2+ made threes in first quarter) versus {opponent} coverages.",
            mechanism_of_change="Hot perimeter shooting keeps the ball in {first_name}'s hands, increasing true shooting and driving gravity; more transition chances off long rebounds raise efficiency without extra minutes.",
            projection_minutes="33-36",
            projection_floor="46-50",
            projection_median="56-60",
            projection_ceiling="66-74",
            probability=10,
            risk_flags=["shooting variance"],
            lineup_fit="High-upside GPP captain; mini-stack with shooters who benefit from collapsing defense; avoid pairing with {opponent} perimeter stoppers.",
            late_swap_note="Monitor pre-lock reports on {player}'s warmup workload; if limited or showing discomfort, pivot to balanced builds.",
        ),
        ScenarioTemplate(
            scenario_title="Point Forward Facilitation Night",
            trigger_conditions="{opponent} aggressively load the nail to deter drives while over-helping on {primary_teammate} post-ups.",
            mechanism_of_change="Usage tilts toward playmaking—assist rate spikes while scoring remains secondary—leading to strong Sorare output via assists, rebounds, and stocks even with moderate scoring.",
            projection_minutes="34-36",
            projection_floor="44-48",
            projection_median="52-56",
            projection_ceiling="60-66",
            probability=9,
            risk_flags=["assist volatility"],
            lineup_fit="Single-Entry builds with {primary_teammate} or lob threats; consider bring-backs with {opponent} stars for shootout correlation.",
            late_swap_note="If pre-lock news hints at a minutes restriction for {primary_teammate}, downgrade this facilitation path and reallocate toward scoring-heavy builds.",
        ),
        ScenarioTemplate(
            scenario_title="Switch Hunting Unlocks Glass & Stocks Spike",
            trigger_conditions="{opponent} lean into small-ball lineups and miss long jumpers early.",
            mechanism_of_change="{player} defends inside more, crashing boards and jumping passing lanes; elevated defensive stat opportunities and extra transition pushes inflate peripherals.",
            projection_minutes="33-35",
            projection_floor="46-50",
            projection_median="54-58",
            projection_ceiling="60-68",
            probability=8,
            risk_flags=["rebound variance"],
            lineup_fit="GPP leverage off {primary_teammate} chalk; pair with {value_wing} who benefit from transition.",
            late_swap_note="If a traditional {opponent} big is confirmed starting heavy minutes pre-lock, reduce exposure to this build and pivot toward balanced or facilitation scenarios.",
        ),
        ScenarioTemplate(
            scenario_title="Early Whistle Compression",
            trigger_conditions="{player} picks up two fouls before mid-first quarter or draws an offensive foul while attacking {opponent_short} frontcourt defenders.",
            mechanism_of_change="Coaches protect him with extended first-half bench stints and staggered fourth-quarter rest, trimming minutes and reducing rhythm, lowering counting stats.",
            projection_minutes="28-32",
            projection_floor="32-36",
            projection_median="38-42",
            projection_ceiling="46-50",
            probability=8,
            risk_flags=["foul risk", "minutes fragility"],
            lineup_fit="Avoid in Cash; hedge exposure in MME by pairing with mid-tier teammates who would absorb usage if {player} sits.",
            late_swap_note="If foul-prone refs (high personal foul rate) announced pre-lock, trim {player} shares and allocate to safer studs.",
        ),
        ScenarioTemplate(
            scenario_title="Defensive Assignment Drag",
            trigger_conditions="{team} task {player} with primary {opponent} star switches late, emphasizing defense over offense.",
            mechanism_of_change="Energy spent on containing perimeter actions reduces drive volume and shooting efficiency; usage dips while assists remain steady.",
            projection_minutes="32-35",
            projection_floor="36-40",
            projection_median="44-48",
            projection_ceiling="52-56",
            probability=7,
            risk_flags=["efficiency dip"],
            lineup_fit="Balanced or contrarian Single-Entry; correlate with {primary_teammate}, fade with {opponent} primary scorer stacks where {player} defers.",
            late_swap_note="If reports indicate {team} starting bigger wings to guard, downgrade this drag scenario and shift back to baseline projection.",
        ),
        ScenarioTemplate(
            scenario_title="{opponent_short} Run Away Blowout Trim",
            trigger_conditions="{opponent} hit an early barrage and {team} trail by 18+ entering fourth; coaches wave the white flag.",
            mechanism_of_change="{player} capped near 29 minutes with limited fourth-quarter run, depressing raw totals despite decent per-minute rates.",
            projection_minutes="27-30",
            projection_floor="30-34",
            projection_median="36-40",
            projection_ceiling="44-48",
            probability=7,
            risk_flags=["blowout", "minutes fragility"],
            lineup_fit="Fades in Cash; leverage GPP builds by correlating with bench teammates who might grab garbage time.",
            late_swap_note="Track live betting lines up to {lock_time}; if {opponent} favoritism balloons due to {team} rest news, cut {player} exposure quickly.",
        ),
        ScenarioTemplate(
            scenario_title="Overtime Showcase",
            trigger_conditions="Tight fourth quarter with neither team leading by more than five inside final two minutes; game extends into overtime.",
            mechanism_of_change="Extra five-plus minutes push {player} to ~40 minutes, allowing accumulation of additional counting stats across all categories.",
            projection_minutes="38-41",
            projection_floor="50-54",
            projection_median="58-62",
            projection_ceiling="66-72",
            probability=6,
            risk_flags=["minutes load"],
            lineup_fit="GPP leverage when stacking full game environments with {opponent} stars; consider pairing with other overtime beneficiaries.",
            late_swap_note="No pre-lock lever—just ensure flexibility for post-lock swaps if earlier games open overtime upside elsewhere.",
        ),
        ScenarioTemplate(
            scenario_title="Injury or Managed Minutes Cap",
            trigger_conditions="{player} reports increased soreness during warmups or {team} hint at keeping him near 28 minutes due to schedule congestion.",
            mechanism_of_change="Medical staff limits bursts and second stints; {player} emphasizes playmaking while deferring drives, causing sharp minute and usage drop.",
            projection_minutes="24-28",
            projection_floor="24-28",
            projection_median="30-34",
            projection_ceiling="38-42",
            probability=7,
            risk_flags=["injury", "minutes fragility"],
            lineup_fit="Strict fade in Cash; in GPPs, only roster if correlating with value teammates who would absorb the slack while hedging with {opponent} studs.",
            late_swap_note="If beat writers flag discomfort before the {lock_time} lock, pivot entirely off {player} and elevate {team} value plus opposing studs.",
        ),
    ]


def generate_scenarios(context: Dict[str, str]) -> List[Dict[str, object]]:
    return [template.render(context) for template in _templates()]


def parse_args(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate Sorare scenario JSON for a specified player."
    )
    parser.add_argument("--player", required=True, help="Full player name, e.g. 'LeBron James'.")
    parser.add_argument("--team", required=True, help="Player's NBA team name.")
    parser.add_argument("--opponent", required=True, help="Opponent team name.")
    parser.add_argument(
        "--lock-time",
        default="11:30 AM",
        help="Sorare lock time in Asia/Manila timezone (default: 11:30 AM).",
    )
    parser.add_argument(
        "--primary-teammate",
        help="Optional name of the primary teammate benefiting from correlations.",
    )
    parser.add_argument(
        "--secondary-handler",
        help="Optional name of the secondary creator or guard in the rotation.",
    )
    parser.add_argument(
        "--bench-guard",
        help="Optional description of bench guards who could gain minutes.",
    )
    parser.add_argument(
        "--value-wing",
        help="Optional description of value wings who thrive in transition.",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_args(argv)
    context = _build_context(args)
    scenarios = generate_scenarios(context)
    json.dump(scenarios, fp=sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":  # pragma: no cover - CLI entry point
    main(sys.argv[1:])
