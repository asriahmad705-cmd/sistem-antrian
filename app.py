from flask import Flask, render_template, request, jsonify
from datetime import datetime
import mysql.connector
import os

app = Flask(__name__)

def get_db():
    return mysql.connector.connect(
        host=os.environ.get("MYSQLHOST", "localhost"),
        user=os.environ.get("MYSQLUSER", "root"),
        password=os.environ.get("MYSQLPASSWORD", ""),
        database=os.environ.get("MYSQLDATABASE", "railway"),
        port=int(os.environ.get("MYSQLPORT", 3306)),
    )

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/admin")
def admin():
    return render_template("admin.html")

@app.route("/laporan")
def laporan():
    return render_template("laporan.html")

# =============================================
# API: DAFTAR RESERVASI
# =============================================
@app.route("/api/reservasi", methods=["POST"])
def tambah_reservasi():
    data = request.json
    wajib = ["nama", "nik", "no_hp", "alamat", "tipe_kamar", "jumlah_tamu", "checkin", "checkout"]
    for field in wajib:
        if not data.get(field):
            return jsonify({"status": "error", "pesan": f"{field} wajib diisi!"}), 400
    try:
        db = get_db()
        cursor = db.cursor()
        checkin = datetime.strptime(data["checkin"], "%Y-%m-%d").date()
        checkout = datetime.strptime(data["checkout"], "%Y-%m-%d").date()
        lama_menginap = (checkout - checkin).days
        if lama_menginap <= 0:
            return jsonify({"status": "error", "pesan": "Tanggal checkout harus setelah checkin!"}), 400

        harga_per_malam = {"standard": 300000, "deluxe": 500000, "suite": 900000, "villa": 1500000}
        harga = harga_per_malam.get(data["tipe_kamar"], 300000)
        total_harga = harga * lama_menginap

        cursor.execute("""
            INSERT INTO reservasi (nama, nik, no_hp, alamat, tipe_kamar, jumlah_tamu,
            checkin, checkout, lama_menginap, harga_per_malam, total_harga,
            metode_pembayaran, status_pembayaran, catatan, waktu_reservasi)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,NOW())
        """, (
            data["nama"], data["nik"], data["no_hp"], data["alamat"],
            data["tipe_kamar"], data["jumlah_tamu"],
            checkin, checkout, lama_menginap, harga, total_harga,
            data.get("metode_pembayaran", "cash"),
            data.get("status_pembayaran", "belum_bayar"),
            data.get("catatan", "")
        ))
        db.commit()
        id_baru = cursor.lastrowid
        cursor.close()
        db.close()
        return jsonify({"status": "ok", "id": id_baru, "total_harga": total_harga, "lama_menginap": lama_menginap})
    except Exception as e:
        return jsonify({"status": "error", "pesan": str(e)}), 500

# =============================================
# API: AMBIL SEMUA RESERVASI
# =============================================
@app.route("/api/reservasi", methods=["GET"])
def get_reservasi():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM reservasi ORDER BY waktu_reservasi DESC")
        data = cursor.fetchall()
        for row in data:
            for key in ["checkin", "checkout", "waktu_reservasi"]:
                if row.get(key):
                    row[key] = str(row[key])
        cursor.close()
        db.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =============================================
# API: UPDATE STATUS
# =============================================
@app.route("/api/reservasi/<int:id>", methods=["PUT"])
def update_reservasi(id):
    data = request.json
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("""
            UPDATE reservasi SET status_pembayaran=%s, catatan=%s WHERE id=%s
        """, (data.get("status_pembayaran"), data.get("catatan"), id))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =============================================
# API: HAPUS RESERVASI
# =============================================
@app.route("/api/reservasi/<int:id>", methods=["DELETE"])
def hapus_reservasi(id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute("DELETE FROM reservasi WHERE id=%s", (id,))
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =============================================
# API: LAPORAN STATISTIK
# =============================================
@app.route("/api/laporan")
def api_laporan():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)

        # Total & pendapatan
        cursor.execute("""
            SELECT 
                COUNT(*) as total_reservasi,
                SUM(total_harga) as total_pendapatan,
                AVG(total_harga) as rata_pendapatan,
                MAX(total_harga) as transaksi_terbesar,
                MIN(total_harga) as transaksi_terkecil,
                SUM(lama_menginap) as total_malam,
                AVG(lama_menginap) as rata_menginap,
                AVG(jumlah_tamu) as rata_tamu
            FROM reservasi
        """)
        ringkasan = cursor.fetchone()

        # Per tipe kamar
        cursor.execute("""
            SELECT tipe_kamar,
                COUNT(*) as jumlah,
                SUM(total_harga) as pendapatan,
                AVG(lama_menginap) as rata_menginap
            FROM reservasi
            GROUP BY tipe_kamar
            ORDER BY pendapatan DESC
        """)
        per_kamar = cursor.fetchall()

        # Per metode pembayaran
        cursor.execute("""
            SELECT metode_pembayaran,
                COUNT(*) as jumlah,
                SUM(total_harga) as total
            FROM reservasi
            GROUP BY metode_pembayaran
        """)
        per_metode = cursor.fetchall()

        # Per status pembayaran
        cursor.execute("""
            SELECT status_pembayaran,
                COUNT(*) as jumlah,
                SUM(total_harga) as total
            FROM reservasi
            GROUP BY status_pembayaran
        """)
        per_status = cursor.fetchall()

        # Pendapatan per bulan
        cursor.execute("""
            SELECT DATE_FORMAT(checkin, '%Y-%m') as bulan,
                COUNT(*) as jumlah,
                SUM(total_harga) as pendapatan
            FROM reservasi
            GROUP BY bulan
            ORDER BY bulan DESC
            LIMIT 12
        """)
        per_bulan = cursor.fetchall()

        cursor.close()
        db.close()

        for key, val in (ringkasan or {}).items():
            if val is not None:
                ringkasan[key] = float(val)

        return jsonify({
            "ringkasan": ringkasan,
            "per_kamar": per_kamar,
            "per_metode": per_metode,
            "per_status": per_status,
            "per_bulan": per_bulan
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=5000)
