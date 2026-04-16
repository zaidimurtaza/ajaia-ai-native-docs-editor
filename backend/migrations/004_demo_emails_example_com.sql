-- If an older 001 seeded @demo.local, rename to @example.com so API EmailStr matches DB.
UPDATE ajaia.users SET email = 'alice@example.com' WHERE email = 'alice@demo.local';
UPDATE ajaia.users SET email = 'bob@example.com' WHERE email = 'bob@demo.local';
