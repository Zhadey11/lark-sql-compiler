INSERT INTO users (email, display_name, active)
VALUES ('sam@example.com', 'Sam Fisher', TRUE);
UPDATE users
SET active = FALSE
WHERE email = 'sam@example.com';
INSERT INTO products (name, price, in_stock)
VALUES ('Field Notes', 12.50, TRUE);
DELETE FROM users WHERE active = FALSE;
DROP TABLE products;
