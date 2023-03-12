SELECT
    * 
FROM
    Win5TargetRaceDetail 
WHERE
    (レース日付 == :race_date 
    AND レース番号 == :race_no)
@order_by
;