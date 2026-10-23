# HOU-GA v23.0 — full-source, official-data integration

- 10 Streamlit pages connected to the navigation, including AI consultation and policy planning.
- 39-district official CSV only; no demo scores, invented coordinates, or synthetic policy outcomes.
- Original multipage source retained in `legacy_pages/`; supporting services/components/utils retained in place; old master files preserved in `legacy_data/` (not loaded).
- Map pins intentionally not drawn until accurate geocodes/boundaries are verified.
- AI requires `OPENAI_API_KEY` and external API access.
- User-entered budgets/staff are assumptions, not official statistics.
- Population baseline mainly 2021-09-30; resource counts R3/R4, not current.

Run: `pip install -r requirements.txt` then `streamlit run app.py`.

This version restores usable navigation rather than claiming every legacy implementation is fully migrated.
