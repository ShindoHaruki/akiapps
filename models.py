from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Combo(db.Model):
    __tablename__ = 'combos'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100))
    combo_string = db.Column(db.Text, nullable=False)
    situation = db.Column(db.String(50), nullable=False)
    poison = db.Column(db.String(50), nullable=False)
    opponent_state = db.Column(db.String(50), nullable=False)
    gauge_usage = db.Column(db.String(50), nullable=False)
    comment = db.Column(db.String(200))
    # 新規追加: コンボ後状況
    after_combo_situation = db.Column(db.String(50))
    # 新規追加: リーサルルート
    lethal_route = db.Column(db.String(50))
    damage = db.Column(db.Integer)
    youtube_url = db.Column(db.String(200))