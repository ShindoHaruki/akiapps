import os
import json
import re
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, jsonify, request

# 環境変数から認証情報を取得
with open("credentials.json", "r") as f:
    CREDS_JSON = json.load(f)
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
CREDS = Credentials.from_service_account_info(CREDS_JSON, scopes=SCOPES)
CLIENT = gspread.authorize(CREDS)
# === スプレッドシートのIDをここに貼り付け ===
# スプレッドシートのURLからIDを取得してください
SPREADSHEET_ID = 'ここにあなたのスプレッドシートIDを貼り付け'

app = Flask(__name__)

# グローバル変数としてデータを格納
COMBO_DATA = []

def load_data_from_sheet():
    """スプレッドシートからデータを読み込み、グローバル変数に格納する"""
    try:
        sheet = CLIENT.open_by_key(SPREADSHEET_ID).sheet1
        all_data = sheet.get_all_values()
        headers = all_data[0]
        records = all_data[1:]
        
        # データを辞書形式のリストに変換
        global COMBO_DATA
        COMBO_DATA = [dict(zip(headers, row)) for row in records]
        print("スプレッドシートからデータをロードしました。")
    except Exception as e:
        print(f"データの読み込みに失敗しました: {e}")
        COMBO_DATA = []

# アプリケーション起動時にデータを読み込む
load_data_from_sheet()

@app.route('/api/combos', methods=['GET'])
def get_combos():
    situation = request.args.get('situation')
    poison = request.args.get('poison')
    opponent_state = request.args.get('opponent_state')
    gauge_usage = request.args.get('gauge_usage')
    lethal_route = request.args.get('lethal_route')
    after_combo_situation = request.args.get('after_combo_situation')

    # メモリ上のデータに対してフィルタリングを実行
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
        # YouTube URLから動画IDを抽出
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

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)