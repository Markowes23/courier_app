# Courier App

This demo application implements a simple courier workflow using Tkinter. It can:

- Manage van details and automatically fill capacity using built-in data.
- Add stops by address and load. Travel time is calculated automatically using Google Maps or OSRM.
- After adding stops you can start the route which opens an interactive map preview (requires `tkintermapview`). Weather data for each stop is retrieved from **open-meteo.com**.
- Notifications are scheduled five minutes before each stop to remind about upcoming deliveries.

Run `pip install -r requirements.txt` to install dependencies. An optional `GOOGLE_API_KEY` environment variable enables more accurate travel times via Google Directions API.

To build a standalone executable, install `pyinstaller` and run:

```
pyinstaller --onefile app.py
```

The resulting binary can be found in the `dist` folder (e.g. `dist/app` or `dist/app.exe` on Windows).

This code is intended for educational purposes and may require additional error handling for production use.
