from flask import Flask, render_template, request, redirect, url_for, jsonify, send_from_directory
import sqlite3, os, math, json
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'uploads'
DB = 'herdsos.db'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit


def get_db_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def find_nearest_hospital(lat, lon, tried=[]):
    conn = get_db_conn()
    cur = conn.execute('SELECT * FROM hospitals')
    rows = cur.fetchall()
    choices = []
    for r in rows:
        if r['id'] in tried:
            continue
        d = haversine(lat, lon, r['lat'], r['lon'])
        choices.append((d, r['id']))
    conn.close()
    if not choices:
        return None
    choices.sort(key=lambda x: x[0])
    return choices[0][1]


@app.route('/')
def index():
    conn = get_db_conn()
    cows = conn.execute('SELECT * FROM cows').fetchall()
    conn.close()
    return render_template('index.html', cows=cows)


@app.route('/report/<int:cow_id>', methods=['GET'])
def report_form(cow_id):
    conn = get_db_conn()
    cow = conn.execute('SELECT * FROM cows WHERE id=?', (cow_id,)).fetchone()
    conn.close()
    if not cow:
        return 'Cow not found', 404
    return render_template('report.html', cow=cow)


@app.route('/submit_report', methods=['POST'])
def submit_report():
    cow_id = request.form.get('cow_id')
    condition = request.form.get('condition')
    lat = request.form.get('lat')
    lon = request.form.get('lon')
    photo = request.files.get('photo')

    photo_filename = None
    if photo and photo.filename:
        fn = secure_filename(photo.filename)
        photo_filename = f"{int(__import__('time').time())}_{fn}"
        photo.save(os.path.join(app.config['UPLOAD_FOLDER'], photo_filename))

    try:
        latf = float(lat)
        lonf = float(lon)
    except:
        latf = None
        lonf = None

    conn = get_db_conn()
    cur = conn.cursor()

    tried = []
    assigned = None

    if latf is not None and lonf is not None:
        assigned = find_nearest_hospital(latf, lonf, tried)

    cur.execute(
        'INSERT INTO reports (cow_id, condition, photo, lat, lon, assigned_hospital, tried_hospitals) VALUES (?, ?, ?, ?, ?, ?, ?)',
        (cow_id, condition, photo_filename, latf, lonf, assigned, json.dumps(tried))
    )
    conn.commit()
    report_id = cur.lastrowid
    conn.close()

    return redirect(url_for('thank_you', report_id=report_id))


@app.route('/thanks/<int:report_id>')
def thank_you(report_id):
    conn = get_db_conn()
    rep = conn.execute(
        'SELECT r.*, c.code as cow_code FROM reports r '
        'LEFT JOIN cows c ON c.id=r.cow_id WHERE r.id=?', 
        (report_id,)
    ).fetchone()
    conn.close()
    return render_template('thanks.html', rep=rep)


@app.route('/hospital/<int:hospital_id>')
def hospital_interface(hospital_id):
    conn = get_db_conn()
    hospital = conn.execute('SELECT * FROM hospitals WHERE id=?', (hospital_id,)).fetchone()
    reports = conn.execute(
        'SELECT * FROM reports WHERE assigned_hospital=? AND status="pending" ORDER BY timestamp DESC',
        (hospital_id,)
    ).fetchall()
    conn.close()
    return render_template('hospital.html', hospital=hospital, reports=reports)


