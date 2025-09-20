import os
import json
import re
import gspread
import logging
from google.oauth2.service_account import Credentials
from flask import Flask, jsonify, request

app = Flask(__name__)

# ===== ログ設定 =====
logging.basicConfig(
    filename='/home/ubuntu/akiapps/app.log',
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)

# グローバル変数としてデータを格納
COMBO_DATA = []

# --- Google スプレッドシート認証 ---
try:
    with open("/home/ubuntu/akiapps/credentials.json", "r") as f:
        CREDS_JSON = json.load(f)
    SCOPES = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    CREDS = Credentials.from_service_account_info(CREDS_JSON, scopes=SCOPES)
    CLIENT = gspread.authorize(CREDS)
except Exception as e:
    logging.error(f"Google認証情報の読み込みに失敗しました: {e}")
    CLIENT = None

SPREADSHEET_ID = '1xDQA97pQJyiZ_CWMmOAz6-87xK3h3FwJ4NtE5ZMXo70'

def load_data_from_sheet():
    """スプレッドシートからデータを読み込み、グローバル変数に格納する"""
    global COMBO_DATA
    if CLIENT is None:
        logging.warning("Googleクライアントが利用できません。データをロードできません。")
        COMBO_DATA = []
        return

    try:
        sheet = CLIENT.open_by_key(SPREADSHEET_ID).sheet1
        all_data = sheet.get_all_values()
        headers = all_data[0]
        records = all_data[1:]
        COMBO_DATA = [dict(zip(headers, row)) for row in records]
        logging.info("スプレッドシートからデータをロードしました。")
    except Exception as e:
        logging.error(f"データの読み込みに失敗しました: {e}")
        COMBO_DATA = []

# 起動時にロード
load_data_from_sheet()

@app.route("/")
def index():
    return "Hello from Flask"

@app.route('/api/combos', methods=['GET'])
def get_combos():
    try:
        situation = request.args.get('situation')
        poison = request.args.get('poison')
        opponent_state = request.args.get('opponent_state')
        gauge_usage = request.args.get('gauge_usage')
        lethal_route = request.args.get('lethal_route')
        after_combo_situation = request.args.get('after_combo_situation')

        filtered_combos = COMBO_DATA

        if situation and situation != 'どこでも':
            filtered_combos = [c for c in filtered_combos if c.get('situation') == situation]
        if poison and poison != '気にしない':
            filtered_combos = [c for c in filtered_combos if c.get('poison') == poison]
        if opponent_state and opponent_state != 'どちらでも':
            filtered_combos = [c for c in filtered_combos if c.get('opponent_state') == opponent_state]
        if gauge_usage and gauge_usage != '気にしない':
            filtered_combos = [c for c in filtered_combos if c.get('gauge_usage') == gauge_usage]
        if lethal_route and lethal_route != '気にしない':
            filtered_combos = [c for c in filtered_combos if lethal_route in c.get('lethal_route', '')]
        if after_combo_situation and after_combo_situation != '':
            filtered_combos = [c for c in filtered_combos if after_combo_situation in c.get('after_combo_situation', '')]

        results = []
        for combo in filtered_combos:
            match = re.search(r'v=([^&]+)', combo.get('youtube_url', ''))
            youtube_embed_url = f'https://www.youtube.com/embed/{match.group(1)}' if match else None

            results.append({
                'title': combo.get('title'),
                'combo_string': combo.get('combo_string'),
                'situation': combo.get('situation'),
                'poison': combo.get('poison'),
                'opponent_state': combo.get('opponent_state'),
                'gauge_usage': combo.get('gauge_usage'),
                'comment': combo.get('comment'),
                'after_combo_situation': combo.get('after_combo_situation'),
                'lethal_route': combo.get('lethal_route'),
                'damage': combo.get('damage'),
                'youtube_embed_url': youtube_embed_url
            })
        return jsonify(results)

    except Exception as e:
        logging.error(f"API処理中に例外が発生しました: {e}")
        return jsonify([]), 200

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
