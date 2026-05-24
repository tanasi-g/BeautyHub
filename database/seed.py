
import bcrypt
from database.connection import Database


#  Ρόλοι
_ROLES = [
    (1, "admin",    "Διαχειριστής"),
    (2, "employee", "Υπάλληλος"),
    (3, "customer", "Πελάτης"),
]

#  Χρήστες
_USERS = [
    # --- admin
    {
        "username": "admin",   "email": "admin@salon.gr",
        "password": "admin123",
        "first_name": "Super", "last_name": "Admin",
        "phone": "2100000000", "role_id": 1,
    },
    # --- υπάλληλοι
    {
        "username": "nikos_k", "email": "nikos@salon.gr",
        "password": "nikos123",
        "first_name": "Νίκος", "last_name": "Κομμωτής",
        "phone": "6911111111", "role_id": 2,
    },
    {
        "username": "maria_k", "email": "maria@salon.gr",
        "password": "maria123",
        "first_name": "Μαρία", "last_name": "Κομμώτρια",
        "phone": "6922222222", "role_id": 2,
    },
    # --- πελάτες
    {
        "username": "petros",  "email": "petros@mail.gr",
        "password": "petros123",
        "first_name": "Πέτρος", "last_name": "Παπαδόπουλος",
        "phone": "6933333333", "role_id": 3,
    },
    {
        "username": "eleni",   "email": "eleni@mail.gr",
        "password": "eleni123",
        "first_name": "Ελένη", "last_name": "Γεωργίου",
        "phone": "6944444444", "role_id": 3,
    },
    {
        "username": "kostas",  "email": "kostas@mail.gr",
        "password": "kostas123",
        "first_name": "Κώστας", "last_name": "Αντωνίου",
        "phone": "6955555555", "role_id": 3,
    },
]

#  Υπηρεσίες κομμωτηρίου
_SERVICES = [
    ("Κούρεμα",                   "Κλασικό κούρεμα για άνδρες και γυναίκες",    30,  15.00),
    ("Βαφή Μαλλιών",              "Ολική βαφή με επαγγελματικά προϊόντα",        90,  45.00),
    ("Χτένισμα",                  "Πλύσιμο και επαγγελματικό χτένισμα",          30,  20.00),
    ("Highlights",                "Μερική ή ολική τεχνική highlights",           120,  80.00),
    ("Θεραπεία Κερατίνης",        "Εξομάλυνση και θρέψη με κερατίνη",           120,  70.00),
    ("Ίσιωμα – Blow Dry",         "Επαγγελματικό ίσιωμα με πιστολάκι",           60,  35.00),
]

#  Κομμωτήρια
_SALONS = [
    ("BeautyHub Κέντρο",     "Ερμού 45",          "Αθήνα",         "2101234567", "kentro@beautyhub.gr"),
    ("BeautyHub Βορρά",      "Εγνατία 12",        "Θεσσαλονίκη",   "2311234567", "vorra@beautyhub.gr"),
    ("Glamour Κομμωτήριο",   "Ποσειδώνος 8",      "Πειραιάς",      "2101987654", "glamour@salon.gr"),
]

#  Προϊόντα E-Shop
_PRODUCTS = [
    ("Σαμπουάν Αναδόμησης",         "Σαμπουάν για κατεστραμμένα μαλλιά με κερατίνη και πρωτεΐνες",   12.50, 20),
    ("Μάσκα Βαθιάς Ενυδάτωσης",     "Εντατική μάσκα για ξηρά και αφυδατωμένα μαλλιά",               18.00, 15),
    ("Serum Λάμψης",                 "Ορός για λαμπερά και απαλά μαλλιά χωρίς βάρος",                24.90, 10),
    ("Σπρέι Θερμοπροστασίας",        "Προστατεύει έως 230°C από πιστολάκι και πλάκα",                 14.50, 25),
    ("Βούτυρο Καριτέ",               "Φυσικό βούτυρο για βαθιά θρέψη και μαλακτική δράση",            9.90, 30),
    ("Λάδι Argan",                   "100% καθαρό λάδι argan για λαμπερά και υγιή μαλλιά",           22.00, 12),
    ("Κρέμα Styling Ελαφριάς Ρ.",    "Κρέμα για φυσικό styling χωρίς ψίχουλα",                       11.50, 18),
    ("Αντηλιακό Μαλλιών SPF30",      "Προστατεύει το χρώμα και τη δομή από τον ήλιο",                19.90,  8),
]


