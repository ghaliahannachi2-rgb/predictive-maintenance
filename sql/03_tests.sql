-- =============================================================
-- 03_tests.sql — Tests d'intégrité (SQL-02)
-- But : prouver que les contraintes acceptent le valide et rejettent l'invalide.
-- =============================================================

\echo '=== Test 1 : insertion ACCEPTÉE (FK valides) ==='
INSERT INTO interventions (machine_id, technicien_id, date_planifiee, description)
VALUES ('pump-00', 1, NOW() + INTERVAL '1 day', 'Remplacement roulement')
RETURNING intervention_id, machine_id, statut;

\echo '=== Test 2 : insertion REJETÉE (FK machine inconnue) ==='
INSERT INTO interventions (machine_id, technicien_id, date_planifiee)
VALUES ('machine-inexistante', 1, NOW() + INTERVAL '1 day');

\echo '=== Test 3 : insertion REJETÉE (CHECK statut invalide) ==='
INSERT INTO interventions (machine_id, technicien_id, date_planifiee, statut)
VALUES ('pump-00', 1, NOW() + INTERVAL '1 day', 'en_attente');

\echo '=== Test 4 : insertion REJETÉE (date_realisee < date_planifiee) ==='
INSERT INTO interventions (machine_id, technicien_id, date_planifiee, date_realisee)
VALUES ('pump-00', 1, NOW() + INTERVAL '1 day', NOW());

\echo '=== Test 5 : insertion REJETÉE (type machine invalide) ==='
INSERT INTO machines (machine_id, type, ligne_id, temperature_nominale, vibration_nominale, current_nominale, rpm_nominal)
VALUES ('pump-99', 'turbine', 1, 40.0, 1.2, 12.0, 2950);