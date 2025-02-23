# 🚀 Bot Transfer Nexus (Multi-Direction Wallet)

Dua skrip Python ini bekerja sama untuk mengotomatisasi transfer token NEX antar wallet Ethereum di jaringan Nexus. Skrip pertama (`bot.py`) membuat dan mengelola banyak wallet sumber, sementara skrip kedua (`sendback.py`) mengirim kembali token ke wallet utama. Ini berguna untuk mengatur aliran dana otomatis.

## 📂 Struktur Proyek
├── bot.py               # Membuat wallet baru, memantau saldo, dan mentransfer token

├── sendback.py          # Mengembalikan token dari wallet ke wallet utama

├── PrivateKeys.txt      # File untuk menyimpan kunci pribadi secara manual

├── wallets.txt          # Daftar alamat wallet tujuan

├── privatekeys.json     # Kunci pribadi yang dibuat secara otomatis



## ⚙️ Fitur Utama

### `bot.py`:
- Membuat wallet baru dan menyimpan kunci pribadi.
- Memantau saldo wallet secara real-time.
- Mengirim token ke daftar wallet tujuan jika saldo mencukupi.
- Mengatur saldo minimum dan cadangan untuk keamanan transaksi.
- Menampilkan status dan log transaksi secara live di terminal.

### `sendback.py`:
- Mengambil kunci pribadi dari `privatekeys.json`.
- Mengembalikan token ke wallet utama jika saldo mencukupi.
- Memantau saldo secara periodik dan otomatis menginisiasi transfer.

## 🛠️ Instalasi

1. Kloning repositori ini

```
git clone https://github.com/yuurichan-N3/Nexus-Transfer-Bot.git
cd Nexus-Transfer-Bot
```


2. Pasang dependensi: Pastikan Python 3.9+ sudah terinstal.

```
pip install -r requirements.txt
```


3. Siapkan file konfigurasi:
- Buat `PrivateKeys.txt` untuk menyimpan kunci pribadi (jika ada).
- Isi `wallets.txt` dengan daftar alamat tujuan. (dikelola otomatis oleh skrip).
- Pastikan `privatekeys.json` ada untuk mengembalikan token (dikelola otomatis oleh skrip).

## 🚀 Cara Menggunakan

1. Menjalankan `bot.py` (mengirim token ke banyak wallet):

```
python bot.py
```


2. Menjalankan `sendback.py` (mengembalikan token ke wallet utama):

```
python sendback.py
```


3. Proses transfer otomatis:
- `bot.py` akan terus memantau saldo wallet sumber dan mengirim token ke wallet tujuan.
- `sendback.py` akan memeriksa saldo wallet tujuan dan mengembalikan token ke wallet utama jika ada kelebihan.

## 🔧 Konfigurasi Penting

Di dalam skrip, Anda bisa mengatur parameter berikut:

### `bot.py`:
- `SALDO_MINIMUM`: Saldo minimum untuk menginisiasi transfer.
- `JUMLAH_TRANSFER_MAKS`: Jumlah maksimum token yang dikirim dalam sekali transfer.
- `INTERVAL_PING`: Waktu jeda untuk memeriksa saldo wallet.

### `sendback.py`:
- `WALLET_TUJUAN`: Alamat wallet utama untuk menerima pengembalian token.
- `JUMLAH_TRANSFER_MAKS`: Batas jumlah token yang dikirim balik ke wallet utama.

## 👀 Tampilan Terminal

Saat bot berjalan, Anda akan melihat tabel status wallet dan log transaksi secara real-time berkat pustaka `Rich`.

## ⚠️ Catatan Penting

- Pastikan jaringan RPC yang digunakan (`https://rpc.nexus.xyz/http`) aktif.
- Jangan bagikan kunci pribadi Anda! Pastikan file kunci hanya bisa diakses oleh Anda.


---


## 📜 Lisensi  

Script ini didistribusikan untuk keperluan pembelajaran dan pengujian. Penggunaan di luar tanggung jawab pengembang.  

Untuk update terbaru, bergabunglah di grup **Telegram**: [Klik di sini](https://t.me/sentineldiscus).


---

## 💡 Disclaimer
Penggunaan bot ini sepenuhnya tanggung jawab pengguna. Kami tidak bertanggung jawab atas penyalahgunaan skrip ini.