@app.route('/hospital_action', methods=['POST'])
def hospital_action():
    action = request.form.get('action')
    report_id = int(request.form.get('report_id'))
    hospital_id = int(request.form.get('hospital_id'))

    conn = get_db_conn()
    cur = conn.cursor()

    rep = cur.execute('SELECT * FROM reports WHERE id=?', (report_id,)).fetchone()
    if not rep:
        conn.close()
        return 'Report not found', 404

    if action == 'accept':
        cur.execute('UPDATE reports SET status=? WHERE id=?', ('accepted', report_id))
        conn.commit()
        conn.close()
        return redirect(url_for('hospital_interface', hospital_id=hospital_id))

    elif action == 'reject':
        tried = []
        if rep['tried_hospitals']:
            try:
                tried = json.loads(rep['tried_hospitals'])
            except:
                tried = []

        tried.append(hospital_id)

        next_h = None
        if rep['lat'] is not None and rep['lon'] is not None:
            next_h = find_nearest_hospital(rep['lat'], rep['lon'], tried)

        if next_h is None:
            cur.execute(
                'UPDATE reports SET status=?, tried_hospitals=? WHERE id=?',
                ('unassigned', json.dumps(tried), report_id)
            )
        else:
            cur.execute(
                'UPDATE reports SET assigned_hospital=?, tried_hospitals=? WHERE id=?',
                (next_h, json.dumps(tried), report_id)
            )

        conn.commit()
        conn.close()
        return redirect(url_for('hospital_interface', hospital_id=hospital_id))

    conn.close()
    return 'Unknown action', 400


# UPDATED DASHBOARD FIX
@app.route('/dashboard')
def dashboard():
    conn = get_db_conn()

    reports_rows = conn.execute(
        'SELECT r.*, c.code as cow_code, h.name as hospital_name '
        'FROM reports r '
        'LEFT JOIN cows c ON c.id=r.cow_id '
        'LEFT JOIN hospitals h ON h.id=r.assigned_hospital '
        'ORDER BY r.timestamp DESC'
    ).fetchall()

    hospitals_rows = conn.execute('SELECT * FROM hospitals').fetchall()
    conn.close()

    reports = [dict(r) for r in reports_rows]
    hospitals = [dict(h) for h in hospitals_rows]

    return render_template('dashboard.html', reports=reports, hospitals=hospitals)


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

######################################
# NEW: API for hospital auto-refresh
######################################
@app.route("/api/hospital_reports/<int:hid>")
def api_hospital_reports(hid):
    conn = get_db_conn()
    cur = conn.cursor()
    rows = cur.execute("SELECT * FROM reports WHERE assigned_hospital=? AND status='pending'", (hid,)).fetchall()
    conn.close()

    return jsonify([dict(r) for r in rows])


######################################
# NEW: Hospital Accept
######################################
@app.route("/hospital_accept/<int:rid>")
def hospital_accept(rid):
    conn = get_db_conn()
    conn.execute("UPDATE reports SET status='accepted' WHERE id=?", (rid,))
    conn.commit()
    conn.close()

    return redirect(request.referrer)


######################################
# NEW: Hospital Reject (Forward to next nearest)
######################################
def find_next_nearest(lat, lon, tried_ids):
    conn = get_db_conn()
    cur = conn.cursor()
    hospitals = cur.execute("SELECT * FROM hospitals").fetchall()
    conn.close()

    best = None
    best_dist = 999999

    for h in hospitals:
        if str(h["id"]) in tried_ids:
            continue

        d = math.sqrt((lat - h["lat"])**2 + (lon - h["lon"])**2)
        if d < best_dist:
            best = h
            best_dist = d

    return best


@app.route("/hospital_reject/<int:rid>/<int:hid>")
def hospital_reject(rid, hid):
    conn = get_db_conn()
    cur = conn.cursor()

    r = cur.execute("SELECT * FROM reports WHERE id=?", (rid,)).fetchone()

    tried = r["tried_hospitals"].split(",") if r["tried_hospitals"] else []
    tried.append(str(hid))

    next_h = find_next_nearest(r["lat"], r["lon"], tried)

    if next_h:
        cur.execute("UPDATE reports SET assigned_hospital=?, tried_hospitals=? WHERE id=?", (next_h["id"], ",".join(tried), rid))
        conn.commit()

    conn.close()
    return redirect(request.referrer)


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
