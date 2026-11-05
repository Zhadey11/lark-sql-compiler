SELECT id, email
FROM users
WHERE active = TRUE AND display_name != 'Unknown';
SELECT id
FROM products
WHERE price >= 10 AND price <= 100
ORDER BY price
LIMIT 25;
SELECT id
FROM users
WHERE email <> 'nobody@example.com' OR active = FALSE;
UPDATE products
SET price = -1.25
WHERE in_stock = TRUE;
DELETE FROM users WHERE active != TRUE;
