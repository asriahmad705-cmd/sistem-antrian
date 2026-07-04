import mysql.connector, os

try:
    conn = mysql.connector.connect(
        host=os.environ.get("MYSQLHOST", "localhost"),
        user=os.environ.get("MYSQLUSER", "root"),
        password=os.environ.get("MYSQLPASSWORD", ""),
        database=os.environ.get("MYSQLDATABASE", "railway"),
        port=int(os.environ.get("MYSQLPORT", 3306)),
    )
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservasi (
            id                  INT AUTO_INCREMENT PRIMARY KEY,
            nama                VARCHAR(100) NOT NULL,
            nik                 VARCHAR(20) NOT NULL,
            no_hp               VARCHAR(20) NOT NULL,
            alamat              TEXT NOT NULL,
            tipe_kamar          ENUM('standard','deluxe','suite','villa') NOT NULL,
            jumlah_tamu         INT NOT NULL,
            checkin             DATE NOT NULL,
            checkout            DATE NOT NULL,
            lama_menginap       INT NOT NULL,
            harga_per_malam     DECIMAL(12,2) NOT NULL,
            total_harga         DECIMAL(12,2) NOT NULL,
            metode_pembayaran   ENUM('cash','transfer','kartu_kredit','qris') DEFAULT 'cash',
            status_pembayaran   ENUM('belum_bayar','dp','lunas') DEFAULT 'belum_bayar',
            catatan             TEXT,
            waktu_reservasi     DATETIME
        )
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("=" * 45)
    print("  Tabel reservasi berhasil dibuat!")
    print("=" * 45)
except Exception as e:
    print(f"[ERROR] {e}")
