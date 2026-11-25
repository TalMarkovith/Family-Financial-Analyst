"""The family's category taxonomy, in one place.

Every sub-category belongs to exactly ONE parent category. Before this,
Groceries_Supermarket and Dining_Restaurants_Wolt were listed under both their
food parent and Variable_Daily ("הוצאות יומיומיות"). The classifier could then
file the same kind of purchase under either parent, which made per-category
trends (e.g. daily expenses) depend on which parent it happened to pick.

Decisions for the two shared sub-categories (they follow how the ledger has
actually been classified so far, so existing data does not move):
  * Groceries_Supermarket   -> Food            (never filed under Variable_Daily)
  * Dining_Restaurants_Wolt -> Food_Delivery   (never filed under Variable_Daily)
Variable_Daily keeps the non-food items: furniture, clothing, gifts, general.

Use normalize_category() whenever a (category, sub_category) pair is produced
or saved, so the parent always follows the sub-category.
"""
from __future__ import annotations

TAXONOMY: dict[str, list[str]] = {
    'Housing_Fixed': ['Rent_Mortgage', 'Utilities_Arnona_Elec_Water_Gas', 'Communication', 'Maintenance_Vaad_Cleaner'],
    'Insurance_Health': ['Insurances', 'Kupat_Holim', 'Private_Medical'],
    'Kids_Family': ['Gan_Education', 'Baby_Equipment_Pharm', 'Kids_Clothing_Toys'],
    'Transportation': ['Car_Gas_Tolls', 'Public_Transit_Taxi', 'Parking_Tolls', 'Car_Maintenance_Licensing'],
    'Variable_Daily': ['Home_Furniture_Decor', 'Clothing_Shoes', 'Gifts_Events', 'General_Shopping'],
    'Leisure_Grooming': ['Subscriptions', 'Personal_Care_Hair_Nails', 'Hobbies_Entertainment_Vacation'],
    'Food': ['Groceries_Supermarket', 'Coffee_Restaurants'],
    'Food_Delivery': ['Dining_Restaurants_Wolt'],
    'Pharm': ['Pharm'],
    'Health': ['Medical_Insurance', 'sport_club_gym'],
    'Insurance': ['Life_Insurance', 'Medical_Private_Insurance'],
    'Home': ['Direct_Online_Shopping'],
    'Investments': ['Savings_Analyst_Brokerage'],
    'Income': ['Tal_Salary', 'Reut_Salary', 'Other_Income_Bit'],
    'Rio': ['Rio_Food', 'Rio_Health', 'Rio_Accessories'],
    'Leisure': ['Tal_Specials'],
}
ALL_CATEGORIES: list[str] = list(TAXONOMY.keys())

# Known misspellings of sub-categories seen in stored data.
SUB_ALIASES: dict[str, str] = {
    '_Pharm': 'Pharm',
}

_PARENT_OF: dict[str, str] = {}
for _parent, _subs in TAXONOMY.items():
    for _sub in _subs:
        if _sub in _PARENT_OF:
            raise ValueError(f"Sub-category {_sub!r} listed under both {_PARENT_OF[_sub]!r} and {_parent!r}")
        _PARENT_OF[_sub] = _parent


def canonical_parent(sub_category) -> str | None:
    """The one parent category of a sub-category, or None if it is not in the taxonomy."""
    if not isinstance(sub_category, str):
        return None
    sub = SUB_ALIASES.get(sub_category, sub_category)
    return _PARENT_OF.get(sub)


def normalize_category(category, sub_category):
    """Return (category, sub_category) with the parent forced to the sub-category's parent.

    Unknown sub-categories (e.g. 'Unknown', 'Error') are returned unchanged.
    """
    sub = SUB_ALIASES.get(sub_category, sub_category) if isinstance(sub_category, str) else sub_category
    parent = canonical_parent(sub)
    return (parent if parent else category), sub


def normalize_frame(df):
    """Copy of df with Category/Sub_Category normalized row by row."""
    out = df.copy()
    if out.empty or 'Sub_Category' not in out.columns:
        return out
    pairs = [normalize_category(c, s) for c, s in zip(out['Category'], out['Sub_Category'])]
    out['Category'] = [p[0] for p in pairs]
    out['Sub_Category'] = [p[1] for p in pairs]
    return out
