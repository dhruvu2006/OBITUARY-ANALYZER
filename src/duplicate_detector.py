import difflib


def find_duplicates(entries):
    """
    Detects possible duplicate entries based on name similarity and age.
    
    Args:
        entries (list of dict): List of extracted entry dicts.
        
    Returns:
        list of tuples: Each tuple is a pair of indices (i, j) that might be duplicates.
    """
    duplicates = []
    n = len(entries)

    for i in range(n):
        for j in range(i + 1, n):
            name_i = entries[i].get('Name', '').lower()
            name_j = entries[j].get('Name', '').lower()
            age_i = str(entries[i].get('Age', ''))
            age_j = str(entries[j].get('Age', ''))

            # Calculate name similarity
            similarity = difflib.SequenceMatcher(None, name_i, name_j).ratio()

            # Flag if names are very similar (>85%) and ages match
            if similarity > 0.85 and age_i == age_j and age_i != 'Unknown':
                duplicates.append((i, j, round(similarity, 2)))
            # Or if names are almost identical (>95%) regardless of age
            elif similarity > 0.95:
                duplicates.append((i, j, round(similarity, 2)))

    return duplicates
