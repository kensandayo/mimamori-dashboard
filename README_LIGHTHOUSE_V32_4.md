# v32.4 Lighthouse improvements

Based on the provided Lighthouse report (accessibility 86/100).

- Sidebar captions and helper text: increased contrast and size.
- Navigation links and sidebar form controls: minimum 44px target height.
- Focus outlines for keyboard navigation.
- Small dashboard labels increased for readability.

Not addressed automatically: semantic heading order, third-party Streamlit component ARIA attributes, and performance metrics. Those require browser inspection and possibly component updates.

Run Lighthouse again in Edge/Chrome after opening the app and waiting for data to load. Scores are not guaranteed.
