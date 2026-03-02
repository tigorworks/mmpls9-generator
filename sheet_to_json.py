import pandas as pd
import json
from datetime import datetime
from zoneinfo import ZoneInfo

# =========================
# GOOGLE SHEET CONFIG
# =========================
sheet_id = "1RSHx8uxaW4qhrVAaeiJNmbuZAVyxlmQR_VSoOeirmBs"
csv_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"

print("Fetching Google Sheet...")

try:
    df = pd.read_csv(csv_url)
except Exception as e:
    raise RuntimeError(f"Gagal membaca Google Sheet: {e}")

# Drop baris kosong total
df = df.dropna(how="all")

if df.empty:
    raise ValueError("Sheet hanya berisi header atau kosong. Generate dibatalkan.")

def has_value(val):
    if pd.isna(val):
        return False
    if isinstance(val, str) and val.strip() == "":
        return False
    return True

# Validasi kolom minimal
required_columns = [
    "Nama Team",
    "Nama Kapten",
    "Email Kapten",
    "No Whatsapp",
]

missing = [col for col in required_columns if col not in df.columns]
if missing:
    raise ValueError(f"Kolom wajib tidak ditemukan: {missing}")

# =========================
# DETEKSI KOLOM MEMBER DINAMIS
# =========================

name_cols = [c for c in df.columns if c.startswith("Nama Lengkap")]
nip_cols = [c for c in df.columns if c.startswith("NIP")]
nick_cols = [c for c in df.columns if "Nick" in c]
game_id_cols = [c for c in df.columns if "ID Game" in c]

if not name_cols:
    raise ValueError("Tidak ditemukan kolom Nama Lengkap.")

teams = []

for _, row in df.iterrows():

    if pd.isna(row["Nama Team"]) or str(row["Nama Team"]).strip() == "":
        continue

    members = []

    max_member = max(len(name_cols), len(nip_cols), len(nick_cols), len(game_id_cols))

    for i in range(max_member):

        if i >= len(name_cols):
            continue

        full_name = row.get(name_cols[i])

        if pd.isna(full_name) or str(full_name).strip() == "":
            continue

        nip_val = row.get(nip_cols[i]) if i < len(nip_cols) else ""
        nick_val = row.get(nick_cols[i]) if i < len(nick_cols) else ""
        game_id_val = row.get(game_id_cols[i]) if i < len(game_id_cols) else ""

        member = {
            "full_name": str(full_name).strip(),
            "nip": str(nip_val).strip(),
            "join from": None,
            "game_id": str(game_id_val).strip(),
            "game_nick": str(nick_val).strip()
        }

        members.append(member)

    if not members:
        continue

    team = {
        "team_name": str(row["Nama Team"]).strip(),
        "captain_name": str(row["Nama Kapten"]).strip(),
        "captain_whatsapp": str(row["No Whatsapp"]).strip(),
        "captain_email": str(row["Email Kapten"]).strip(),
        "logo": has_value(row.get("Logo Team")),
        "idcard": has_value(row.get("Berkas ID Card")),
        "members": members
    }

    teams.append(team)

if not teams:
    raise ValueError("Tidak ada tim valid ditemukan. Generate dibatalkan.")

# =========================
# LAST UPDATE (Asia/Jakarta UTC+7)
# =========================
jakarta_time = datetime.now(ZoneInfo("Asia/Jakarta"))
last_update = jakarta_time.strftime("%Y-%m-%d %H:%M:%S")

final_json = {
    "lastupdate": last_update,
    "teams": teams
}

# =========================
# SAVE LOCAL FILE
# =========================
with open("mmpl.json", "w", encoding="utf-8") as f:
    json.dump(final_json, f, indent="\t", ensure_ascii=False)

print("mmpl.json berhasil dibuat ✅")
