#-------------------------------------------------------------------------------------------------------------------

#Hey curious developer, Its nice to see you here 
#Feel free to find any bugs, errors or any kind of problems in the code 
#You can also tell what improvements can be done or what new features should be added
#Contact : pratikaovhal@gmail.com
#          @pratik_ovhal13(instagram) 
#Your any kind advice is very helpful for this project which is being created by only 1 developer  

#--------------------------------------------------------------------------------------------------------------------







import requests
from bs4 import BeautifulSoup
import time
import json
import os

# —————————————————————————————
# CONFIGURATION
# —————————————————————————————
BOT_TOKEN = 'YOUR BOT TOKEN HERE'
SUBSCRIBERS_FILE = 'subscribers.json'
POLL_INTERVAL = 60  # seconds

# —————————————————————————————
# STATE LOAD WITH PATCH
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
                send_message(chat_id, "🎉 You have Subscribed to live cricket score bot created by \n@pratik_ovhal13 (instagram)!")


def send_message(chat_id, text):
    prev_id = subscribers.get(chat_id)
    if prev_id is not None:
        del_url = f'https://api.telegram.org/bot{BOT_TOKEN}/deleteMessage'
        requests.post(del_url, data={'chat_id': chat_id, 'message_id': prev_id})
    send_url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    payload = {'chat_id': chat_id, 'text': text}
    resp = requests.post(send_url, data=payload).json()
    new_id = resp.get('result', {}).get('message_id')
    subscribers[chat_id] = new_id
    save_subscribers()


def get_scores():
    r = requests.get('https://www.cricbuzz.com/')
    soup = BeautifulSoup(r.content, 'html.parser')
    
    # Live
    t1 = soup.find('div', class_='cb-hmscg-tm-bat-scr cb-font-14')
    t2 = soup.find('div', class_='cb-hmscg-tm-bwl-scr cb-font-14')
    res = soup.find('div', class_='cb-mtch-crd-state cb-ovr-flo cb-font-12 cb-text-apple-red')
    if t1 and t2:
        return 'live', f"🏏 Live Score:\n{t1.text.strip()}\n{t2.text.strip()}\n{res.text.strip()}"
    
    # Completed
    t1 = soup.find('div', class_='cb-col-100 cb-ovr-flo cb-hmscg-tm-bat-scr cb-font-14')
    t2 = soup.find('div', class_='cb-col-100 cb-ovr-flo cb-hmscg-tm-bwl-scr cb-font-14')
    #res = soup.find('div', class_='cb-mtch-crd-state cb-ovr-flo cb-font-12 cb-text-apple-red')
    if t1 and t2 and res:
        msg = f"✅ Match Result:\n{t1.text.strip()}\n{t2.text.strip()}\nResult: {res.text.strip()}"
        return 'completed', msg
    return 'none', None

# —————————————————————————————
# MAIN LOOP
# —————————————————————————————
def main():
    print("🚀 Bot started. Polling and sending updates...")
    match_ended = False
    while True:
        fetch_updates()
        state, info = get_scores()
        if subscribers:
            if state == 'live':
                if match_ended:
                    match_ended = False
                for cid in list(subscribers.keys()):
                    send_message(cid, info + "\n\n📌 Made by @pratik_ovhal13 (Instagram)")
            elif state == 'completed':
                if not match_ended:
                    for cid in list(subscribers.keys()):
                        send_message(cid, info + "\n\n📌 Made by @pratik_ovhal13 (Instagram)")
                    match_ended = True
            # else: no match, do nothing
        time.sleep(POLL_INTERVAL)

if __name__ == '__main__':
    main()
