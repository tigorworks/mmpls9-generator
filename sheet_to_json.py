import pandas as pd
import json
import os
from ftplib import FTP_TLS

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
df = pd.read_csv(csv_url)

teams = []

for _, row in df.iterrows():
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

        if pd.isna(full_name):
            continue

        member = {
            "full_name": str(full_name),
            "nip": str(row.get(nip_col, "")),
            "join from": None,
            "game_id": str(row.get(game_id_col, "")),
            "game_nick": str(row.get(nick_col, ""))
        }

        members.append(member)

    team = {
        "team_name": row["Nama Team"],
        "captain_name": row["Nama Kapten"],
        "whatsapp_number": str(row["No Whatsapp"]),
        "logo": has_value(row["Logo Team"]),
        "idcard": has_value(row["Berkas ID Card"]),
        "members": members
    }

    teams.append(team)

final_json = {"teams": teams}

local_file = "mmpl.json"

with open(local_file, "w", encoding="utf-8") as f:
    json.dump(final_json, f, indent="\t", ensure_ascii=False)

print("JSON generated successfully")

print("Uploading via FTPS...")

ftps = FTP_TLS()
ftps.connect(FTP_HOST, FTP_PORT)
ftps.login(FTP_USER, FTP_PASS)
ftps.prot_p()

with open(local_file, "rb") as f:
    ftps.storbinary(f"STOR {REMOTE_FILE}", f)

ftps.quit()

print("Upload successful")
