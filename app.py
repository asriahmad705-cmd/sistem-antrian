from flask import Flask, render_template, request, jsonify, redirect, url_for
import mysql.connector
from datetime import datetime
import os

app = Flask(__name__)

# =============================================
# KONFIGURASI DATABASE - RAILWAY ENV VARIABLE
# =============================================
def get_db():
    return mysql.connector.connect(
        host=os.environ.get("MYSQLHOST", "localhost"),
        user=os.environ.get("MYSQLUSER", "root"),
        password=os.environ.get("MYSQLPASSWORD", ""),
        database=os.environ.get("MYSQLDATABASE", "db_antrian"),
        port=int(os.environ.get("MYSQLPORT", 3306)),
    )

# =============================================
# HALAMAN UTAMA - FORM PENDAFTARAN
# =============================================
@app.route("/")
def index():
    return render_template("index.html")

# =============================================
# PROSES PENDAFTARAN
# =============================================
@app.route("/daftar", methods=["POST"])
def daftar():
    nama = request.form.get("nama", "").strip()
    keperluan = request.form.get("keperluan", "").strip()
    no_hp = request.form.get("no_hp", "").strip()

    if not nama or not keperluan:
        return jsonify({"status": "error", "pesan": "Nama dan keperluan wajib diisi!"}), 400

    try:
        db = get_db()
        cursor = db.cursor()

        hari_ini = datetime.now().date()
        cursor.execute(
            "SELECT COUNT(*) FROM antrian WHERE DATE(waktu_daftar) = %s",
            (hari_ini,)
        )
        jumlah = cursor.fetchone()[0]
        nomor_antrian = jumlah + 1

        cursor.execute(
            """INSERT INTO antrian (nama, keperluan, no_hp, nomor_antrian, status, waktu_daftar)
               VALUES (%s, %s, %s, %s, 'menunggu', NOW())""",
            (nama, keperluan, no_hp, nomor_antrian)
        )
        db.commit()
        id_baru = cursor.lastrowid
        cursor.close()
        db.close()

        return jsonify({
            "status": "ok",
            "nomor_antrian": nomor_antrian,
            "nama": nama,
            "keperluan": keperluan,
            "id": id_baru
        })

    except Exception as e:
        return jsonify({"status": "error", "pesan": str(e)}), 500

# =============================================
# HALAMAN ADMIN
# =============================================
@app.route("/admin")
def admin():
    return render_template("admin.html")

# =============================================
# API: AMBIL DATA ANTRIAN
# =============================================
@app.route("/api/antrian")
def api_antrian():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        hari_ini = datetime.now().date()
        cursor.execute(
            """SELECT * FROM antrian
               WHERE DATE(waktu_daftar) = %s
               ORDER BY nomor_antrian ASC""",
            (hari_ini,)
        )
        data = cursor.fetchall()
        for row in data:
            if row.get("waktu_daftar"):
                row["waktu_daftar"] = row["waktu_daftar"].strftime("%H:%M:%S")
            if row.get("waktu_dipanggil"):
                row["waktu_dipanggil"] = row["waktu_dipanggil"].strftime("%H:%M:%S")
        cursor.close()
        db.close()
        return jsonify(data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =============================================
# API: PANGGIL ANTRIAN BERIKUTNYA
# =============================================
@app.route("/api/panggil", methods=["POST"])
def panggil():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        hari_ini = datetime.now().date()

        cursor.execute(
            """SELECT * FROM antrian
               WHERE DATE(waktu_daftar) = %s AND status = 'menunggu'
               ORDER BY nomor_antrian ASC LIMIT 1""",
            (hari_ini,)
        )
        antrian = cursor.fetchone()

        if not antrian:
            cursor.close()
            db.close()
            return jsonify({"status": "kosong", "pesan": "Tidak ada antrian yang menunggu"})

        cursor.execute(
            "UPDATE antrian SET status='dipanggil', waktu_dipanggil=NOW() WHERE id=%s",
            (antrian["id"],)
        )
        db.commit()
        cursor.close()
        db.close()

        return jsonify({
            "status": "ok",
            "nomor_antrian": antrian["nomor_antrian"],
            "nama": antrian["nama"],
            "keperluan": antrian["keperluan"]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =============================================
# API: SELESAIKAN ANTRIAN
# =============================================
@app.route("/api/selesai/<int:id>", methods=["POST"])
def selesai(id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE antrian SET status='selesai' WHERE id=%s", (id,)
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =============================================
# API: HAPUS / SKIP ANTRIAN
# =============================================
@app.route("/api/hapus/<int:id>", methods=["POST"])
def hapus(id):
    try:
        db = get_db()
        cursor = db.cursor()
        cursor.execute(
            "UPDATE antrian SET status='dilewati' WHERE id=%s", (id,)
        )
        db.commit()
        cursor.close()
        db.close()
        return jsonify({"status": "ok"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# =============================================
# API: STATUS ANTRIAN (untuk monitor publik)
# =============================================
@app.route("/api/status")
def status():
    try:
        db = get_db()
        cursor = db.cursor(dictionary=True)
        hari_ini = datetime.now().date()

        cursor.execute(
            "SELECT * FROM antrian WHERE DATE(waktu_daftar)=%s AND status='dipanggil' ORDER BY waktu_dipanggil DESC LIMIT 1",
            (hari_ini,)
        )
        dipanggil = cursor.fetchone()

        cursor.execute(
            "SELECT COUNT(*) as total FROM antrian WHERE DATE(waktu_daftar)=%s AND status='menunggu'",
            (hari_ini,)
        )
        menunggu = cursor.fetchone()["total"]

        cursor.close()
        db.close()

        return jsonify({
            "sedang_dipanggil": {
                "nomor": dipanggil["nomor_antrian"] if dipanggil else None,
                "nama": dipanggil["nama"] if dipanggil else None,
            },
            "menunggu": menunggu
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=5000)
