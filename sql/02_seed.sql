-- =============================================================
-- 02_seed.sql — Données de référence (idempotent)
-- =============================================================

-- 1. Site
INSERT INTO sites (nom, ville, pays) VALUES
    ('usine-tunis', 'Tunis', 'Tunisie')
ON CONFLICT (nom) DO NOTHING;

-- 2. Lignes
INSERT INTO lignes (site_id, nom)
SELECT s.site_id, l.nom
FROM sites s, (VALUES ('ligne1'), ('ligne2')) AS l(nom)
WHERE s.nom = 'usine-tunis'
ON CONFLICT (site_id, nom) DO NOTHING;

-- 3. 20 machines (mêmes IDs que fleet.py)
INSERT INTO machines (machine_id, type, ligne_id, temperature_nominale, vibration_nominale, current_nominale, rpm_nominal)
SELECT
    m.machine_id,
    m.type,
    l.ligne_id,
    m.temp,
    m.vib,
    m.cur,
    m.rpm
FROM (VALUES
    ('pump-00',       'pump',       'ligne1', 40.0, 1.2, 12.0, 2950),
    ('motor-01',      'motor',      'ligne2', 45.0, 1.5, 15.0, 1480),
    ('compressor-02', 'compressor', 'ligne1', 55.0, 2.0, 20.0,  980),
    ('pump-03',       'pump',       'ligne2', 40.0, 1.2, 12.0, 2950),
    ('motor-04',      'motor',      'ligne1', 45.0, 1.5, 15.0, 1480),
    ('compressor-05', 'compressor', 'ligne2', 55.0, 2.0, 20.0,  980),
    ('pump-06',       'pump',       'ligne1', 40.0, 1.2, 12.0, 2950),
    ('motor-07',      'motor',      'ligne2', 45.0, 1.5, 15.0, 1480),
    ('compressor-08', 'compressor', 'ligne1', 55.0, 2.0, 20.0,  980),
    ('pump-09',       'pump',       'ligne2', 40.0, 1.2, 12.0, 2950),
    ('motor-10',      'motor',      'ligne1', 45.0, 1.5, 15.0, 1480),
    ('compressor-11', 'compressor', 'ligne2', 55.0, 2.0, 20.0,  980),
    ('pump-12',       'pump',       'ligne1', 40.0, 1.2, 12.0, 2950),
    ('motor-13',      'motor',      'ligne2', 45.0, 1.5, 15.0, 1480),
    ('compressor-14', 'compressor', 'ligne1', 55.0, 2.0, 20.0,  980),
    ('pump-15',       'pump',       'ligne2', 40.0, 1.2, 12.0, 2950),
    ('motor-16',      'motor',      'ligne1', 45.0, 1.5, 15.0, 1480),
    ('compressor-17', 'compressor', 'ligne2', 55.0, 2.0, 20.0,  980),
    ('pump-18',       'pump',       'ligne1', 40.0, 1.2, 12.0, 2950),
    ('motor-19',      'motor',      'ligne2', 45.0, 1.5, 15.0, 1480)
) AS m(machine_id, type, ligne_nom, temp, vib, cur, rpm)
JOIN lignes l ON l.nom = m.ligne_nom
ON CONFLICT (machine_id) DO NOTHING;

-- 4. 3 techniciens
INSERT INTO techniciens (nom, email, specialite) VALUES
    ('Ali Ben Salah',  'ali.bensalah@usine.tn',   'mecanique'),
    ('Sonia Trabelsi', 'sonia.trabelsi@usine.tn', 'electrique'),
    ('Karim Jaziri',   'karim.jaziri@usine.tn',   'instrumentation')
ON CONFLICT (email) DO NOTHING;