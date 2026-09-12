"""Test all new fetchers to verify they work."""
import sys
sys.path.insert(0, ".")

from fetchers import opportunitydesk, grants_gov, findaphd, linkedin_jobs

def test_fetcher(name, fetch_fn):
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"{'='*60}")
    try:
        items = fetch_fn()
        print(f"  Found: {len(items)} items")
        if items:
            for i, item in enumerate(items[:3]):
                print(f"  [{i+1}] {item.get('title', 'N/A')[:80]}")
                print(f"      URL: {item.get('url', 'N/A')[:80]}")
                print(f"      Country: {item.get('country', 'N/A')}")
                print(f"      Level: {item.get('level', 'N/A')}")
        else:
            print("  WARNING: No items returned!")
        return len(items)
    except Exception as e:
        print(f"  ERROR: {e}")
        return 0

if __name__ == "__main__":
    total = 0
    results = {}

    results["opportunitydesk"] = test_fetcher("Opportunity Desk RSS", opportunitydesk.fetch)
    results["grants-gov"] = test_fetcher("Grants.gov API", grants_gov.fetch)
    results["findaphd"] = test_fetcher("FindAPhD", findaphd.fetch)
    results["linkedin-jobs"] = test_fetcher("LinkedIn Jobs", linkedin_jobs.fetch)

    total = sum(results.values())
    print(f"\n{'='*60}")
    print(f"SUMMARY: {total} total items from {len(results)} sources")
    print(f"{'='*60}")
    for name, count in results.items():
        status = "OK" if count > 0 else "FAILED"
        print(f"  {name}: {count} items [{status}]")
