import sqlite3
import os
import qrcode

DB = "herdsos.db"

# -----------------------------
# 1. Remove old database
# -----------------------------
if os.path.exists(DB):
    print("Removing old DB...")
    os.remove(DB)

conn = sqlite3.connect(DB)
c = conn.cursor()

# -----------------------------
# 2. Create tables
# -----------------------------
c.execute('''
CREATE TABLE hospitals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    phone TEXT,
    lat REAL,
    lon REAL,
    address TEXT
)
''')

c.execute('''
CREATE TABLE cows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    code TEXT,
    description TEXT
)
''')

c.execute('''
CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cow_id INTEGER,
    condition TEXT,
    photo TEXT,
    lat REAL,
    lon REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'pending',
    assigned_hospital INTEGER,
    tried_hospitals TEXT DEFAULT ''
)
''')

# -----------------------------
# 3. Seed hospitals
# -----------------------------
hospitals = [
    ('Bengaluru Vet Clinic','+91-80-1111-0001', 12.9716, 77.5946, 'Main Street, Bengaluru'),
    ('Whitefield Animal Care','+91-80-1111-0002', 12.9719, 77.7499, 'Whitefield'),
    ('Yelahanka Vet','+91-80-1111-0003', 13.0680, 77.5938, 'Yelahanka'),
    ('Mysore Road Clinic','+91-80-1111-0004', 12.2958, 76.6394, 'Mysore Road'),
    ('Vemana Vet Clinic','+91-80-1111-0007', 12.9297, 77.6224, 'Koramangala')
]

for h in hospitals:
    c.execute('INSERT INTO hospitals (name, phone, lat, lon, address) VALUES (?, ?, ?, ?, ?)', h)

# -----------------------------
# 4. Seed cows
# -----------------------------
cows = [
    ('COW-1001', 'Brown cow with ear tag A1'),
    ('COW-1002', 'Grey cow near market'),
    ('COW-1003', 'Stray cow - often in road'),
    ('COW-1004', 'Grey cow near junction')
]

for cow in cows:
    c.execute('INSERT INTO cows (code, description) VALUES (?, ?)', cow)

conn.commit()
conn.close()

# -----------------------------
# 5. Generate QR codes using VERCEL URL ONLY
# -----------------------------
VERCEL_BASE = "https://herdsosl.vercel.app/report/{}"
print("Using Vercel URL for QR:", VERCEL_BASE)

os.makedirs("qrcodes", exist_ok=True)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute("SELECT id FROM cows")
rows = cur.fetchall()

for r in rows:
    cowid = r[0]
    url = VERCEL_BASE.format(cowid)
    img = qrcode.make(url)
    img.save(os.path.join("qrcodes", f"cow_{cowid}.png"))

conn.close()

print("Database initialized and QR codes generated using Vercel URL!")

