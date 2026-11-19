-- =============================================================
-- 01_schema.sql — Schéma relationnel du projet
-- Tables : sites, lignes, machines, techniciens, interventions, alertes
-- Contraintes : PK, FK, UNIQUE, CHECK
-- =============================================================

-- 1. Sites (usines)
CREATE TABLE sites (
    site_id      SERIAL PRIMARY KEY,
    nom          VARCHAR(100) NOT NULL UNIQUE,
    ville        VARCHAR(100) NOT NULL,
    pays         VARCHAR(100) NOT NULL DEFAULT 'Tunisie'
);

-- 2. Lignes de production (par site)
CREATE TABLE lignes (
    ligne_id     SERIAL PRIMARY KEY,
    site_id      INTEGER NOT NULL REFERENCES sites(site_id) ON DELETE CASCADE,
    nom          VARCHAR(50) NOT NULL,
    UNIQUE (site_id, nom)
);

-- 3. Machines (référentiel)
CREATE TABLE machines (
    machine_id   VARCHAR(20) PRIMARY KEY,         -- ex. 'pump-00'
    type         VARCHAR(20) NOT NULL CHECK (type IN ('pump', 'motor', 'compressor')),
    ligne_id     INTEGER NOT NULL REFERENCES lignes(ligne_id) ON DELETE RESTRICT,
    date_mise_en_service DATE NOT NULL DEFAULT CURRENT_DATE,
    temperature_nominale NUMERIC(5,2) NOT NULL CHECK (temperature_nominale > 0),
    vibration_nominale   NUMERIC(5,2) NOT NULL CHECK (vibration_nominale > 0),
    current_nominale     NUMERIC(5,2) NOT NULL CHECK (current_nominale > 0),
    rpm_nominal          INTEGER NOT NULL CHECK (rpm_nominal > 0)
);

-- 4. Techniciens
CREATE TABLE techniciens (
    technicien_id SERIAL PRIMARY KEY,
    nom           VARCHAR(100) NOT NULL,
    email         VARCHAR(150) NOT NULL UNIQUE,
    specialite    VARCHAR(50) NOT NULL CHECK (specialite IN ('mecanique', 'electrique', 'instrumentation'))
);

-- 5. Interventions (transaction métier)
CREATE TABLE interventions (
    intervention_id SERIAL PRIMARY KEY,
    machine_id      VARCHAR(20) NOT NULL REFERENCES machines(machine_id) ON DELETE RESTRICT,
    technicien_id   INTEGER NOT NULL REFERENCES techniciens(technicien_id) ON DELETE RESTRICT,
    date_planifiee  TIMESTAMP NOT NULL,
    date_realisee   TIMESTAMP,
    statut          VARCHAR(20) NOT NULL DEFAULT 'planifiee'
                    CHECK (statut IN ('planifiee', 'en_cours', 'terminee', 'annulee')),
    description     TEXT,
    cout_estime     NUMERIC(10,2) CHECK (cout_estime >= 0),
    CHECK (date_realisee IS NULL OR date_realisee >= date_planifiee)
);

-- 6. Alertes (acquittées côté SQL, contenu côté NoSQL)
CREATE TABLE alertes_acquittees (
    alerte_id    VARCHAR(50) PRIMARY KEY,          -- id de l'alerte MongoDB
    machine_id   VARCHAR(20) NOT NULL REFERENCES machines(machine_id) ON DELETE CASCADE,
    technicien_id INTEGER REFERENCES techniciens(technicien_id) ON DELETE SET NULL,
    date_acquittement TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    commentaire  TEXT
);

-- =============================================================
-- Index (SQL-05)
-- =============================================================
CREATE INDEX idx_machines_type        ON machines(type);
CREATE INDEX idx_interventions_machine ON interventions(machine_id, date_planifiee);
CREATE INDEX idx_interventions_statut  ON interventions(statut);
CREATE INDEX idx_alertes_machine       ON alertes_acquittees(machine_id, date_acquittement);