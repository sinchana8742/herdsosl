import sqlite3
import os
import qrcode
import socket

# -----------------------
# AUTO-DETECT LOCAL IP
# -----------------------
def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # No internet required, only routing
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

local_ip = get_local_ip()
print("Auto-detected IP:", local_ip)

# -----------------------
# DATABASE RESET
# -----------------------
DB = 'herdsos.db'

if os.path.exists(DB):
    print('Removing old DB...')
    os.remove(DB)

conn = sqlite3.connect(DB)
c = conn.cursor()

# -----------------------
# CREATE TABLES
# -----------------------
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

# -----------------------
# INSERT HOSPITALS
# -----------------------
hospitals = [
    ('Bengaluru Vet Clinic','+91-80-1111-0001', 12.9716, 77.5946, 'Main Street, Bengaluru'),
    ('Whitefield Animal Care','+91-80-1111-0002', 12.9719, 77.7499, 'Whitefield'),
    ('Yelahanka Vet','+91-80-1111-0003', 13.0680, 77.5938, 'Yelahanka'),
    ('Mysore Road Clinic','+91-80-1111-0004', 12.2958, 76.6394, 'Mysore Road'),
    ('Vemana Vet Clinic','+91-80-1111-0007', 12.9297, 77.6224, 'Koramangala')
]

for h in hospitals:
    c.execute('INSERT INTO hospitals (name, phone, lat, lon, address) VALUES (?, ?, ?, ?, ?)', h)

# -----------------------
# INSERT COWS
# -----------------------
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

# -----------------------
# GENERATE QR CODES
# -----------------------
os.makedirs('qrcodes', exist_ok=True)

conn = sqlite3.connect(DB)
cur = conn.cursor()
cur.execute('SELECT id FROM cows')
rows = cur.fetchall()

# Auto-created base URL using detected IP
base = f'http://{local_ip}:5000/report/{{}}'

print("Using base URL for QR codes:", base)

for r in rows:
    cowid = r[0]
    url = base.format(cowid)
    img = qrcode.make(url)
    img.save(os.path.join('qrcodes', f'cow_{cowid}.png'))

print('Database initialized and QR codes generated in qrcodes/')
conn.close()
