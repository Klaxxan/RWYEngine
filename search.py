from rapidfuzz import fuzz, process

def prepare_search_data(entries):
    """
    Convert database rows or Entry objects into a searchable dict.
    Keys: entry IDs
    Values: combined searchable text
    """
    search_dict = {}

    for e in entries:
        # If e is a sqlite3.Row or a dict-like row
        if isinstance(e, dict) or hasattr(e, "keys"):
            entry_id = e["id"]
            title = e["title"] or ""
            description = e["description"] or ""
            category = e["category"] or ""
            tags = e["tags"] or ""
            synonyms = e["synonyms"] or ""
        else:
            # If e is an Entry model
            entry_id = e.id
            title = e.title
            description = e.description
            category = e.category
            tags = e.tags
            synonyms = e.synonyms

        combined = f"{title} {description} {category} {tags} {synonyms}"
        search_dict[entry_id] = combined

    return search_dict


def fuzzy_search(query, entries, limit=20):
    """
    Perform fuzzy search on entries.
    Returns a list of (entry_id, score) sorted by relevance.
    """
    if not query.strip():
        return []

    search_dict = prepare_search_data(entries)

    # RapidFuzz process.extract gives best matches
    results = process.extract(
        query,
        search_dict,
        scorer=fuzz.token_sort_ratio,
        limit=limit
    )

    # Format: [(entry_id, score), ...]
    cleaned_results = [(match[2], int(match[1])) for match in results]

    return cleaned_results
