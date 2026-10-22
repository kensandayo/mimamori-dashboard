# District relative evaluation update

- District detail page now displays each active indicator's raw value, unweighted mean of districts, difference from that mean, descending raw-value rank, and relative position.
- Relative high / low is based on the upper / lower quartiles of available district observations. Ties share a rank. Uniform observations are labeled as such.
- Risk direction is shown separately; high does not always mean problematic.
- Reference-only indicators in the regional profile also display relative comparisons.
- These comparisons reflect the currently loaded data, which may contain demonstration values. They are not validated service-need estimates.
- Existing policy comparison navigation and other pages are preserved.

Run: `pip install -r requirements.txt` then `streamlit run app.py`.
