# Slovenian Government Ministers Lookup

A comprehensive system for querying Slovenian government minister data from 1990-2022, with bilingual (English/Slovenian) support.

## Files Overview

1. **`combine_ministers.py`** - Script to combine all individual government JSON files into a single queryable dataset
2. **`minister_lookup.py`** - Main utility module with the `MinisterLookup` class and convenience functions
3. **`example_usage.py`** - Comprehensive examples demonstrating all functionality
4. **`data/ministers_combined.json`** - Combined dataset (created by running combine_ministers.py)

## Quick Start

### 1. Combine the data files
```bash
python combine_ministers.py
```

### 2. Basic usage
```python
from minister_lookup import find_minister, get_timeline

# Who was Finance Minister on a specific date?
minister = find_minister("Finance", "2015-06-15")
print(f"{minister['name']} was Finance Minister")

# Get complete timeline of Defense Ministers
defense_ministers = get_timeline("Defense")
for minister in defense_ministers:
    print(f"{minister['name']} ({minister['start_date']} - {minister['end_date']})")
```

### 3. Advanced usage with the MinisterLookup class
```python
from minister_lookup import MinisterLookup

lookup = MinisterLookup()

# Search by person name
positions = lookup.search_ministers("Janez Janša")

# Get all ministers from a specific government
gov8_ministers = lookup.get_government_ministers(8)

# Who was in office on a specific date?
ministers_2010 = lookup.who_was_minister_on("2010-01-01")

# Bilingual queries
minister_en = lookup.find_minister("Health", "2020-06-01", "en")
minister_sl = lookup.find_minister("Zdravje", "2020-06-01", "sl")
```

## Key Features

### ✨ **Flexible Ministry Matching**
- Partial name matching: "Finance", "Economic", "Defense" all work
- Bilingual support: Search in English or Slovenian
- Case-insensitive matching

### 🌐 **Bilingual Support**
- All data available in English and Slovenian
- Specify language with `language="en"` or `language="sl"`
- Ministry names, titles, and terms localized

### 🔍 **Multiple Query Methods**
- **By Ministry + Date**: `find_minister("Finance", "2015-06-15")`
- **By Person**: `search_ministers("Dimitrij Rupel")`
- **By Government**: `get_government_ministers(8)`
- **By Date**: `who_was_minister_on("2010-01-01")`
- **Timeline**: `get_ministry_timeline("Defense")`

### 📊 **Rich Data**
- 203 minister positions across 14 governments (1990-2022)
- 46 unique ministries, 149 unique individuals
- Complete terms, transitions, predecessors, termination reasons
- Government context and metadata

## API Reference

### Main Functions

#### `find_minister(ministry, date, language="en")`
Find the minister for a specific ministry on a given date.
- **ministry**: Ministry name (English or Slovenian, partial matches work)
- **date**: Date in "YYYY-MM-DD" format
- **language**: Output language ("en" or "sl")
- **Returns**: Dict with minister info or None

#### `get_timeline(ministry, language="en")`
Get chronological timeline of all ministers for a ministry.
- **Returns**: List of ministers sorted by start date

#### `list_ministries(language="en")`
Get list of all unique ministry names.
- **Returns**: Sorted list of ministry names

### MinisterLookup Class Methods

#### `search_ministers(name, language="en")`
Search for ministers by name (partial matching).

#### `get_government_ministers(government_number, language="en")`
Get all ministers from a specific government (1-14).

#### `who_was_minister_on(date, language="en")`
Get all ministers who were in office on a specific date.

## Data Structure

Each minister record contains:
```json
{
  "name": "Dr. Dimitrij Rupel",
  "ministry": {
    "en": "Foreign Affairs",
    "sl": "Zunanje zadeve"
  },
  "title": {
    "en": "Minister of Foreign Affairs",
    "sl": "Minister za zunanje zadeve"
  },
  "ministry_code": "MZZ",
  "start_date": "2000-11-30",
  "end_date": "2002-12-19",
  "government_number": 6,
  "termination_reason": {
    "en": "replaced",
    "sl": "zamenjan"
  },
  "predecessor": "Dr. Boris Frlec"
}
```

## Examples

### Find COVID-19 Health Ministers
```python
lookup = MinisterLookup()

# Start of pandemic
march_2020 = lookup.find_minister("Health", "2020-03-15")
print(f"March 2020: {march_2020['name']}")

# Later in pandemic
jan_2021 = lookup.find_minister("Health", "2021-01-15")
print(f"January 2021: {jan_2021['name']}")
```

### Most Active Politicians
```python
from collections import Counter

lookup = MinisterLookup()
name_counts = Counter(m['name'] for m in lookup.data['ministers'])
most_active = name_counts.most_common(5)

for name, positions in most_active:
    print(f"{name}: {positions} ministerial positions")
```

### Ministry Evolution
```python
# Find all economy-related ministries
all_ministries = lookup.list_ministries()
economy_ministries = [m for m in all_ministries if "econom" in m.lower()]

for ministry in economy_ministries:
    timeline = lookup.get_ministry_timeline(ministry)
    print(f"{ministry}: {len(timeline)} ministers")
```

## Statistics

- **Total Governments**: 14 (1990-2022)
- **Total Minister Positions**: 203
- **Unique Ministries**: 46
- **Unique Individuals**: 149
- **Most Positions**: Dr. Dimitrij Rupel (6 positions)
- **Longest Serving**: Karl Erjavec (Defense, 1449 days)

## Data Sources

All data verified against official Slovenian government sources:
- https://www.gov.si/drzavni-organi/vlada/o-vladi/pretekle-vlade/
- Individual government pages for each administration
- Bilingual translations from official government terminology