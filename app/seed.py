"""Creates clearly FAKE members and claims for testing. No real people or data."""
import random
from datetime import date, timedelta

from app.db import get_conn, init_db

random.seed(42)

FIRST = ["Ava", "Liam", "Maya", "Noah", "Zara", "Owen", "Isla", "Ravi", "Lena", "Omar",
         "Grace", "Theo", "Priya", "Marcus", "Elena", "Samuel", "Hana", "Diego", "Ruth", "Kofi"]
LAST = ["Patel", "Nguyen", "Garcia", "Okafor", "Kim", "Silva", "Cohen", "Reyes", "Novak",
        "Haddad", "Jensen", "Moreau", "Tanaka", "Brooks", "Ivanova", "Mensah", "Larsen",
        "Duarte", "Osei", "Fischer"]
CITIES = [("Newark", "NJ", "07102"), ("Trenton", "NJ", "08608"), ("Albany", "NY", "12207"),
          ("Hartford", "CT", "06103"), ("Scranton", "PA", "18503")]
PLANS = ["Original Medicare", "Medicare Advantage (HMO)", "Medicare Advantage (PPO)"]
SERVICES = [
    ("Annual wellness visit", 180), ("Physical therapy session", 140),
    ("MRI - lower back", 1200), ("Cardiac rehabilitation", 260),
    ("Skilled nursing facility stay (7 days)", 4200), ("Hearing exam", 150),
    ("Routine eye exam", 120), ("Durable medical equipment - walker", 95),
    ("Outpatient mental health visit", 175), ("Cosmetic procedure", 2500),
]
PROVIDERS = ["Riverside Clinic", "Northgate Hospital", "Oak Valley Therapy",
             "Summit Imaging", "Lakeshore Rural Health Clinic"]
DENIALS = ["Service not medically necessary", "Excluded from coverage",
           "Missing prior authorization", "Provider out of network"]


def main():
    init_db()
    with get_conn() as conn:
        conn.execute("TRUNCATE care.claims, care.members, care.messages, care.audit_log")

        n_claims = 0
        for i in range(20):
            member_id = f"M{1001 + i}"
            first, last = FIRST[i], LAST[i]
            city, state, zip_code = random.choice(CITIES)
            dob = date(1940, 1, 1) + timedelta(days=random.randint(0, 365 * 20))
            conn.execute(
                "INSERT INTO care.members VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                (member_id, f"{first} {last}", dob, random.choice(PLANS),
                 f"555-01{i:02d}", f"{first.lower()}.{last.lower()}@example.com",
                 f"{random.randint(10, 999)} Maple Street", city, state, zip_code),
            )

            for j in range(random.randint(3, 6)):
                service, base = random.choice(SERVICES)
                status = random.choices(["approved", "denied", "pending"], [6, 2, 2])[0]
                if service == "Cosmetic procedure":
                    status = "denied"
                reason = None
                if status == "denied":
                    reason = ("Excluded from coverage" if service == "Cosmetic procedure"
                              else random.choice(DENIALS))
                conn.execute(
                    "INSERT INTO care.claims VALUES (%s,%s,%s,%s,%s,%s,%s,%s)",
                    (f"C{member_id[1:]}-{j + 1}", member_id,
                     date(2026, 1, 1) + timedelta(days=random.randint(0, 240)),
                     random.choice(PROVIDERS), service,
                     round(base * random.uniform(0.8, 1.3), 2), status, reason),
                )
                n_claims += 1

        print(f"Created 20 fake members and {n_claims} claims.\n")
        member = conn.execute("SELECT * FROM care.members WHERE member_id = 'M1001'").fetchone()
        print("Example member:", member)
        for c in conn.execute(
                "SELECT claim_id, service, status, denial_reason FROM care.claims "
                "WHERE member_id = 'M1001' ORDER BY claim_id").fetchall():
            print("  claim:", c)


if __name__ == "__main__":
    main()