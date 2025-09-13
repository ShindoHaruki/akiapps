import os
import re
import gspread
from google.oauth2.service_account import Credentials
from flask import Flask, jsonify, request
from models import db, Combo

# 認証設定
SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
CREDS = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
CLIENT = gspread.authorize(CREDS)
SPREADSHEET_ID = '1xDQA97pQJyiZ_CWMmOAz6-87xK3h3FwJ4NtE5ZMXo70'

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///combos.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def load_data_from_sheet():
    """スプレッドシートからデータを読み込み、データベースを更新する"""
    try:
        sheet = CLIENT.open_by_key(SPREADSHEET_ID).sheet1
        all_data = sheet.get_all_values()
        headers = all_data[0]
        records = all_data[1:]
    except gspread.exceptions.APIError as e:
        print(f"APIエラー: スプレッドシートの共有設定を確認してください。{e}")
        return
    except Exception as e:
        print(f"データの読み込みに失敗しました: {e}")
        return

    with app.app_context():
        db.session.query(Combo).delete()
        db.session.commit()

        new_combos = []
        for row in records:
            record_dict = dict(zip(headers, row))
            
            new_combo = Combo(
                title=record_dict.get('title'),
                combo_string=record_dict.get('combo_string'),
                situation=record_dict.get('situation'),
                poison=record_dict.get('poison'),
                opponent_state=record_dict.get('opponent_state'),
                gauge_usage=record_dict.get('gauge_usage'),
                comment=record_dict.get('comment'),
                after_combo_situation=record_dict.get('after_combo_situation'),
                lethal_route=record_dict.get('lethal_route'),
                damage=record_dict.get('damage'),
                youtube_url=record_dict.get('youtube_url')
            )
            new_combos.append(new_combo)
        
        db.session.add_all(new_combos)
        db.session.commit()
        print("スプレッドシートからデータベースを更新しました。")

with app.app_context():
    db.create_all()
    load_data_from_sheet()

# コンボ検索API
@app.route('/api/combos', methods=['GET'])
def get_combos():
    situation = request.args.get('situation')
    poison = request.args.get('poison')
    opponent_state = request.args.get('opponent_state')
    gauge_usage = request.args.get('gauge_usage')
    lethal_route = request.args.get('lethal_route')
    after_combo_situation = request.args.get('after_combo_situation')

    query = Combo.query
    if situation and situation != 'どこでも':
        query = query.filter_by(situation=situation)
    if poison and poison != '気にしない':
        query = query.filter_by(poison=poison)
    if opponent_state and opponent_state != 'どちらでも':
        query = query.filter_by(opponent_state=opponent_state)
    if gauge_usage and gauge_usage != '気にしない':
        query = query.filter_by(gauge_usage=gauge_usage)
    if lethal_route and lethal_route != '気にしない':
        query = query.filter(Combo.lethal_route.like(f'%{lethal_route}%'))
    if after_combo_situation and after_combo_situation != '':
        # テキストボックスが空の場合はフィルタリングしない
        query = query.filter(Combo.after_combo_situation.like(f'%{after_combo_situation}%'))

    combos = query.all()

    results = []
    for combo in combos:
        match = re.search(r'v=([^&]+)', combo.youtube_url)
        youtube_embed_url = f'https://www.youtube.com/embed/{match.group(1)}' if match else None

        results.append({
            'title': combo.title,
            'combo_string': combo.combo_string,
            'situation': combo.situation,
            'poison': combo.poison,
            'opponent_state': combo.opponent_state,
            'gauge_usage': combo.gauge_usage,
            'comment': combo.comment,
            'after_combo_situation': combo.after_combo_situation,
            'lethal_route': combo.lethal_route,
            'damage': combo.damage,
            'youtube_embed_url': youtube_embed_url
        })
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)