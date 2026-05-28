
CREATE TABLE IF NOT EXISTS roles (
    id           INTEGER PRIMARY KEY,
    name         TEXT    NOT NULL UNIQUE,   -- 'admin', 'employee', 'customer'
    display_name TEXT    NOT NULL
);

CREATE TABLE IF NOT EXISTS users (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    username      TEXT    NOT NULL UNIQUE,
    email         TEXT    NOT NULL UNIQUE,
    password_hash TEXT    NOT NULL,
    first_name    TEXT    NOT NULL,
    last_name     TEXT    NOT NULL,
    phone         TEXT,
    role_id       INTEGER NOT NULL,
    is_active     INTEGER NOT NULL DEFAULT 1,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);

-- Κομμωτήρια
CREATE TABLE IF NOT EXISTS salons (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT    NOT NULL,
    address    TEXT    NOT NULL,
    city       TEXT    NOT NULL,
    phone      TEXT,
    email      TEXT,
    is_active  INTEGER NOT NULL DEFAULT 1,
    created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS salon_services (
    salon_id   INTEGER NOT NULL,
    service_id INTEGER NOT NULL,
    PRIMARY KEY (salon_id, service_id),
    FOREIGN KEY (salon_id)   REFERENCES salons(id)   ON DELETE CASCADE,
    FOREIGN KEY (service_id) REFERENCES services(id) ON DELETE CASCADE
);

--  Μελλοντικοί πίνακες

CREATE TABLE IF NOT EXISTS services (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT    NOT NULL,
    description  TEXT,
    duration_min INTEGER NOT NULL DEFAULT 30,
    price        REAL    NOT NULL DEFAULT 0.0,
    is_active    INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS appointments (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER NOT NULL,
    employee_id INTEGER NOT NULL,
    service_id  INTEGER NOT NULL,
    salon_id    INTEGER,
    scheduled_at TEXT   NOT NULL,
    status      TEXT    NOT NULL DEFAULT 'pending',  -- pending | confirmed | done | cancelled
    notes       TEXT,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (customer_id) REFERENCES users(id),
    FOREIGN KEY (employee_id) REFERENCES users(id),
    FOREIGN KEY (service_id)  REFERENCES services(id),
    FOREIGN KEY (salon_id)    REFERENCES salons(id)
);

CREATE TABLE IF NOT EXISTS notifications (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id    INTEGER NOT NULL,
    message    TEXT    NOT NULL,
    is_read    INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (user_id) REFERENCES users(id)
);

--  E-Shop
CREATE TABLE IF NOT EXISTS products (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT    NOT NULL UNIQUE,
    description TEXT,
    price       REAL    NOT NULL DEFAULT 0.0,
    stock       INTEGER NOT NULL DEFAULT 0,
    image_path  TEXT,
    is_active   INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT    NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS orders (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id    INTEGER NOT NULL,
    total_price    REAL    NOT NULL,
    status         TEXT    NOT NULL DEFAULT 'pending',
    payment_method TEXT    NOT NULL DEFAULT 'cod',
    created_at     TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (customer_id) REFERENCES users(id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id     INTEGER NOT NULL,
    product_id   INTEGER NOT NULL,
    product_name TEXT    NOT NULL,
    quantity     INTEGER NOT NULL,
    unit_price   REAL    NOT NULL,
    FOREIGN KEY (order_id)   REFERENCES orders(id)   ON DELETE CASCADE,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

--  Αξιολογήσεις Υπηρεσιών
CREATE TABLE IF NOT EXISTS reviews (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id INTEGER NOT NULL UNIQUE,   -- μία αξιολόγηση ανά ραντεβού
    customer_id    INTEGER NOT NULL,
    employee_id    INTEGER NOT NULL,
    service_id     INTEGER NOT NULL,
    rating         INTEGER NOT NULL CHECK(rating BETWEEN 1 AND 5),
    comment        TEXT,
    created_at     TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    FOREIGN KEY (appointment_id) REFERENCES appointments(id),
    FOREIGN KEY (customer_id)    REFERENCES users(id),
    FOREIGN KEY (employee_id)    REFERENCES users(id),
    FOREIGN KEY (service_id)     REFERENCES services(id)
);

--  Απογραφή Αποθήκης
CREATE TABLE IF NOT EXISTS inventories (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    status       TEXT    NOT NULL DEFAULT 'draft',   -- 'draft' | 'completed' | 'cancelled'
    inv_type     TEXT    NOT NULL DEFAULT 'full',    -- 'full' | 'partial'
    filter_kw    TEXT,
    created_at   TEXT    NOT NULL DEFAULT (datetime('now', 'localtime')),
    completed_at TEXT
);

CREATE TABLE IF NOT EXISTS inventory_lines (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    inventory_id INTEGER NOT NULL,
    product_id   INTEGER NOT NULL,
    product_name TEXT    NOT NULL,
    system_qty   INTEGER NOT NULL,
    actual_qty   INTEGER NOT NULL DEFAULT 0,
    deviation    INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (inventory_id) REFERENCES inventories(id) ON DELETE CASCADE,
    FOREIGN KEY (product_id)   REFERENCES products(id)
);
