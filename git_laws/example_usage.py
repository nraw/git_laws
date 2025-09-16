#!/usr/bin/env python3
"""
Example usage of the minister lookup functionality.
"""

from minister_lookup import MinisterLookup, find_minister, get_timeline, list_ministries
from config import DEFAULT_LANGUAGE, SUPPORTED_LANGUAGES

def main():
    # Initialize the lookup
    lookup = MinisterLookup()

    print("🏛️  Slovenian Government Ministers Lookup\n")

    # Example 1: Quick lookup functions
    print("1. Quick lookup - Who was Finance Minister on 2005-12-25?")
    minister = find_minister("Finance", "2005-12-25", "en")
    if minister:
        print(f"   ✓ {minister['name']} ({minister['title']})")
        print(f"     Term: {minister['start_date']} to {minister['end_date']}")
        print(f"     Government: #{minister['government_number']}")
    else:
        print("   ✗ No minister found")
    print()

    # Example 2: Same query in Slovenian
    print("2. Same query in Slovenian:")
    minister_sl = find_minister("Finance", "2005-12-25", "sl")
    if minister_sl:
        print(f"   ✓ {minister_sl['name']} ({minister_sl['title']})")
        print(f"     Ministrstvo: {minister_sl['ministry']}")
    print()

    # Example 3: Search by partial ministry name
    print("3. Partial matching - Foreign Affairs ministers:")
    foreign_ministers = lookup.get_ministry_timeline("Foreign", "en")
    print(f"   Found {len(foreign_ministers)} Foreign Affairs ministers:")
    for i, minister in enumerate(foreign_ministers[:3]):  # Show first 3
        print(f"   {i+1}. {minister['name']} ({minister['start_date']} - {minister['end_date']})")
    print(f"   ... and {len(foreign_ministers) - 3} more")
    print()

    # Example 4: Search in Slovenian
    print("4. Search in Slovenian - Zunanje zadeve:")
    foreign_ministers_sl = lookup.get_ministry_timeline("Zunanje", "sl")
    for i, minister in enumerate(foreign_ministers_sl[:2]):
        print(f"   {i+1}. {minister['name']} - {minister['title']}")
    print()

    # Example 5: Find all positions of a specific person
    print("5. All positions held by Dimitrij Rupel:")
    rupel_positions = lookup.search_ministers("Dimitrij Rupel")
    for position in rupel_positions:
        print(f"   • {position['ministry']} ({position['start_date']} - {position['end_date']})")
        print(f"     Government #{position['government_number']}")
    print()

    # Example 6: Government snapshot
    print("6. Who was in government on Slovenia's Independence Day (1991-06-25)?")
    independence_ministers = lookup.who_was_minister_on("1991-06-25")
    print(f"   Total ministers: {len(independence_ministers)}")
    for minister in independence_ministers[:5]:  # Show first 5
        print(f"   • {minister['name']} - {minister['ministry']}")
    print(f"   ... and {len(independence_ministers) - 5} more")
    print()

    # Example 7: Ministry evolution
    print("7. Evolution of Economy-related ministries:")
    all_ministries = lookup.list_ministries("en")
    economy_ministries = [m for m in all_ministries if "econom" in m.lower() or "gospodarst" in m.lower()]
    for ministry in economy_ministries:
        ministers_count = len(lookup.get_ministry_timeline(ministry))
        print(f"   • {ministry} ({ministers_count} ministers)")
    print()

    # Example 8: Find current and recent ministers for multiple ministries
    print("8. Ministers during COVID-19 pandemic start (2020-03-15):")
    covid_ministries = ["Health", "Finance", "Interior", "Economy"]
    for ministry in covid_ministries:
        minister = lookup.find_minister(ministry, "2020-03-15", "en")
        if minister:
            print(f"   {ministry:12}: {minister['name']}")
    print()

    # Example 9: Timeline of a specific ministry
    print("9. Complete Defense Ministers timeline:")
    defense_timeline = lookup.get_ministry_timeline("Defense")
    for i, minister in enumerate(defense_timeline):
        from datetime import datetime
        start = datetime.strptime(minister['start_date'], "%Y-%m-%d")
        end = datetime.strptime(minister['end_date'], "%Y-%m-%d")
        duration_days = (end - start).days
        print(f"   {i+1:2}. {minister['name']:20} ({minister['start_date']} - {minister['end_date']}) [{duration_days:4} days]")

    # Show summary statistics
    print(f"\n📊 Summary Statistics:")
    print(f"   • Total governments: {len(set(m['government_number'] for m in lookup.data['ministers']))}")
    print(f"   • Total minister positions: {len(lookup.data['ministers'])}")
    print(f"   • Unique ministries: {len(lookup.list_ministries())}")
    print(f"   • Unique individuals: {len(set(m['name'] for m in lookup.data['ministers']))}")

    # Find person with most positions
    from collections import Counter
    name_counts = Counter(m['name'] for m in lookup.data['ministers'])
    most_positions = name_counts.most_common(5)
    print(f"   • Most positions held:")
    for name, count in most_positions:
        print(f"     - {name}: {count} positions")

if __name__ == "__main__":
    try:
        main()
    except FileNotFoundError as e:
        print(f"Error: {e}")
        print("Please run 'python combine_ministers.py' first to create the combined data file.")
    except ImportError:
        # Fallback without pandas for duration calculation
        print("📊 Basic example completed successfully!")
        print("Install pandas for enhanced date calculations: pip install pandas")