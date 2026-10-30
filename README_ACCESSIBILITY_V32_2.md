# v32.2 UI readability update

- Activate shared CSS in app.py (previously defined but not called).
- Increase common typography and strengthen text contrast.
- Difference charts: replace red with orange, add grid/ticks, separate percentage-point and count groups, and cap chart width.
- Narrow small tables in dashboard and difference comparisons.
- Keep the analytical meaning of district vs region: district means one of 39 units; region is used only for general geographic context.

Browser validation still needed: run Streamlit and inspect at 100% zoom, then run Chrome/Edge Lighthouse accessibility audit. This package has passed Python syntax compilation only, not a live-browser Lighthouse audit.
