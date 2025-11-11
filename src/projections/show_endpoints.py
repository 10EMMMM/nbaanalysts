
import nba_api.stats.endpoints
import inspect

def get_endpoints():
    """
    Gets a list of all endpoint classes in the nba_api.stats.endpoints module.
    """
    endpoints = []
    for name, obj in inspect.getmembers(nba_api.stats.endpoints):
        if inspect.isclass(obj):
            endpoints.append(name)
    return endpoints

if __name__ == "__main__":
    all_endpoints = get_endpoints()
    for endpoint in sorted(all_endpoints):
        print(endpoint)
