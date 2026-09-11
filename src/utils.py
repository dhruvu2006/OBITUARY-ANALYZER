import pandas as pd

# --- Demo Mode Constants ---
DEMO_TOTAL_PAGES = 24
DEMO_DETECTED_PAGES = [
    {"page": 7,  "score": 94, "label": "OBITUARY",        "entries": 8},
    {"page": 12, "score": 87, "label": "DEATH NOTICES",   "entries": 5},
    {"page": 18, "score": 76, "label": "DEATH NOTICES",   "entries": 2},
]


def get_demo_data():
    """
    Returns a demo DataFrame with all fields populated.
    Used when Demo Mode is active.
    """
    data = [
        # Page 7
        {"Name": "Alice Brown",       "Age": "92", "Age_Source": "direct",     "Page": 7,  "Notice_Type": "Obituary",     "Location": "Kerala",   "Date": "2026-09-08", "Confidence": 0.95},
        {"Name": "David Moore",       "Age": "71", "Age_Source": "direct",     "Page": 7,  "Notice_Type": "Death Notice", "Location": "Unknown",  "Date": "Unknown",    "Confidence": 0.88},
        {"Name": "Dorothy Harris",    "Age": "95", "Age_Source": "direct",     "Page": 7,  "Notice_Type": "Obituary",     "Location": "Kochi",    "Date": "2026-09-07", "Confidence": 0.92},
        {"Name": "Elizabeth Davis",   "Age": "91", "Age_Source": "direct",     "Page": 7,  "Notice_Type": "Memorial",     "Location": "Thrissur", "Date": "2026-09-05", "Confidence": 0.91},
        {"Name": "James Miller",      "Age": "62", "Age_Source": "calculated", "Page": 7,  "Notice_Type": "Death Notice", "Location": "Unknown",  "Date": "Unknown",    "Confidence": 0.75},
        {"Name": "John Mathew",       "Age": "74", "Age_Source": "direct",     "Page": 7,  "Notice_Type": "Death Notice", "Location": "Kannur",   "Date": "2026-09-09", "Confidence": 0.93},
        {"Name": "Joseph White",      "Age": "76", "Age_Source": "direct",     "Page": 7,  "Notice_Type": "Obituary",     "Location": "Unknown",  "Date": "Unknown",    "Confidence": 0.87},
        {"Name": "Margaret Clark",    "Age": "84", "Age_Source": "direct",     "Page": 7,  "Notice_Type": "Memorial",     "Location": "Calicut",  "Date": "2026-09-06", "Confidence": 0.90},
        # Page 12
        {"Name": "Mary Thomas",       "Age": "81", "Age_Source": "direct",     "Page": 12, "Notice_Type": "Obituary",     "Location": "Trivandrum","Date": "2026-09-08","Confidence": 0.94},
        {"Name": "Michael Smith",     "Age": "79", "Age_Source": "direct",     "Page": 12, "Notice_Type": "Death Notice", "Location": "Unknown",  "Date": "Unknown",    "Confidence": 0.86},
        {"Name": "Richard Martin",    "Age": "59", "Age_Source": "direct",     "Page": 12, "Notice_Type": "Death Notice", "Location": "Unknown",  "Date": "2026-09-07", "Confidence": 0.80},
        {"Name": "Robert Wilson",     "Age": "67", "Age_Source": "direct",     "Page": 12, "Notice_Type": "Obituary",     "Location": "Ernakulam","Date": "2026-09-09", "Confidence": 0.92},
        {"Name": "Sarah Johnson",     "Age": "88", "Age_Source": "direct",     "Page": 12, "Notice_Type": "Memorial",     "Location": "Kottayam", "Date": "2026-09-06", "Confidence": 0.89},
        # Page 18
        {"Name": "Susan Anderson",    "Age": "68", "Age_Source": "direct",     "Page": 18, "Notice_Type": "Condolence",   "Location": "Unknown",  "Date": "Unknown",    "Confidence": 0.72},
        {"Name": "William Taylor",    "Age": "55", "Age_Source": "direct",     "Page": 18, "Notice_Type": "Death Notice", "Location": "Unknown",  "Date": "2026-09-08", "Confidence": 0.83},
    ]
    return pd.DataFrame(data)
