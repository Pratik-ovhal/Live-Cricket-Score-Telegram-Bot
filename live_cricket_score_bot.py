import requests
from bs4 import BeautifulSoup
import time
import json
import os
from datetime import datetime

# —————————————————————————————
# CONFIGURATION
# —————————————————————————————
BOT_TOKEN = 'YOUR BOT TOKEN HERE'
SUBSCRIBERS_FILE = 'subscribers.json'
POLL_INTERVAL = 60  # seconds
ALLOWED_HOURS = tuple(range(24))




# —————————————————————————————
# STATE LOAD
# —————————————————————————————
if os.path.exists(SUBSCRIBERS_FILE):
    with open(SUBSCRIBERS_FILE, 'r') as f:
        data = json.load(f)
    if isinstance(data, list):
        subscribers = {int(cid): None for cid in data}
    else:
        subscribers = {int(cid): msgid for cid, msgid in data.items()}
else:
    subscribers = {}



last_update_id = 0

# —————————————————————————————
# HELPERS
# —————————————————————————————
def is_allowed_time():
    current_hour = datetime.now().hour
    return current_hour in ALLOWED_HOURS

def save_subscribers():
    to_dump = {str(cid): msgid for cid, msgid in subscribers.items()}
    with open(SUBSCRIBERS_FILE, 'w') as f:
        json.dump(to_dump, f)



def fetch_updates():
    global last_update_id
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/getUpdates'
    params = {'timeout': 5, 'offset': last_update_id + 1}
    resp = requests.get(url, params=params).json()

    for upd in resp.get('result', []):
        last_update_id = max(last_update_id, upd['update_id'])
        msg = upd.get('message')
        if not msg:
            continue
        chat_id = msg['chat']['id']
        text = msg.get('text', '')
        if text.strip().lower() == '/start':
            if chat_id not in subscribers:
                subscribers[chat_id] = None
                save_subscribers()
                send_message(chat_id, "🎉 <b>Welcome!</b>\n\nYou have <b>subscribed</b> to the Live Cricket Score Bot!\n\nMade by 👉 <b>@pratik_ovhal13</b> (Instagram)")

        callback = upd.get('callback_query')
        if callback:
            chat_id = callback['message']['chat']['id']
            query_id = callback['id']
            data = callback['data']

            if data == 'refresh':
                live_score = get_live_update()
                answer_callback_query(query_id)
                send_message(chat_id, live_score)

def answer_callback_query(callback_query_id):
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/answerCallbackQuery'
    requests.post(url, data={'callback_query_id': callback_query_id})

def send_message(chat_id, text):
    prev_id = subscribers.get(chat_id)
    if prev_id is not None:
        del_url = f'https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage'
        try:
            requests.post(del_url, data={'chat_id': chat_id, 'message_id': prev_id})
        except:
            pass

    send_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': chat_id,
        'text': f"{text}\n\n🔔 <i>Made with ❤️ by @pratik_ovhal13</i>",
        'parse_mode': 'HTML',
        'reply_markup': json.dumps({
            "inline_keyboard": [
                [{"text": "🔄 Refresh Score", "callback_data": "refresh"}],
                [{"text": "📸 Follow on Instagram", "url": "https://instagram.com/pratik_ovhal13"}]
            ]
        })
    }

    try:
        resp = requests.post(send_url, data=payload).json()
        new_id = resp.get('result', {}).get('message_id')
        subscribers[chat_id] = new_id
        save_subscribers()
    except:
        pass


# —————————————————————————————
# SCRAPER
# —————————————————————————————




def get_live_update():
    homepage_url = 'https://www.cricbuzz.com/'
    r = requests.get(homepage_url)
    soup = BeautifulSoup(r.content, 'html.parser')

    match_links = soup.find_all('a', href=True)

    live_match_url = None

    for link in match_links:
        href = link['href']
        if '/live-cricket-scores/' in href:
            live_match_url = 'https://www.cricbuzz.com' + href
            break

    if not live_match_url:
        return "🚫 <b>No live match happening currently!</b>"

    match_resp = requests.get(live_match_url)
    match_soup = BeautifulSoup(match_resp.content, 'html.parser')

    # Match Title
    match_title = match_soup.find('h1', class_='cb-nav-hdr cb-font-18 line-ht24')
    match_title = match_title.text.strip() if match_title else "Live Match"

    # Match Status
    status_block = match_soup.find('div', class_='cb-text-inprogress')
    match_status = status_block.text.strip() if status_block else "Status unavailable"

    # Teams and Score
    Liveteam1 = soup.find('div', class_='cb-hmscg-tm-bat-scr cb-font-14').text.strip()
    Liveteam2 = soup.find('div', class_='cb-hmscg-tm-bwl-scr cb-font-14').text.strip()

    # Prepare Final Message
    message = f"""🏏 <b>{match_title}</b>

<b>📢 Match Status:</b> {match_status}

<b>🆚 Teams:</b>
🔹 {Liveteam1}
🔹 {Liveteam2}

✨ Stay tuned for more updates and enjoy the match!
"""
    return message






# —————————————————————————————
# MAIN LOOP
# —————————————————————————————
def main():
    print("🚀 Bot started. Polling and sending updates...")
    last_sent_message = None

    while True:
        fetch_updates()

        if not is_allowed_time():
            print("⏰ Outside allowed time. Bot is idle.")
            time.sleep(POLL_INTERVAL)
            continue

        live_update = get_live_update()

        if subscribers:
            if live_update != last_sent_message:
                for cid in list(subscribers.keys()):
                    send_message(cid, live_update + "\n\n📌 Made by @pratik_ovhal13 (Instagram)")
                last_sent_message = live_update
                print("✅ Sent update to subscribers.")
            else:
                print("📭 No new update.")

        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    main()
