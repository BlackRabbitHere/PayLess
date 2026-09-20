CREATE TABLE merchant (
    code varchar(32) PRIMARY KEY,
    display_name varchar(100) NOT NULL,
    category varchar(32) NOT NULL
);
CREATE TABLE merchant_alias (
    alias varchar(100) PRIMARY KEY,
    merchant varchar(32) NOT NULL REFERENCES merchant(code)
);
CREATE TABLE provider (
    code varchar(32) PRIMARY KEY,
    display_name varchar(100) NOT NULL,
    merchant varchar(32) NOT NULL REFERENCES merchant(code)
);
INSERT INTO merchant VALUES ('SWIGGY', 'Swiggy', 'FOOD_DELIVERY'), ('YATRA', 'Yatra', 'TRAVEL'),
    ('EASEMYTRIP', 'EaseMyTrip', 'TRAVEL');
INSERT INTO merchant_alias VALUES ('swigy', 'SWIGGY'), ('swiggy money', 'SWIGGY'),
    ('ease my trip', 'EASEMYTRIP'), ('emt', 'EASEMYTRIP');
INSERT INTO provider VALUES ('GYFTR', 'GyFTR', 'SWIGGY'), ('YATRA', 'Yatra', 'YATRA'),
    ('EASEMYTRIP', 'EaseMyTrip', 'EASEMYTRIP');

CREATE TABLE offer (
    id bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    source_external_key varchar(512) NOT NULL UNIQUE,
    merchant varchar(32) NOT NULL REFERENCES merchant(code),
    provider varchar(32) NOT NULL REFERENCES provider(code),
    verification_status varchar(32) NOT NULL,
    last_verified_at timestamptz,
    valid_until timestamptz,
    observed_at timestamptz NOT NULL,
    fixture boolean NOT NULL,
    payload jsonb NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);
-- One row per acquisition attempt; scraper IDs can repeat when a cached envelope is returned.
CREATE TABLE scraper_run (
    id uuid PRIMARY KEY,
    request_id varchar(64) NOT NULL,
    scraper_request_id uuid NOT NULL,
    merchant varchar(32) NOT NULL REFERENCES merchant(code),
    provider varchar(32) NOT NULL REFERENCES provider(code),
    status varchar(32) NOT NULL,
    fixture boolean NOT NULL,
    offers_received integer NOT NULL CHECK (offers_received >= 0),
    partial_failures integer NOT NULL CHECK (partial_failures >= 0),
    duration_ms bigint NOT NULL CHECK (duration_ms >= 0),
    completed_at timestamptz NOT NULL DEFAULT now()
);
