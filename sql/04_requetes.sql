-- =============================================================
-- 04_requetes.sql — Catalogue de 8 requêtes (SQL-03)
-- 2 jointures, 2 agrégations, 1 CTE, 1 sous-requête
-- =============================================================

\echo '=== Q1 (jointure) : machines avec leur ligne et leur site ==='
SELECT m.machine_id, m.type, l.nom AS ligne, s.nom AS site, s.ville
FROM machines m
JOIN lignes l ON l.ligne_id = m.ligne_id
JOIN sites  s ON s.site_id = l.site_id
ORDER BY m.machine_id;

\echo '=== Q2 (jointure) : interventions avec machine et technicien ==='
SELECT i.intervention_id, i.machine_id, m.type,
       t.nom AS technicien, t.specialite,
       i.date_planifiee, i.statut
FROM interventions i
JOIN machines    m ON m.machine_id = i.machine_id
JOIN techniciens t ON t.technicien_id = i.technicien_id
ORDER BY i.date_planifiee DESC;

\echo '=== Q3 (agrégation) : nombre de machines par type ==='
SELECT type, COUNT(*) AS nb_machines,
       ROUND(AVG(temperature_nominale)::numeric, 1) AS temp_moy
FROM machines
GROUP BY type
ORDER BY nb_machines DESC;

\echo '=== Q4 (agrégation) : interventions par statut ==='
SELECT statut, COUNT(*) AS nb,
       MIN(date_planifiee) AS premiere,
       MAX(date_planifiee) AS derniere
FROM interventions
GROUP BY statut
ORDER BY nb DESC;

\echo '=== Q5 (sous-requête) : machines sans aucune intervention ==='
SELECT machine_id, type
FROM machines
WHERE machine_id NOT IN (SELECT machine_id FROM interventions)
ORDER BY machine_id;

\echo '=== Q6 (CTE) : top 3 des machines les plus planifiées ==='
WITH planif AS (
    SELECT machine_id, COUNT(*) AS nb_interventions
    FROM interventions
    GROUP BY machine_id
)
SELECT p.machine_id, m.type, p.nb_interventions
FROM planif p
JOIN machines m ON m.machine_id = p.machine_id
ORDER BY p.nb_interventions DESC, p.machine_id
LIMIT 3;

\echo '=== Q7 (CTE + agrégation) : taux de machines planifiées par ligne ==='
WITH par_ligne AS (
    SELECT l.ligne_id, l.nom AS ligne, COUNT(m.machine_id) AS nb_machines
    FROM lignes l
    LEFT JOIN machines m ON m.ligne_id = l.ligne_id
    GROUP BY l.ligne_id, l.nom
),
planifiees AS (
    SELECT m.ligne_id, COUNT(DISTINCT i.machine_id) AS nb_planifiees
    FROM interventions i
    JOIN machines m ON m.machine_id = i.machine_id
    GROUP BY m.ligne_id
)
SELECT pl.ligne, pl.nb_machines,
       COALESCE(pz.nb_planifiees, 0) AS nb_planifiees,
       ROUND(100.0 * COALESCE(pz.nb_planifiees, 0) / NULLIF(pl.nb_machines, 0), 1) AS taux_pct
FROM par_ligne pl
LEFT JOIN planifiees pz ON pz.ligne_id = pl.ligne_id
ORDER BY pl.ligne;

\echo '=== Q8 (sous-requête corrélée) : machines avec intervention la plus récente ==='
SELECT m.machine_id, m.type,
       (SELECT MAX(i.date_planifiee)
        FROM interventions i
        WHERE i.machine_id = m.machine_id) AS derniere_intervention
FROM machines m
WHERE EXISTS (SELECT 1 FROM interventions i WHERE i.machine_id = m.machine_id)
ORDER BY derniere_intervention DESC NULLS LAST;