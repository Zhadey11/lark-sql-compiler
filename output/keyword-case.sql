CREATE TABLE audit_log (
  id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
  message TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
INSERT INTO audit_log (message)
VALUES ('Mixed case keywords');
SELECT *
FROM audit_log
ORDER BY created_at
LIMIT 5;
