SELECT 
    u.email,
    COUNT(l.id) AS count_links,
    u.date_joined
FROM 
    maker_user u
LEFT JOIN 
    maker_link l ON u.id = l.user_id
GROUP BY 
    u.id
ORDER BY 
    count_links DESC, 
    u.date_joined ASC
LIMIT 10;