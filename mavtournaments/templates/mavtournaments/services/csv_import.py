# mavtournaments/services/csv_import.py
import csv
import io

def parse_team_rows_from_bytes(file_bytes: bytes):
    text = file_bytes.decode("utf-8", errors="ignore")
    return parse_team_rows_from_text(text)

def parse_team_rows_from_text(text: str):
    rows = []

    # Try comma-CSV first: Team, user1, user2
    try:
        reader = csv.reader(io.StringIO(text))
        for raw in reader:
            if not raw or not (raw[0] or "").strip():
                continue
            team = raw[0].strip()
            usernames = [c.strip() for c in raw[1:] if (c or "").strip()]
            if team and usernames:
                rows.append({"team": team, "usernames": usernames})
    except Exception:
        pass

    # Fallback: "Team; user1,user2"
    if not rows:
        for line in text.splitlines():
            if ";" in line:
                left, right = line.split(";", 1)
                team = (left or "").strip()
                usernames = [u.strip() for u in (right or "").split(",") if u.strip()]
                if team and usernames:
                    rows.append({"team": team, "usernames": usernames})

    return rows
