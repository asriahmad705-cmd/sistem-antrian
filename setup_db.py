"""
Jalankan file ini SEKALI setelah deploy untuk membuat tabel.
Di Railway: buka Railway Shell lalu ketik -> python setup_db.py
"""

import mysql.connector
import os

try:
    conn = mysql.connector.connect(
        host=os.environ.get("MYSQLHOST", "localhost"),
        user=os.environ.get("MYSQLUSER", "root"),
        password=os.environ.get("MYSQLPASSWORD", ""),
        database=os.environ.get("MYSQLDATABASE", "db_antrian"),
        port=int(os.environ.get("MYSQLPORT", 3306)),
    )
    cursor = conn.cursor()

    # Buat tabel antrian
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS antrian (
            id              INT AUTO_INCREMENT PRIMARY KEY,
            nomor_antrian   INT NOT NULL,
            nama            VARCHAR(100) NOT NULL,
            keperluan       VARCHAR(200) NOT NULL,
            no_hp           VARCHAR(20),
            status          ENUM('menunggu','dipanggil','selesai','dilewati') DEFAULT 'menunggu',
            waktu_daftar    DATETIME,
            waktu_dipanggil DATETIME
        )
    """)

    conn.commit()
    cursor.close()
    conn.close()

    print("=" * 45)
    print("  Tabel berhasil dibuat!")
    print("  Aplikasi siap digunakan.")
    print("=" * 45)

except mysql.connector.Error as e:
    print(f"\n[ERROR] Gagal konek ke MySQL: {e}")
