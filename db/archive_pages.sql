CREATE TABLE IF NOT EXISTS removed_pages AS
SELECT *, 
       CURRENT_TIMESTAMP AS removal_date,
       'viewFallbackFrom=net-9.0' AS removal_reason
FROM pages
WHERE 1=0;

INSERT INTO removed_pages
SELECT *, 
       CURRENT_TIMESTAMP AS removal_date,
       'viewFallbackFrom=net-9.0' AS removal_reason
FROM pages
WHERE original_url LIKE '%&viewFallbackFrom=net-9.0%';

SELECT COUNT(*) FROM pages WHERE original_url LIKE '%&viewFallbackFrom=net-9.0%';
SELECT COUNT(*) FROM removed_pages WHERE original_url LIKE '%&viewFallbackFrom=net-9.0%';
SELECT COUNT(*) FROM removed_pages WHERE removal_reason = 'viewFallbackFrom=net-9.0';

DELETE FROM pages WHERE original_url LIKE '%&viewFallbackFrom=net-9.0%';