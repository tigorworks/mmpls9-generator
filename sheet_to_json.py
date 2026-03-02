import pandas as pd
import json
import os
from ftplib import FTP_TLS
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# GOOGLE SHEET CONFIG
# =========================
sheet_id = "1RSHx8uxaW4qhrVAaeiJNmbuZAVyxlmQR_VSoOeirmBs"
csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

# =========================
# FTP CONFIG (FROM ENV)
# =========================
FTP_HOST = "ftp.dunuw.com"
FTP_USER = "mmpls9@dunuw.com"
FTP_PASS = os.getenv("FTP_PASS")
FTP_PORT = 21
REMOTE_FILE = "mmpl.json"

if not FTP_PASS:
    raise ValueError("FTP_PASS environment variable not set")

def has_value(val):
    if pd.isna(val):
        return False
    if isinstance(val, str) and val.strip() == "":
        return False
    return True

print("Fetching Google Sheet...")

try:
    df = pd.read_csv(csv_url)
except Exception as e:
    raise RuntimeError(f"Gagal membaca Google Sheet: {e}")

# =========================
# VALIDATION
# =========================

df = df.dropna(how="all")

if df.empty:
    raise ValueError("Sheet hanya berisi header atau kosong. Upload dibatalkan.")

required_columns = [
    "Nama Team",
    "Nama Kapten",
    "Email Kapten",
    "No Whatsapp Kapten",
    "Logo Team",
    "Berkas ID Card",
    "Nama Lengkap",
    "NIP",
    "Nick In-Game",
    "ID Game"
]

missing = [col for col in required_columns if col not in df.columns]
if missing:
    raise ValueError(f"Kolom wajib tidak ditemukan: {missing}")

teams = []

for _, row in df.iterrows():

    if pd.isna(row["Nama Team"]) or str(row["Nama Team"]).strip() == "":
        continue

    members = []

    for i in range(1, 11):
        if i == 1:
            nama_col = "Nama Lengkap"
            nip_col = "NIP"
            nick_col = "Nick In-Game"
            game_id_col = "ID Game"
        else:
            nama_col = f"Nama Lengkap {i}"
            nip_col = f"NIP {i}"
            nick_col = f"Nick In-Game {i}"
            game_id_col = f"ID Game {i}"

        full_name = row.get(nama_col)

        if pd.isna(full_name) or str(full_name).strip() == "":
            continue

        member = {
            "full_name": str(full_name).strip(),
            "nip": str(row.get(nip_col, "")).strip(),
            "join from": None,
            "game_id": str(row.get(game_id_col, "")).strip(),
            "game_nick": str(row.get(nick_col, "")).strip()
        }

        members.append(member)

    if not members:
        continue

    team = {
        "team_name": str(row["Nama Team"]).strip(),
        "captain_name": str(row["Nama Kapten"]).strip(),
        "captain_whatsapp": str(row["No Whatsapp Kapten"]).strip(),
        "captain_email": str(row["Email Kapten"]).strip(),
        "logo": has_value(row["Logo Team"]),
        "idcard": has_value(row["Berkas ID Card"]),
        "members": members
    }

    teams.append(team)

if not teams:
    raise ValueError("Tidak ada tim valid ditemukan. Upload dibatalkan.")

# =========================
# LAST UPDATE (Asia/Jakarta)
# =========================
jakarta_time = datetime.now(ZoneInfo("Asia/Jakarta"))
last_update = jakarta_time.strftime("%Y-%m-%d %H:%M:%S")

final_json = {
    "lastupdate": last_update,
    "teams": teams
}

local_file = "mmpl.json"

with open(local_file, "w", encoding="utf-8") as f:
    json.dump(final_json, f, indent="\t", ensure_ascii=False)

print("JSON generated successfully")

# =========================
# UPLOAD VIA FTPS
# =========================
print("Uploading via FTPS...")

try:
    ftps = FTP_TLS()
    ftps.connect(FTP_HOST, FTP_PORT)
    ftps.login(FTP_USER, FTP_PASS)
    ftps.prot_p()

    with open(local_file, "rb") as f:
        ftps.storbinary(f"STOR {REMOTE_FILE}", f)

    ftps.quit()

    print("Upload successful ✅")

except Exception as e:
    raise RuntimeError(f"Upload FTPS gagal: {e}")