#  Helpers
def _uid(conn, username: str) -> int:
    return conn.execute("SELECT id FROM users WHERE username=?", (username,)).fetchone()["id"]

def _sid(conn, svc_name: str) -> int:
    return conn.execute("SELECT id FROM services WHERE name=?", (svc_name,)).fetchone()["id"]

def _insert_user(conn, user: dict) -> None:
    existing = conn.execute(
        "SELECT id, role_id FROM users WHERE username=?", (user["username"],)
    ).fetchone()
    if existing:
        # correct role if it was created with wrong role (e.g. via customer registration form)
        if existing["role_id"] != user["role_id"]:
            conn.execute(
                "UPDATE users SET role_id=? WHERE id=?", (user["role_id"], existing["id"])
            )
            print(f"[seed] fixed role for '{user['username']}' -> role_id={user['role_id']}")
        return
    pw_hash = bcrypt.hashpw(user["password"].encode(), bcrypt.gensalt()).decode()
    conn.execute(
        "INSERT INTO users (username,email,password_hash,first_name,last_name,phone,role_id) "
        "VALUES (:username,:email,:pw_hash,:first_name,:last_name,:phone,:role_id)",
        {**user, "pw_hash": pw_hash},
    )
    print(f"[seed] user '{user['username']}'  ->  password: {user['password']}")



