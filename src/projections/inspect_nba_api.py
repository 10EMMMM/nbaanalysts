import inspect
from nba_api.stats.endpoints import boxscoreusagev2, playerdashboardbyshootingsplits

print("BoxScoreUsageV2:")
print(inspect.signature(boxscoreusagev2.BoxScoreUsageV2.__init__))

print("\nPlayerDashboardByShootingSplits:")
print(inspect.signature(playerdashboardbyshootingsplits.PlayerDashboardByShootingSplits.__init__))
