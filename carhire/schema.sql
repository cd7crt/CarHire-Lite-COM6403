DROP TABLE IF EXISTS bookings;
DROP TABLE IF EXISTS cars;

CREATE TABLE cars (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    make        TEXT    NOT NULL,
    model       TEXT    NOT NULL,
    category    TEXT    NOT NULL CHECK (category IN ('ECONOMY', 'COMPACT', 'SUV', 'LUXURY')),
    seats       INTEGER NOT NULL,
    daily_rate  INTEGER NOT NULL            -- whole pounds
);

CREATE TABLE bookings (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    reference           TEXT    NOT NULL UNIQUE,
    car_id              INTEGER NOT NULL REFERENCES cars (id),
    customer_name       TEXT    NOT NULL,
    customer_email      TEXT    NOT NULL,
    driver_age          INTEGER NOT NULL,
    licence_number      TEXT    NOT NULL,
    pickup_date         TEXT    NOT NULL,   -- YYYY-MM-DD
    return_date         TEXT    NOT NULL,   -- YYYY-MM-DD
    gps                 INTEGER NOT NULL DEFAULT 0,
    insurance           INTEGER NOT NULL DEFAULT 0,
    days                INTEGER NOT NULL,
    base_price          TEXT    NOT NULL,   -- money stored as decimal strings, e.g. '252.00'
    discount            TEXT    NOT NULL,
    surcharge           TEXT    NOT NULL,
    extras_price        TEXT    NOT NULL,
    total_price         TEXT    NOT NULL,
    status              TEXT    NOT NULL DEFAULT 'CONFIRMED'
                        CHECK (status IN ('CONFIRMED', 'PICKED_UP', 'RETURNED', 'CANCELLED')),
    refund_amount       TEXT,
    actual_return_date  TEXT,
    late_fee            TEXT,
    created_at          TEXT    NOT NULL
);

INSERT INTO cars (make, model, category, seats, daily_rate) VALUES
    ('Toyota',        'Yaris',    'ECONOMY', 5,  30),
    ('Ford',          'Fiesta',   'ECONOMY', 5,  32),
    ('Vauxhall',      'Astra',    'COMPACT', 5,  38),
    ('Volkswagen',    'Golf',     'COMPACT', 5,  40),
    ('Kia',           'Sportage', 'SUV',     5,  62),
    ('Nissan',        'Qashqai',  'SUV',     5,  65),
    ('BMW',           '5 Series', 'LUXURY',  5, 120),
    ('Mercedes-Benz', 'E-Class',  'LUXURY',  5, 125);
