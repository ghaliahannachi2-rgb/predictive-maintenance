-- =============================================================
-- 06_app_user.sql — Compte applicatif aux droits limités (SQL-06)
-- L'utilisateur app_usine peut lire/écrire les tables métier,
-- mais ne peut PAS créer/détruire des tables, ni gérer les rôles.
-- =============================================================

-- 1. Créer le rôle applicatif (si absent)
DO $$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'app_usine') THEN
        CREATE ROLE app_usine LOGIN PASSWORD 'AppUsine2026!';
    END IF;
END $$;

-- 2. Droits sur le schéma public (usage, pas création)
GRANT USAGE ON SCHEMA public TO app_usine;

-- 3. Droits de lecture sur toutes les tables métier
GRANT SELECT ON ALL TABLES IN SCHEMA public TO app_usine;

-- 4. Droits d'écriture limités (insertion/mise à jour) sur les tables métier
GRANT INSERT, UPDATE ON interventions, alertes_acquittees TO app_usine;

-- 5. Droits sur les séquences (pour les INSERT avec SERIAL)
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO app_usine;

-- 6. Interdire explicitement la création de tables/objets
REVOKE CREATE ON SCHEMA public FROM app_usine;

-- 7. Vérification
\echo '=== Droits de app_usine ==='
SELECT grantee, table_name, privilege_type
FROM information_schema.role_table_grants
WHERE grantee = 'app_usine'
ORDER BY table_name, privilege_type;