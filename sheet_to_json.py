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
    # Semua kolom dipaksa string
    df = pd.read_csv(csv_url, dtype=str)
except Exception as e:
    raise RuntimeError(f"Gagal membaca Google Sheet: {e}")

# Hapus baris kosong total
df = df.dropna(how="all")

if df.empty:
    raise ValueError("Sheet hanya berisi header atau kosong. Generate dibatalkan.")

# =========================
# UTIL FUNCTION
# =========================

def clean(val):
    if val is None:
        return ""
    val = str(val).strip()
    if val.lower() == "nan":
        return ""
    return val

def has_value(val):
    return clean(val) != ""

# =========================
# VALIDASI KOLOM MINIMAL
# =========================

required_columns = [
    "Nama Team",
    "Nama Kapten",
    "Email Kapten",
    "No Whatsapp"
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

# =========================
# PROSES DATA
# =========================

for _, row in df.iterrows():

    team_name = clean(row.get("Nama Team"))

    if team_name == "":
        continue

    members = []

    # Scan semua slot member (tidak break)
    for i in range(len(name_cols)):

        full_name = clean(row.get(name_cols[i]))

        # Kalau kosong → skip saja
        if full_name == "":
            continue

        nip_val = clean(row.get(nip_cols[i])) if i < len(nip_cols) else ""
        nick_val = clean(row.get(nick_cols[i])) if i < len(nick_cols) else ""
        game_id_val = clean(row.get(game_id_cols[i])) if i < len(game_id_cols) else ""

        member = {
            "full_name": full_name,
            "nip": nip_val,
            "join_from": None,
            "game_id": game_id_val,
            "game_nick": nick_val
        }

        members.append(member)

    # Skip tim tanpa member valid
    if not members:
        continue

    team = {
        "team_name": team_name,
        "captain_name": clean(row.get("Nama Kapten")),
        "captain_whatsapp": clean(row.get("No Whatsapp")),
        "captain_email": clean(row.get("Email Kapten")),
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
# SAVE FILE
# =========================

with open("mmpl.json", "w", encoding="utf-8") as f:
    json.dump(final_json, f, indent="\t", ensure_ascii=False)

print("mmpl.json berhasil dibuat ✅")
