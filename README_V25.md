# HOU-GA v25.0 - linked weights

- The weight pattern page saves/loads weights; session state is shared with dashboard, rankings, district comparison, district detail, map district table, city analysis, simulation, decision support and AI context.
- Selecting a pattern and clicking Apply updates the current session; all other pages recompute using the same weights.
- Rankings can select the weighted score; map pin display is still unavailable until geographic coordinates are verified.
- Weighted scores are within-39-district relative normalization and do not predict policy outcomes.
- Historical datasets are not current 2026 statistics.
- The API key should be in a local .env file at the application root; do not share it.