# build data
def seed_database() -> None:
    conn = Database.get_connection()

    has_data = conn.execute(
        "SELECT 1 FROM salons LIMIT 1"
    ).fetchone()

    if has_data:
        print("Database already seeded.")
        return

    print("Seeding database...")

    # - roles -
    conn.executemany(
        "INSERT OR IGNORE INTO roles (id,name,display_name) VALUES (?,?,?)",
        _ROLES
    )

    # - users -
    for u in _USERS:
        _insert_user(conn, u)
    conn.commit()

    # - services -
    for name, desc, dur, price in _SERVICES:
        conn.execute(
            """
            INSERT OR IGNORE INTO services
            (name,description,duration_min,price)
            VALUES (?,?,?,?)
            """,
            (name, desc, dur, price),
        )
    conn.commit()

    # - salons -
    for name, addr, city, phone, email in _SALONS:
        conn.execute(
            """
            INSERT OR IGNORE INTO salons
            (name,address,city,phone,email)
            VALUES (?,?,?,?,?)
            """,
            (name, addr, city, phone, email),
        )
    conn.commit()

    # salon - services -
    svc_ids = {
        row["name"]: row["id"]
        for row in conn.execute(
            "SELECT id,name FROM services"
        ).fetchall()
    }

    salon_ids = {
        row["name"]: row["id"]
        for row in conn.execute(
            "SELECT id,name FROM salons"
        ).fetchall()
    }

    salon_svc_map = {
        "BeautyHub Κέντρο": list(svc_ids.values()),
        "BeautyHub Βορρά": [
            svc_ids[n]
            for n in (
                "Κούρεμα",
                "Βαφή Μαλλιών",
                "Χτένισμα",
                "Highlights",
            )
        ],
        "Glamour Κομμωτήριο": [
            svc_ids[n]
            for n in (
                "Κούρεμα",
                "Χτένισμα",
                "Ίσιωμα – Blow Dry",
            )
        ],
    }

    for salon_name, svcs in salon_svc_map.items():
        sid = salon_ids[salon_name]

        for svc_id in svcs:
            conn.execute(
                """
                INSERT OR IGNORE INTO salon_services
                (salon_id,service_id)
                VALUES (?,?)
                """,
                (sid, svc_id),
            )
    conn.commit()

    # - products -
    for name, desc, price, stock in _PRODUCTS:
        conn.execute(
            """
            INSERT OR IGNORE INTO products
            (name,description,price,stock)
            VALUES (?,?,?,?)
            """,
            (name, desc, price, stock),
        )
    conn.commit()

    # - appointments -
    nikos_id = _uid(conn, "nikos_k")
    maria_id = _uid(conn, "maria_k")
    petros_id = _uid(conn, "petros")
    eleni_id = _uid(conn, "eleni")
    kostas_id = _uid(conn, "kostas")

    svc_koup = _sid(conn, "Κούρεμα")
    svc_vafi = _sid(conn, "Βαφή Μαλλιών")
    svc_high = _sid(conn, "Highlights")
    svc_ker = _sid(conn, "Θεραπεία Κερατίνης")

    appts = [
        (petros_id, nikos_id, svc_koup, "2026-06-02 10:00", "pending", None),
        (eleni_id, nikos_id, svc_vafi, "2026-06-03 14:00", "confirmed", "Αλλεργία σε αμμωνία"),
        (kostas_id, maria_id, svc_high, "2026-06-04 11:00", "pending", None),
        (eleni_id, maria_id, svc_ker, "2026-06-10 09:30", "pending", None),

        # past appointments
        (petros_id, nikos_id, svc_koup, "2026-05-10 10:00", "done", None),
        (eleni_id, nikos_id, svc_vafi, "2026-05-15 15:00", "done", None),

        # cancelled
        (kostas_id, nikos_id, svc_koup, "2026-05-20 09:00", "cancelled", None),
    ]

    for cid, eid, svid, sat, status, notes in appts:
        exists = conn.execute(
            """
            SELECT 1
            FROM appointments
            WHERE customer_id=?
              AND employee_id=?
              AND scheduled_at=?
            """,
            (cid, eid, sat),
        ).fetchone()

        if not exists:
            conn.execute(
                """
                INSERT INTO appointments
                (
                    customer_id,
                    employee_id,
                    service_id,
                    scheduled_at,
                    status,
                    notes
                )
                VALUES (?,?,?,?,?,?)
                """,
                (cid, eid, svid, sat, status, notes),
            )

    conn.commit()

    # - orders -
    prod_ids = {
        row["name"]: row["id"]
        for row in conn.execute(
            "SELECT id,name FROM products"
        ).fetchall()
    }

    def _ensure_order(customer_id, total, status, payment, items):
        exists = conn.execute(
            """
            SELECT id
            FROM orders
            WHERE customer_id=?
              AND total_price=?
              AND status=?
            """,
            (customer_id, total, status),
        ).fetchone()

        if exists:
            return

        cur = conn.execute(
            """
            INSERT INTO orders
            (customer_id,total_price,status,payment_method)
            VALUES (?,?,?,?)
            """,
            (customer_id, total, status, payment),
        )

        oid = cur.lastrowid

        for pname, qty, price in items:
            conn.execute(
                """
                INSERT INTO order_items
                (
                    order_id,
                    product_id,
                    product_name,
                    quantity,
                    unit_price
                )
                VALUES (?,?,?,?,?)
                """,
                (oid, prod_ids[pname], pname, qty, price),
            )

    _ensure_order(
        petros_id,
        37.40,
        "completed",
        "cod",
        [
            ("Σαμπουάν Αναδόμησης", 2, 12.50),
            ("Σπρέι Θερμοπροστασίας", 1, 14.50),
        ],
    )

    _ensure_order(
        eleni_id,
        42.90,
        "completed",
        "cod",
        [
            ("Μάσκα Βαθιάς Ενυδάτωσης", 1, 18.00),
            ("Serum Λάμψης", 1, 24.90),
        ],
    )

    _ensure_order(
        petros_id,
        9.90,
        "pending",
        "cod",
        [
            ("Βούτυρο Καριτέ", 1, 9.90),
        ],
    )

    _ensure_order(
        kostas_id,
        33.50,
        "cancelled",
        "cod",
        [
            ("Λάδι Argan", 1, 22.00),
            ("Κρέμα Styling Ελαφριάς Ρ.", 1, 11.50),
        ],
    )

    conn.commit()

    # - notifications -
    notifs = [
        (
            petros_id,
            "Το ραντεβού σας για «Κούρεμα» την 2026-06-02 10:00 καταχωρήθηκε επιτυχώς."
        ),
        (
            eleni_id,
            "Το ραντεβού σας για «Βαφή Μαλλιών» την 2026-06-03 14:00 επιβεβαιώθηκε από τον κομμωτή."
        ),
        (
            kostas_id,
            "Το ραντεβού σας για «Highlights» την 2026-06-04 11:00 καταχωρήθηκε επιτυχώς."
        ),
        (
            petros_id,
            "Η παραγγελία σας #1 ολοκληρώθηκε. Ευχαριστούμε για την αγορά!"
        ),
        (
            eleni_id,
            "Η παραγγελία σας #2 ολοκληρώθηκε. Ευχαριστούμε για την αγορά!"
        ),
    ]

    for uid, msg in notifs:
        exists = conn.execute(
            """
            SELECT 1
            FROM notifications
            WHERE user_id=?
              AND message=?
            """,
            (uid, msg),
        ).fetchone()

        if not exists:
            conn.execute(
                """
                INSERT INTO notifications
                (user_id,message)
                VALUES (?,?)
                """,
                (uid, msg),
            )

    conn.commit()

    print("Database seeded successfully.")
