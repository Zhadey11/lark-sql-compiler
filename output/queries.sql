SELECT *
FROM users;
SELECT email, display_name
FROM users
WHERE active = TRUE
ORDER BY created_at DESC
LIMIT 20;
SELECT name, price
FROM products
WHERE in_stock = TRUE
ORDER BY price
LIMIT 10;
