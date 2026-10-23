"""Local, review-gated municipal knowledge and persistent conversations.
SQLite is single-instance local storage; do not deploy publicly without auth, encryption and backup policy.
"""
import json
import os
import re
import sqlite3
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = Path(os.getenv("HOUGA_KNOWLEDGE_DB", str(ROOT / "local_data" / "city_knowledge.sqlite3")))
MAX_TEXT = 3000

def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS conversations (
      id INTEGER PRIMARY KEY AUTOINCREMENT, district TEXT NOT NULL,
      role TEXT NOT NULL CHECK(role IN ('user','assistant')),
      content TEXT NOT NULL, created_at TEXT NOT NULL);
    CREATE TABLE IF NOT EXISTS knowledge (
      id INTEGER PRIMARY KEY AUTOINCREMENT, district TEXT NOT NULL,
      category TEXT NOT NULL, content TEXT NOT NULL, source TEXT NOT NULL,
      status TEXT NOT NULL CHECK(status IN ('pending','approved','rejected','archived')),
      created_at TEXT NOT NULL, updated_at TEXT NOT NULL, valid_until TEXT,
      reviewer_note TEXT NOT NULL DEFAULT '');
    """)
    return conn

def now():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")

def check_text(value, limit=MAX_TEXT):
    value = str(value or '').strip()
    if not value or len(value)>limit: raise ValueError(f'入力は1〜{limit}文字で指定してください')
    return value

def add_message(district,role,content):
    if role not in ('user','assistant'): raise ValueError('role')
    with connect() as db:
        db.execute('INSERT INTO conversations(district,role,content,created_at) VALUES(?,?,?,?)', (check_text(district,100),role,check_text(content,15000),now()))

def messages(district,limit=60):
    with connect() as db:
        rows=db.execute('SELECT role,content,created_at FROM conversations WHERE district=? ORDER BY id DESC LIMIT ?', (district,min(int(limit),200))).fetchall()
    return [dict(x) for x in reversed(rows)]

def clear_messages(district):
    with connect() as db: db.execute('DELETE FROM conversations WHERE district=?',(district,))

def propose(district,category,content,source,valid_until=None):
    t=now()
    if valid_until and not re.fullmatch(r'\d{4}-\d{2}-\d{2}',valid_until): raise ValueError('期限はYYYY-MM-DD形式')
    with connect() as db:
        cur=db.execute('INSERT INTO knowledge(district,category,content,source,status,created_at,updated_at,valid_until) VALUES(?,?,?,?,?,?,?,?)',
          (check_text(district,100),check_text(category,80),check_text(content),check_text(source,200),'pending',t,t,valid_until))
        return cur.lastrowid

def review(item_id,status,note=''):
    if status not in ('approved','rejected','archived'): raise ValueError('status')
    with connect() as db:
        db.execute('UPDATE knowledge SET status=?,reviewer_note=?,updated_at=? WHERE id=?', (status,str(note)[:500],now(),int(item_id)))

def update(item_id,content,source,valid_until=None):
    with connect() as db:
        db.execute('UPDATE knowledge SET content=?,source=?,valid_until=?,status=?,updated_at=? WHERE id=?',
          (check_text(content),check_text(source,200),valid_until,'pending',now(),int(item_id)))

def items(district=None,status=None):
    q='SELECT * FROM knowledge WHERE 1=1'; args=[]
    if district: q+=' AND district=?'; args.append(district)
    if status: q+=' AND status=?'; args.append(status)
    q+=' ORDER BY updated_at DESC, id DESC'
    with connect() as db: return [dict(r) for r in db.execute(q,args).fetchall()]

def retrieve(district,query='',limit=8):
    # No external embedding dependency. District records rank ahead of citywide ones.
    rows=[r for r in items(status='approved') if r['district'] in (district,'全市共通') and (not r['valid_until'] or r['valid_until']>=now()[:10])]
    tokens=set(re.findall(r'[\w一-龯ぁ-んァ-ン]{2,}',query.lower()))
    def score(r):
        hay=(r['category']+' '+r['content']).lower()
        return (10 if r['district']==district else 0)+sum(2 for t in tokens if t in hay)
    return sorted(rows,key=lambda r:(-score(r),-r['id']))[:limit]

def knowledge_prompt(rows):
    if not rows: return '確認・承認された現場情報は登録されていません。'
    return '\n'.join(f"[記録ID:{r['id']}] 地区:{r['district']} 種別:{r['category']} 内容:{r['content']} 出典:{r['source']} 有効期限:{r['valid_until'] or '未設定'}" for r in rows)
