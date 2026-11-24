-- =============================================================
-- 05_transaction.sql — Transaction « planifier une intervention » (SQL-04)
-- Cas A : COMMIT (tout valide)
-- Cas B : ROLLBACK (erreur au milieu → rien n'est conservé)
-- =============================================================

\echo '=== Cas A : transaction valide (COMMIT) ==='
BEGIN;

-- 1. Vérifier la machine (verrou de ligne)
SELECT machine_id, type FROM machines WHERE machine_id = 'pump-00' FOR UPDATE;

-- 2. Insérer l'intervention
INSERT INTO interventions (machine_id, technicien_id, date_planifiee, description, cout_estime)
VALUES ('pump-00', 1, NOW() + INTERVAL '2 days', 'Contrôle roulement', 150.00)
RETURNING intervention_id, machine_id, statut;

-- 3. Vérifier le résultat dans la transaction
SELECT COUNT(*) AS interventions_pump00 FROM interventions WHERE machine_id = 'pump-00';

COMMIT;

\echo '=== Cas B : transaction invalide (ROLLBACK) ==='
BEGIN;

-- 1. Insérer une intervention valide
INSERT INTO interventions (machine_id, technicien_id, date_planifiee, description)
VALUES ('pump-03', 2, NOW() + INTERVAL '3 days', 'Test rollback')
RETURNING intervention_id;

-- 2. Provoquer une erreur (FK invalide) → la transaction entière doit être annulée
INSERT INTO interventions (machine_id, technicien_id, date_planifiee)
VALUES ('machine-inexistante', 2, NOW() + INTERVAL '3 days');

ROLLBACK;

\echo '=== Vérification post-rollback : pump-03 ne doit PAS avoir d intervention ==='
SELECT COUNT(*) AS interventions_pump03 FROM interventions WHERE machine_id = 'pump-03';