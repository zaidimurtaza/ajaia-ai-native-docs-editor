-- If you ran an older 001 that stored plaintext "demo", re-hash demo accounts.
-- Safe to re-run: same bcrypt hash for password "demo" (cost 12).

UPDATE ajaia.users
SET password = '$2b$12$YgD8LOorjJAjmpFtK9.dquWyUuTiiBr/R0cKEVnT60RuQu6XcE2YC'
WHERE email IN ('alice@example.com', 'bob@example.com');
