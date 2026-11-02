from flask import Flask, request, redirect, url_for, render_template_string, session
import sqlite3
from datetime import date, timedelta
from functools import wraps

app = Flask(__name__)
app.secret_key = "pharmastock_secret_key_2026"

DATABASE = "pharmastock.db"


# ---------------------------------------------------------------- DATABASE
def get_db():
    connection = sqlite3.connect(DATABASE)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_db()

    connection.execute("""
        CREATE TABLE IF NOT EXISTS medicines (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            expiry TEXT NOT NULL,
            minimum_stock INTEGER NOT NULL
        )
    """)

    # Remove duplicate names, keeping the oldest record.
    connection.execute("""
        DELETE FROM medicines
        WHERE id NOT IN (
            SELECT MIN(id)
            FROM medicines
            GROUP BY LOWER(TRIM(name))
        )
    """)

    # Prevent duplicate names, ignoring case and surrounding spaces.
    connection.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS unique_medicine_name
        ON medicines (LOWER(TRIM(name)))
    """)

    connection.commit()
    connection.close()


# ---------------------------------------------------------------- AUTH
def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


# ---------------------------------------------------------------- STYLES
STYLE = """
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    :root {
        --primary: #0f9d75;
        --primary-dark: #087f5b;
        --primary-soft: #e6f7f1;
        --ink: #0f172a;
        --muted: #64748b;
        --line: #e8edf3;
        --bg: #f4f7fb;
        --card: #ffffff;
        --red: #e03131;
        --red-soft: #fff0f0;
        --orange: #e67700;
        --orange-soft: #fff4e0;
        --blue: #1c7ed6;
        --blue-soft: #e7f1fd;
        --radius: 16px;
        --shadow: 0 4px 24px rgba(15, 23, 42, 0.06);
    }

    * { box-sizing: border-box; }

    body {
        margin: 0;
        font-family: 'Inter', system-ui, -apple-system, Segoe UI, Arial, sans-serif;
        color: var(--ink);
        background:
            radial-gradient(1000px 400px at 100% -10%, #d3f4e6 0%, transparent 60%),
            radial-gradient(800px 400px at -10% 0%, #dbeafe 0%, transparent 55%),
            var(--bg);
        min-height: 100vh;
    }

    a { color: var(--primary-dark); text-decoration: none; font-weight: 600; }

    /* ---------- top bar ---------- */
    .topbar {
        position: sticky; top: 0; z-index: 10;
        background: rgba(255, 255, 255, 0.85);
        backdrop-filter: blur(10px);
        border-bottom: 1px solid var(--line);
    }
    .topbar-inner {
        max-width: 1280px; margin: auto;
        padding: 14px 24px;
        display: flex; justify-content: space-between; align-items: center;
    }
    .brand { display: flex; align-items: center; gap: 12px; }
    .brand-logo {
        width: 42px; height: 42px; border-radius: 12px;
        background: linear-gradient(135deg, #12b886, #087f5b);
        display: grid; place-items: center;
        font-size: 22px;
        box-shadow: 0 6px 16px rgba(8, 127, 91, 0.35);
    }
    .brand h1 { margin: 0; font-size: 20px; font-weight: 800; letter-spacing: -0.3px; }
    .brand span { display: block; font-size: 12px; color: var(--muted); font-weight: 500; }

    .btn-logout {
        background: var(--red-soft); color: var(--red);
        padding: 9px 16px; border-radius: 10px; font-size: 14px;
        transition: all .2s;
    }
    .btn-logout:hover { background: var(--red); color: white; }

    /* ---------- layout ---------- */
    .wrapper { max-width: 1280px; margin: auto; padding: 28px 24px 50px; }

    .hero { margin-bottom: 22px; }
    .hero h2 { margin: 0 0 4px; font-size: 26px; letter-spacing: -0.5px; }
    .hero p { margin: 0; color: var(--muted); }

    .message {
        background: var(--primary-soft); color: var(--primary-dark);
        border: 1px solid #b7ead7; border-left: 5px solid var(--primary);
        padding: 14px 18px; border-radius: 12px; margin-bottom: 22px;
        font-weight: 500;
        animation: slide .4s ease;
    }
    @keyframes slide { from { opacity: 0; transform: translateY(-8px);} to { opacity: 1; transform: none; } }

    /* ---------- stat cards ---------- */
    .cards {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(210px, 1fr));
        gap: 18px; margin-bottom: 26px;
    }
    .stat {
        background: var(--card); border-radius: var(--radius);
        padding: 20px; box-shadow: var(--shadow);
        border: 1px solid var(--line);
        display: flex; align-items: center; gap: 16px;
        transition: transform .2s, box-shadow .2s;
    }
    .stat:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(15, 23, 42, 0.1); }
    .stat-icon {
        width: 54px; height: 54px; border-radius: 14px;
        display: grid; place-items: center; font-size: 26px;
    }
    .stat.green .stat-icon { background: var(--primary-soft); }
    .stat.red .stat-icon { background: var(--red-soft); }
    .stat.orange .stat-icon { background: var(--orange-soft); }
    .stat.blue .stat-icon { background: var(--blue-soft); }
    .stat p { margin: 0; color: var(--muted); font-size: 13px; font-weight: 600; }
    .stat h3 { margin: 2px 0 0; font-size: 30px; letter-spacing: -1px; }

    /* ---------- panels ---------- */
    .panel {
        background: var(--card); border-radius: var(--radius);
        padding: 24px; box-shadow: var(--shadow);
        border: 1px solid var(--line); margin-bottom: 26px;
    }
    .panel-head {
        display: flex; justify-content: space-between; align-items: center;
        flex-wrap: wrap; gap: 14px; margin-bottom: 18px;
    }
    .panel-head h2 { margin: 0; font-size: 19px; letter-spacing: -0.3px; }

    /* ---------- forms ---------- */
    label { display: block; font-size: 12px; font-weight: 600; color: var(--muted); margin-bottom: 6px; }

    input[type=text], input[type=password], input[type=number], input[type=date] {
        width: 100%;
        padding: 11px 14px;
        border: 1.5px solid var(--line);
        border-radius: 10px;
        font-size: 14px; font-family: inherit;
        background: #fbfcfe; color: var(--ink);
        transition: all .2s;
    }
    input:focus {
        outline: none; border-color: var(--primary);
        background: white; box-shadow: 0 0 0 4px rgba(18, 184, 134, 0.15);
    }

    .add-form {
        display: grid;
        grid-template-columns: 2fr 1fr 1.3fr 1fr auto;
        gap: 14px; align-items: end;
    }

    button, .btn {
        font-family: inherit; font-size: 14px; font-weight: 600;
        padding: 11px 20px; border: none; border-radius: 10px;
        cursor: pointer; color: white;
        background: linear-gradient(135deg, #12b886, #087f5b);
        box-shadow: 0 4px 12px rgba(8, 127, 91, 0.25);
        transition: all .2s;
    }
    button:hover { transform: translateY(-1px); box-shadow: 0 8px 18px rgba(8, 127, 91, 0.3); }
    button:active { transform: translateY(0); }

    .btn-delete {
        background: var(--red-soft); color: var(--red);
        box-shadow: none; padding: 9px 14px;
    }
    .btn-delete:hover { background: var(--red); color: white; box-shadow: none; }

    .btn-light {
        background: var(--primary-soft); color: var(--primary-dark);
        box-shadow: none; padding: 10px 16px;
    }
    .btn-light:hover { background: #cdeee0; box-shadow: none; }

    /* ---------- search ---------- */
    .search-form { display: flex; gap: 10px; align-items: center; flex-wrap: wrap; }
    .search-form input { width: 280px; max-width: 100%; }

    /* ---------- table ---------- */
    .table-wrap { overflow-x: auto; border-radius: 12px; border: 1px solid var(--line); }
    table { width: 100%; border-collapse: collapse; min-width: 880px; }
    thead th {
        background: #065f46;
        color: #ffffff;
        font-size: 12px;
        text-transform: uppercase;
        letter-spacing: 0.6px;
        padding: 14px 16px;
        text-align: left;
        font-weight: 700;
        border-bottom: 1px solid #064e3b;
    }
    tbody td {
        padding: 16px; border-bottom: 1px solid var(--line);
        vertical-align: middle; font-size: 14px;
    }
    tbody tr:last-child td { border-bottom: none; }
    tbody tr { transition: background .15s; }
    tbody tr:hover { background: #f9fcfb; }

    .sl-no { color: #000; font-weight: bold; }

    .med-name { display: inline-flex; align-items: center; gap: 12px; font-weight: 600; background-color: #d1fae5; color: #065f46; padding: 8px 12px; border-radius: 8px; }
    .med-icon {
        width: 38px; height: 38px; border-radius: 10px;
        background: var(--primary-soft);
        display: grid; place-items: center; font-size: 18px; flex-shrink: 0;
    }

    .stock-bar { width: 110px; height: 6px; background: #edf1f5; border-radius: 10px; margin-top: 6px; overflow: hidden; }
    .stock-bar span { display: block; height: 100%; border-radius: 10px; }

    /* ---------- badges ---------- */
    .badge {
        display: inline-flex; align-items: center; gap: 6px;
        padding: 6px 12px; border-radius: 999px;
        font-size: 12px; font-weight: 700; white-space: nowrap;
    }
    .badge::before { content: ''; width: 7px; height: 7px; border-radius: 50%; background: currentColor; }
    .badge.expired { background: var(--red-soft); color: var(--red); }
    .badge.low { background: var(--red-soft); color: var(--red); }
    .badge.warning { background: var(--orange-soft); color: var(--orange); }
    .badge.available { background: var(--primary-soft); color: var(--primary-dark); }

    /* ---------- edit (expands inside the row, never floats) ---------- */
    details.edit { position: static; min-width: 110px; }
    details.edit summary {
        list-style: none; cursor: pointer; display: inline-block;
        background: var(--blue-soft); color: var(--blue);
        padding: 9px 14px; border-radius: 10px; font-weight: 600; font-size: 14px;
        transition: all .2s;
    }
    details.edit summary::-webkit-details-marker { display: none; }
    details.edit summary:hover { background: var(--blue); color: white; }
    details.edit[open] summary { background: var(--blue); color: white; }

    .edit-form {
        position: static;
        width: 230px; margin-top: 12px; padding: 16px;
        background: white; border-radius: 14px; border: 1px solid var(--line);
        box-shadow: var(--shadow);
        animation: slide .2s ease;
    }
    .edit-form div { margin-bottom: 12px; }
    .edit-form button { width: 100%; }

    .empty { text-align: center; padding: 50px 20px !important; color: var(--muted); }
    .empty .big { font-size: 44px; display: block; margin-bottom: 8px; }

    .footer { text-align: center; color: var(--muted); font-size: 13px; margin-top: 10px; }

    /* ---------- login ---------- */
    .login-page {
        min-height: 100vh; display: grid; place-items: center; padding: 20px;
    }
    .login-box {
        width: 100%; max-width: 410px; background: white;
        padding: 38px 34px; border-radius: 22px;
        box-shadow: 0 25px 60px rgba(15, 23, 42, 0.14);
        border: 1px solid var(--line); text-align: center;
        animation: slide .5s ease;
    }
    .login-box .brand-logo { margin: 0 auto 16px; width: 62px; height: 62px; font-size: 32px; border-radius: 18px; }
    .login-box h1 { margin: 0; font-size: 26px; letter-spacing: -0.5px; }
    .login-box > p { color: var(--muted); margin: 6px 0 26px; }
    .login-box form { text-align: left; }
    .login-box .field { margin-bottom: 16px; }
    .login-box button { width: 100%; padding: 13px; font-size: 15px; margin-top: 6px; }
    .error {
        background: var(--red-soft); color: var(--red);
        padding: 11px 14px; border-radius: 10px; margin-bottom: 18px;
        font-size: 14px; font-weight: 600; text-align: center;
    }

    /* ---------- responsive ---------- */
    @media (max-width: 960px) {
        .add-form { grid-template-columns: 1fr 1fr; }
        .add-form button { grid-column: 1 / -1; }
    }
    @media (max-width: 560px) {
        .wrapper { padding: 18px 14px 40px; }
        .topbar-inner { padding: 12px 14px; }
        .add-form { grid-template-columns: 1fr; }
        .search-form input { width: 100%; }
        .brand span { display: none; }
    }
</style>
"""


# ---------------------------------------------------------------- MAIN PAGE
HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PharmaStock | Dashboard</title>
    {{ style|safe }}
</head>
<body>

<div class="topbar">
    <div class="topbar-inner">
        <div class="brand">
            <div class="brand-logo">💊</div>
            <div>
                <h1>PharmaStock</h1>
                <span>Medicine Inventory Monitoring System</span>
            </div>
        </div>
        <a href="/logout" class="btn-logout">⎋ Logout</a>
    </div>
</div>

<div class="wrapper">
    <div class="hero">
        <h2>Inventory Dashboard</h2>
        <p>Track stock levels and expiry dates at a glance.</p>
    </div>

    {% if message %}
        <div class="message">✓ {{ message }}</div>
    {% endif %}

    {% if low_stock > 0 %}
    <div class="message" style="background:#fff0f0; color:#c92a2a; border-color:#ffc9c9;">
        ⚠️ Low Stock Alert: {{ low_stock }} medicine(s) need restocking.
    </div>
    {% endif %}

    {% if expired > 0 %}
    <div class="message" style="background:#fff0f0; color:#c92a2a; border-color:#ffc9c9;">
        🚨 Expired Medicine Alert: {{ expired }} medicine(s) have expired.
    </div>
    {% endif %}

    {% if expiring > 0 %}
    <div class="message" style="background:#fff4e0; color:#b35c00; border-color:#ffd8a8;">
        ⏳ Expiry Alert: {{ expiring }} medicine(s) are expiring within 30 days.
    </div>
    {% endif %}

    <div class="cards">
        <div class="stat green">
            <div class="stat-icon">📦</div>
            <div><p>Total Medicines</p><h3>{{ medicines|length }}</h3></div>
        </div>
        <div class="stat red">
            <div class="stat-icon">📉</div>
            <div><p>Low Stock</p><h3>{{ low_stock }}</h3></div>
        </div>
        <div class="stat orange">
            <div class="stat-icon">⏳</div>
            <div><p>Expiry Warnings</p><h3>{{ expiring }}</h3></div>
        </div>
    </div>

    <div class="panel">
        <div class="panel-head">
            <h2>➕ Add New Medicine</h2>
        </div>
        <form action="/add" method="post" class="add-form">
            <div>
                <label>Medicine Name</label>
                <input type="text" name="name" placeholder="e.g. Paracetamol 500mg" required>
            </div>
            <div>
                <label>Quantity</label>
                <input type="number" name="quantity" placeholder="0" min="0" required>
            </div>
            <div>
                <label>Expiry Date</label>
                <input type="date" name="expiry" required>
            </div>
            <div>
                <label>Minimum Stock</label>
                <input type="number" name="minimum_stock" min="0" value="10" required>
            </div>
            <button type="submit">Add Medicine</button>
        </form>
    </div>

    <div class="panel">
        <div class="panel-head">
            <h2>📋 Medicine Inventory</h2>
            <form method="get" action="/" class="search-form">
                <input type="text" name="search" placeholder="🔍 Search medicine by name..." value="{{ search }}">
                <button type="submit">Search</button>
                {% if search %}<a href="/" class="btn btn-light">Show All</a>{% endif %}
            </form>
        </div>

        <div class="table-wrap">
            <table>
                <thead>
                    <tr>
                        <th>SL.NO</th>
                        <th>Medicine</th>
                        <th>Quantity</th>
                        <th>Expiry Date</th>
                        <th>Min. Stock</th>
                        <th>Stock Status</th>
                        <th>Expiry Status</th>
                        <th>Edit</th>
                        <th>Delete</th>
                    </tr>
                </thead>

                <tbody>
                    {% for medicine in medicines %}
                        {% set ratio = [100, (medicine['quantity'] / ([medicine['minimum_stock'] * 2, 1]|max) * 100)|int]|min %}

                        <tr>
                            <td class="sl-no">{{ loop.index }}</td>

                            <td>
                                <div class="med-name">
                                    <div class="med-icon">💊</div>
                                    {{ medicine['name'] }}
                                </div>
                            </td>

                            <td>
                                <strong>{{ medicine['quantity'] }}</strong>
                                <div class="stock-bar">
                                    <span style="
                                        width:{{ ratio }}%;
                                        background:
                                        {% if medicine['quantity'] <= medicine['minimum_stock'] %}#e03131
                                        {% elif ratio < 70 %}#f59f00
                                        {% else %}#12b886{% endif %};
                                    "></span>
                                </div>
                            </td>

                            <td>{{ medicine['expiry'] }}</td>
                            <td>{{ medicine['minimum_stock'] }}</td>

                            <td>
                                {% if medicine['quantity'] <= medicine['minimum_stock'] %}
                                    <span class="badge low">Low Stock</span>
                                {% else %}
                                    <span class="badge available">Available</span>
                                {% endif %}
                            </td>

                            <td>
                                {% if medicine['expiry'] < today %}
                                    <span class="badge expired">Expired</span>
                                {% elif medicine['expiry'] <= expiry_limit %}
                                    <span class="badge warning">Expiring Soon</span>
                                {% else %}
                                    <span class="badge available">Not Expired</span>
                                {% endif %}
                            </td>

                            <td>
                                <details class="edit">
                                    <summary>✏️ Edit</summary>

                                    <form class="edit-form"
                                          action="/edit/{{ medicine['id'] }}"
                                          method="post">

                                        <div>
                                            <label>Quantity</label>
                                            <input type="number" name="quantity"
                                                   value="{{ medicine['quantity'] }}" min="0" required>
                                        </div>

                                        <div>
                                            <label>Expiry Date</label>
                                            <input type="date" name="expiry"
                                                   value="{{ medicine['expiry'] }}" required>
                                        </div>

                                        <div>
                                            <label>Minimum Stock</label>
                                            <input type="number" name="minimum_stock"
                                                   value="{{ medicine['minimum_stock'] }}" min="0" required>
                                        </div>

                                        <button type="submit">Update Details</button>
                                    </form>
                                </details>
                            </td>

                            <td>
                                <form action="/delete/{{ medicine['id'] }}"
                                      method="post"
                                      onsubmit="return confirm('Delete this medicine?');">
                                    <button class="btn-delete" type="submit">🗑 Delete</button>
                                </form>
                            </td>
                        </tr>

                    {% else %}
                        <tr>
                            <td colspan="9" class="empty">
                                <span class="big">🩺</span>
                                {% if search %}
                                    No medicines found for "{{ search }}".
                                {% else %}
                                    No medicines yet. Add your first one above!
                                {% endif %}
                            </td>
                        </tr>
                    {% endfor %}
                </tbody>
            </table>
        </div>
    </div>

    <p class="footer">PharmaStock — Educational Project</p>
</div>

<script>
    // Remove ?message=... from the address bar so the banner doesn't come back on refresh.
    (function () {
        var url = new URL(window.location.href);
        if (url.searchParams.has("message")) {
            url.searchParams.delete("message");
            window.history.replaceState({}, "", url.pathname + url.search);
        }
    })();
</script>
</body>
</html>
"""


LOGIN_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PharmaStock | Login</title>
    {{ style|safe }}
</head>
<body>
    <div class="login-page">
        <div class="login-box">
            <div class="brand-logo">💊</div>
            <h1>PharmaStock</h1>
            <p>Sign in to manage your medicine inventory</p>

            {% if error %}
                <div class="error">⚠ {{ error }}</div>
            {% endif %}

            <form method="post">
                <div class="field">
                    <label>Username</label>
                    <input type="text" name="username" placeholder="Enter username" required autofocus>
                </div>
                <div class="field">
                    <label>Password</label>
                    <input type="password" name="password" placeholder="Enter password" required>
                </div>
                <button type="submit">Login →</button>
            </form>
        </div>
    </div>
</body>
</html>
"""


# ---------------------------------------------------------------- ROUTES
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")

        if username == "admin" and password == "admin123":
            session["logged_in"] = True
            return redirect(url_for("home"))

        error = "Invalid username or password!"

    return render_template_string(LOGIN_HTML, style=STYLE, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def home():
    today = date.today()
    expiry_limit = today + timedelta(days=30)

    connection = get_db()
    search = request.args.get("search", "").strip()

    if search:
        medicines = connection.execute(
            """
            SELECT * FROM medicines
            WHERE name LIKE ?
            ORDER BY id
            """,
            (f"%{search}%",)
        ).fetchall()
    else:
        medicines = connection.execute(
            "SELECT * FROM medicines ORDER BY id"
        ).fetchall()

    low_stock = connection.execute("""
        SELECT COUNT(*)
        FROM medicines
        WHERE quantity <= minimum_stock
    """).fetchone()[0]

    expiring = connection.execute("""
        SELECT COUNT(*)
        FROM medicines
        WHERE expiry >= ? AND expiry <= ?
    """, (
        today.isoformat(),
        expiry_limit.isoformat()
    )).fetchone()[0]

    expired = connection.execute("""
        SELECT COUNT(*)
        FROM medicines
        WHERE expiry < ?
    """, (today.isoformat(),)).fetchone()[0]

    connection.close()

    return render_template_string(
        HTML,
        style=STYLE,
        medicines=medicines,
        search=search,
        low_stock=low_stock,
        expiring=expiring,
        expired=expired,
        today=today.isoformat(),
        expiry_limit=expiry_limit.isoformat(),
        message=request.args.get("message", "")
    )


@app.route("/add", methods=["POST"])
@login_required
def add_medicine():
    name = request.form["name"].strip()
    expiry = request.form["expiry"]

    try:
        quantity = int(request.form["quantity"])
        minimum_stock = int(request.form["minimum_stock"])
        date.fromisoformat(expiry)
    except (ValueError, TypeError):
        return "Invalid medicine details.", 400

    if not name or quantity < 0 or minimum_stock < 0:
        return "Please enter valid medicine details.", 400

    connection = get_db()

    try:
        connection.execute("""
            INSERT INTO medicines
                (name, quantity, expiry, minimum_stock)
            VALUES (?, ?, ?, ?)
        """, (name, quantity, expiry, minimum_stock))
        connection.commit()
    except sqlite3.IntegrityError:
        connection.close()
        return redirect(url_for(
            "home",
            message="This medicine already exists. Please update its details instead."
        ))

    connection.close()
    return redirect(url_for("home", message="Medicine added successfully."))


@app.route("/edit/<int:medicine_id>", methods=["POST"])
@login_required
def edit_stock(medicine_id):
    expiry = request.form["expiry"]

    try:
        quantity = int(request.form["quantity"])
        minimum_stock = int(request.form["minimum_stock"])
        date.fromisoformat(expiry)
    except (ValueError, TypeError):
        return "Invalid medicine details.", 400

    if quantity < 0 or minimum_stock < 0:
        return "Values cannot be negative.", 400

    connection = get_db()
    connection.execute("""
        UPDATE medicines
        SET quantity = ?,
            expiry = ?,
            minimum_stock = ?
        WHERE id = ?
    """, (quantity, expiry, minimum_stock, medicine_id))
    connection.commit()
    connection.close()

    return redirect(url_for("home", message="Medicine details updated successfully."))


@app.route("/delete/<int:medicine_id>", methods=["POST"])
@login_required
def delete_medicine(medicine_id):
    connection = get_db()
    connection.execute("DELETE FROM medicines WHERE id = ?", (medicine_id,))
    connection.commit()
    connection.close()

    return redirect(url_for("home", message="Medicine deleted successfully."))


if __name__ == "__main__":
    initialize_database()
    app.run(host="0.0.0.0", port=5000, debug=False)