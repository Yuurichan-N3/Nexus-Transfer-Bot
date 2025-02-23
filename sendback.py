import time
import requests
from web3 import Web3
import sys
from datetime import datetime
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from dataclasses import dataclass
from typing import Dict, List
import threading
import queue
import os
import asyncio
import json

# Setup logging hanya untuk transaksi
class LogTransaksi:
    def __init__(self):
        self.logs = []
        self.max_logs = 10
        self.kunci = threading.Lock()

    def tambah_log(self, pesan):
        with self.kunci:
            waktu = datetime.now().strftime("%H:%M:%S")
            log_baru = f"[{waktu}] - {pesan}"
            self.logs.append(log_baru)
            if len(self.logs) > self.max_logs:
                self.logs.pop(0)

    def dapatkan_logs(self):
        with self.kunci:
            return self.logs

log_transaksi = LogTransaksi()

@dataclass
class StatusWallet:
    alamat: str
    saldo: float
    ping_terakhir: datetime
    status: str
    percobaan: int
    kesalahan: List[str]

class BotTransferNexus:
    def __init__(self):
        self.konsol = Console()
        self.status_wallet: Dict[str, StatusWallet] = {}
        self.antrian_status = queue.Queue()
        self.kunci = threading.Lock()
        self.pembaruan_tabel_terakhir = 0
        self.INTERVAL_PEMBARUAN_TABEL = 5
        
        # Konfigurasi
        self.FILE_KUNCI_JSON = 'privatekeys.json'  # Sumber kunci pribadi pengirim
        self.WALLET_TUJUAN = '0xC9b1D27074B98f0c34b80875CbFA9783EbE770C8'  # Ganti dengan alamat penerima Anda
        self.URL_PING = 'https://nexus.rpc.caldera.xyz/http'
        self.SALDO_MINIMUM = 1.0
        self.JUMLAH_TRANSFER_MAKS = 0.001
        self.CADANGAN = 0.5
        self.INTERVAL_PING = 30
        self.DECIMAL_NEX = 18
        self.BATAS_GAS = 21000
        self.HARGA_GAS = Web3.to_wei('5', 'gwei')
        
        self.w3 = Web3(Web3.HTTPProvider(self.URL_PING))

    def muat_kunci_pribadi(self) -> List[str]:
        """Memuat kunci pribadi dari privatekeys.json"""
        try:
            if not os.path.exists(self.FILE_KUNCI_JSON):
                print(f"[ERROR] File kunci pribadi {self.FILE_KUNCI_JSON} tidak ditemukan!")
                return []
            with open(self.FILE_KUNCI_JSON, 'r') as file:
                kunci_dict = json.load(file)
                kunci = list(kunci_dict.values())  # Mengambil semua kunci pribadi
            if not kunci:
                print("[ERROR] Tidak ada kunci pribadi di file JSON!")
                return []
            print(f"[INFO] Memuat {len(kunci)} kunci pribadi dari {self.FILE_KUNCI_JSON}")
            return kunci
        except Exception as e:
            print(f"[ERROR] Gagal memuat kunci pribadi: {str(e)}")
            return []

    def perbarui_status_wallet(self, alamat: str, status: str, kesalahan: List[str]):
        with self.kunci:
            if alamat not in self.status_wallet:
                self.status_wallet[alamat] = StatusWallet(
                    alamat=alamat,
                    saldo=0.0,
                    ping_terakhir=datetime.now(),
                    status=status,
                    percobaan=0,
                    kesalahan=kesalahan
                )
            else:
                self.status_wallet[alamat].status = status
                self.status_wallet[alamat].kesalahan = kesalahan
                self.status_wallet[alamat].ping_terakhir = datetime.now()

    def buat_tabel_status(self) -> Table:
        tabel = Table(show_header=True, header_style="bold")
        tabel.add_column("Alamat", style="cyan")
        tabel.add_column("Saldo", justify="right", style="green")
        tabel.add_column("Status", style="bold")
        tabel.add_column("Ping Terakhir", style="blue")
        tabel.add_column("Percobaan", justify="right")
        
        with self.kunci:
            for status in self.status_wallet.values():
                tabel.add_row(
                    status.alamat[:8] + "...",
                    f"{status.saldo:.4f} NEX",
                    status.status,
                    status.ping_terakhir.strftime("%H:%M:%S"),
                    str(status.percobaan)
                )
        return tabel

    async def ping_wallet(self, wallet: str):
        alamat = self.w3.eth.account.from_key(wallet).address
        
        while True:
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "id": int(time.time()),
                    "method": "eth_getBalance",
                    "params": [alamat, "latest"]
                }
                respon = requests.post(self.URL_PING, json=payload, timeout=30)
                respon.raise_for_status()
                hasil = respon.json()
                
                if "result" in hasil:
                    saldo = int(hasil["result"], 16) / (10 ** self.DECIMAL_NEX)
                    
                    with self.kunci:
                        if alamat in self.status_wallet:
                            saldo_lama = self.status_wallet[alamat].saldo
                            self.status_wallet[alamat].saldo = saldo
                            self.status_wallet[alamat].percobaan += 1
                            self.status_wallet[alamat].status = "Aktif"
                            self.status_wallet[alamat].kesalahan = []
                    
                    if saldo != saldo_lama:
                        print(f"[INFO] Pembaruan saldo untuk {alamat[:8]}...: {saldo:.4f} NEX")
                    
                    if saldo >= self.SALDO_MINIMUM:
                        self.perbarui_status_wallet(alamat, "Mentransfer", [])
                        print(f"[INFO] Memulai transfer dari {alamat[:8]}...")
                        berhasil = await self.transfer_nex(wallet, saldo)
                        self.perbarui_status_wallet(alamat, "Terkirim" if berhasil else "Gagal", [])
                        
            except Exception as e:
                pesan_kesalahan = f"Ping gagal untuk {alamat[:8]}...: {str(e)}"
                print(f"[ERROR] {pesan_kesalahan}")
                self.perbarui_status_wallet(alamat, "Kesalahan", [pesan_kesalahan])
                
            await asyncio.sleep(self.INTERVAL_PING)

    async def transfer_nex(self, kunci_pribadi: str, saldo: float):
        try:
            akun = self.w3.eth.account.from_key(kunci_pribadi)
            nonce = self.w3.eth.get_transaction_count(akun.address)
            wallet_tujuan = self.WALLET_TUJUAN
            
            saldo_tersedia = saldo - self.CADANGAN
            if saldo_tersedia <= 0:
                pesan = f"Saldo tidak cukup untuk transfer dari {akun.address[:8]}..."
                print(f"[WARNING] {pesan}")
                log_transaksi.tambah_log(f"GAGAL: {pesan}")
                return False
            
            jumlah_kirim = min(saldo_tersedia, self.JUMLAH_TRANSFER_MAKS)
            jumlah_kirim_wei = int(jumlah_kirim * (10 ** self.DECIMAL_NEX))

            if jumlah_kirim_wei <= 0:
                pesan = f"Jumlah kirim terlalu kecil untuk {akun.address[:8]}..."
                print(f"[WARNING] {pesan}")
                log_transaksi.tambah_log(f"GAGAL: {pesan}")
                return False

            tx = {
                'nonce': nonce,
                'to': wallet_tujuan,
                'value': jumlah_kirim_wei,
                'gas': self.BATAS_GAS,
                'gasPrice': self.HARGA_GAS,
                'chainId': self.w3.eth.chain_id
            }

            tx_bertanda = self.w3.eth.account.sign_transaction(tx, kunci_pribadi)
            tx_hash = self.w3.eth.send_raw_transaction(tx_bertanda.raw_transaction)
            
            pesan = f"Berhasil transfer {jumlah_kirim:.4f} NEX dari {akun.address[:8]}... ke {wallet_tujuan[:8]}... TXID: {tx_hash.hex()}"
            print(f"[INFO] {pesan}")
            log_transaksi.tambah_log(f"BERHASIL: {pesan}")
            return True
            
        except Exception as e:
            pesan_kesalahan = f"Transfer gagal untuk {akun.address[:8]}...: {str(e)}"
            print(f"[ERROR] {pesan_kesalahan}")
            log_transaksi.tambah_log(f"GAGAL: {pesan_kesalahan}")
            return False

    async def kelola_tampilan_status(self):
        tata_letak = Layout()
        tata_letak.split(
            Layout(name="header", size=8),
            Layout(name="main", ratio=5),
            Layout(name="log", size=30)
        )
        spanduk = """
        🚀 BOT TRANSFER NEXUS    
    Transfer otomatis NEX ke wallet tujuan
    Dibuat Oleh : 佐賀県産（𝒀𝑼𝑷𝑹𝑰）🇯🇵 
"""
        panel_spanduk = Panel(
            spanduk,
            style="bold blue",
            expand=False,
            padding=(1, 1),
            title_align="center"
        )
        tata_letak["header"].update(panel_spanduk)

        with Live(tata_letak, console=self.konsol, refresh_per_second=1) as live:
            while True:
                waktu_sekarang = time.time()
                if waktu_sekarang - self.pembaruan_tabel_terakhir >= self.INTERVAL_PEMBARUAN_TABEL:
                    tabel = self.buat_tabel_status()
                    tata_letak["main"].update(tabel)
                    
                    logs = log_transaksi.dapatkan_logs()
                    log_teks = "\n".join(logs) if logs else "Belum ada transaksi"
                    tata_letak["log"].update(Panel(log_teks, title="Log Transaksi (Maks 10)", style="yellow"))
                    
                    self.pembaruan_tabel_terakhir = waktu_sekarang
                await asyncio.sleep(1)

    async def mulai(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        print("[INFO] Memulai Bot Transfer Nexus")
        
        self.kunci_pribadi = self.muat_kunci_pribadi()
        
        if not self.kunci_pribadi:
            print("[ERROR] Tidak ada kunci pribadi yang tersedia!")
            print(f"[INFO] Pastikan {self.FILE_KUNCI_JSON} berisi kunci pribadi untuk mengirim")
            sys.exit(1)
        
        # Validasi alamat tujuan
        if not Web3.is_address(self.WALLET_TUJUAN):
            print(f"[ERROR] Alamat tujuan {self.WALLET_TUJUAN} tidak valid!")
            sys.exit(1)
        
        for wallet in self.kunci_pribadi:
            alamat = self.w3.eth.account.from_key(wallet).address
            self.status_wallet[alamat] = StatusWallet(
                alamat=alamat,
                saldo=0.0,
                ping_terakhir=datetime.now(),
                status="Memulai",
                percobaan=0,
                kesalahan=[]
            )
        
        tugas_tampilan_status = asyncio.create_task(self.kelola_tampilan_status())
        await asyncio.sleep(1)
        
        tugas_wallet = [asyncio.create_task(self.ping_wallet(wallet)) for wallet in self.kunci_pribadi]
        await asyncio.gather(tugas_tampilan_status, *tugas_wallet)

if __name__ == "__main__":
    bot = BotTransferNexus()
    try:
        asyncio.run(bot.mulai())
    except KeyboardInterrupt:
        print("\n[INFO] Menutup Bot Transfer Nexus...")
        sys.exit(0)
