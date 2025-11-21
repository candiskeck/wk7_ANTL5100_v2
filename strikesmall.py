import pandas as pd

# Load your full dataset
strikes = pd.read_csv(r"C:\Users\Candis\Documents\candis\ANTL 5100\Strike_Reports.csv",
                      encoding='latin1', low_memory=False)

# Option 1: Keep only the columns your dashboard uses
columns_needed = ["INDEX_NR", "AIRPORT_ID", "AIRPORT", "INDICATED_DAMAGE",
                  "STR_ENG1", "COST_REPAIRS", "INCIDENT_DATE", "INCIDENT_YEAR", "INCIDENT_MONTH", "STATE"]
strikes_small = strikes[columns_needed]

# Option 2: Optionally, keep only a subset of rows (e.g., last 5 years)
strikes_small["INCIDENT_DATE"] = pd.to_datetime(strikes_small["INCIDENT_DATE"], errors='coerce')
strikes_small = strikes_small[strikes_small["INCIDENT_DATE"].dt.year >= 2018]

# Save the smaller CSV
strikes_small.to_csv(r"C:\Users\Candis\Documents\candis\ANTL 5100\Strike_Reports_small.csv", index=False)
print("Smaller CSV created!")