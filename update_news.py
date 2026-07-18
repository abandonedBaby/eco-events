import urllib.request
import xml.etree.ElementTree as ET
import pandas as pd
import os

def fetch_live_news():
    url = "https://nfs.faireconomy.media/ff_calendar_thisweek.xml"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    events = []
    
    try:
        with urllib.request.urlopen(req) as response:
            xml_data = response.read()
        root = ET.fromstring(xml_data)
        for event in root.findall('event'):
            country = event.find('country').text if event.find('country') is not None else ""
            impact = event.find('impact').text if event.find('impact') is not None else ""
            
            if country == 'USD' and impact == 'High':
                title = event.find('title').text
                date_str = event.find('date').text
                time_str = event.find('time').text
                
                if time_str and 'All Day' not in time_str and 'Tentative' not in time_str:
                    try:
                        dt_str = f"{date_str} {time_str}"
                        # Match original logic: Localize XML as UTC, convert to Eastern, strip TZ info
                        dt_obj = pd.to_datetime(dt_str).tz_localize('UTC').tz_convert('US/Eastern').tz_localize(None)
                        events.append({'Event_Time': dt_obj.strftime('%Y-%m-%d %H:%M:%S'), 'title': title})
                    except Exception:
                        pass
        return pd.DataFrame(events)
    except Exception as e:
        print(f"Error fetching live XML: {e}")
        return pd.DataFrame()

# File paths
csv_filename = "news_archive.csv"

# 1. Load existing historical news database if it exists
if os.path.exists(csv_filename):
    archive_df = pd.read_csv(csv_filename)
else:
    archive_df = pd.DataFrame(columns=['Event_Time', 'title'])

# 2. Fetch new weekly events
live_df = fetch_live_news()

if not live_df.empty:
    # Combine, drop duplicates based on time and title, and sort
    combined_df = pd.concat([archive_df, live_df], ignore_index=True)
    combined_df = combined_df.drop_duplicates(subset=['Event_Time', 'title'], keep='first')
    combined_df = combined_df.sort_values(by='Event_Time', ascending=False)
    
    # Save back to your repository
    combined_df.to_csv(csv_filename, index=False)
    print(f"Successfully synced news archive. Total records: {len(combined_df)}")
else:
    print("No new news events found or fetch failed.")