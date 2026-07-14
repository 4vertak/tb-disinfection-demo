-- Параметры (заменить при необходимости):
--   :start_date = '2026-01-01 00:00:00+09'::timestamptz
--   :end_date   = '2026-12-31 23:59:59+09'::timestamptz

-- ЗАПРОС 1: Оперативная сводка за период (KPI дезотдела)

-- Бизнес-вопрос:
--   Сколько заявок выполнено, отказано и находится в работе
--   за выбранный период?

-- Логика подсчёта:
--   - incompleted: статус 'incompleted', по дате подачи (≤ конец периода)
--   - completed:   статус 'completed', по дате дезинфекции
--   - refused:     статус 'refused', по дате отказа (disinfection_date)

-- Особенности:
--   - Часовой пояс Asia/Yakutsk
--   - JOIN disinfection обязателен (запись создаётся вместе с заявкой)

SELECT
	COUNT(DISTINCT a.id) FILTER (
        WHERE a.status = 'incompleted'
          AND a.submission_date AT TIME ZONE 'Asia/Yakutsk' 
             <= :end_date
    ) AS in_completed,
    COUNT(DISTINCT a.id) FILTER (
        WHERE a.status = 'completed'
          AND d.disinfection_date AT TIME ZONE 'Asia/Yakutsk' 
              BETWEEN :start_date AND :end_date
    ) AS completed,
    
    COUNT(DISTINCT a.id) FILTER (
        WHERE a.status = 'refused'
          AND d.disinfection_date AT TIME ZONE 'Asia/Yakutsk' 
             BETWEEN :start_date AND :end_date
    ) AS refused
FROM
    application a
    JOIN disinfection d ON d.application_id = a.id;

-- ЗАПРОС 2: Топ-10 дезинфекторов по количеству обработок и площади

-- Бизнес-вопросы:
--   1. Кто из дезинфекторов выполняет наибольший объём работы?
--   2. Как распределяется нагрузка между сотрудниками?
--   3. Кто может претендовать на премирование / нуждается в помощи?

-- Особенности:
--   - Учитывает часовой пояс Asia/Yakutsk (UTC+9)
--   - Только завершённые дезинфекции с положительной площадью
--   - Площадь делится на количество дезинфекторов в обработке
--   - Топ-3 по убыванию количества обработок

WITH disinfection_details AS (
    SELECT
        d.id,
        df.full_name,
        d.area_size,
        COUNT(*) OVER (PARTITION BY d.id) AS disinfectors_per_disinfection
    FROM
        disinfection d
        JOIN disinfection_disinfector dd ON d.id = dd.disinfection_id
        JOIN disinfector df ON df.id = dd.disinfector_id
    WHERE
        d.disinfection_date AT TIME ZONE 'Asia/Yakutsk'
            BETWEEN :start_date AND :end_date
        AND d.rejection_reason = 'completed'
        AND d.area_size > 0
)
SELECT
    full_name,
    COUNT(DISTINCT id) AS disinfection_count,
    ROUND(SUM(area_size::numeric / disinfectors_per_disinfection), 2) AS total_area_sqm
FROM
    disinfection_details
GROUP BY
    full_name
ORDER BY
    disinfection_count DESC,
    total_area_sqm DESC
LIMIT 3;

-- ЗАПРОС 3: Своевременность обработки по типам эпидемических очагов

-- Бизнес-вопросы:
--   1. По каким типам очагов дезинфекция выполняется медленнее всего?
--   2. Каков разброс времени реакции (мин/макс)?
--   3. Соответствуют ли сроки обработки требованиям санитарных правил?

-- Особенности:
--   - Учитывает часовой пояс Asia/Yakutsk (UTC+9)
--   - Длительность в часах от submission_date до disinfection_date
--   - Сортировка по убыванию среднего времени (проблемные зоны сверху)

SELECT
    ef.name AS focus_name,
    COUNT(app.id) AS total_processed,
    COUNT(CASE WHEN app.status = 'completed' THEN 1 END) AS completed_count,
    ROUND(
        100.0 * COUNT(CASE WHEN app.status = 'completed' THEN 1 END) / 
        NULLIF(COUNT(app.id), 0),
        1
    ) AS completion_rate_percent,
    ROUND(
        AVG(EXTRACT(EPOCH FROM (d.disinfection_date - app.submission_date)) / 3600),
        1
    ) AS avg_response_hours,
    ROUND(
        MIN(EXTRACT(EPOCH FROM (d.disinfection_date - app.submission_date)) / 3600),
        1
    ) AS min_response_hours,
    ROUND(
        MAX(EXTRACT(EPOCH FROM (d.disinfection_date - app.submission_date)) / 3600),
        1
    ) AS max_response_hours
FROM
    epidemic_focus ef
    JOIN application app ON app.focus_id = ef.id
    JOIN disinfection d ON d.application_id = app.id
WHERE
    app.submission_date AT TIME ZONE 'Asia/Yakutsk' 
        BETWEEN :start_date AND :end_date
GROUP BY
    ef.name
ORDER BY
    avg_response_hours DESC;

-- ЗАПРОС 4: Количество заявок по участкам за период
-- Бизнес-вопросы:
--   1. Какие участки генерируют наибольшую нагрузку?
--   2. Какой процент выполнения заявок по участкам?

-- Особенности:
--   - Учитывает часовой пояс Asia/Yakutsk (UTC+9)
--   - Считает общее количество, количество завершённых заявок и процент выполнения

SELECT
    a.name_area AS area_name,
    COUNT(app.id) AS total,
    COUNT(CASE WHEN app.status = 'completed' THEN 1 END) AS completed_applications,
    ROUND(
        100.0 * COUNT(CASE WHEN app.status = 'completed' THEN 1 END) / 
        NULLIF(COUNT(app.id), 0),
        1
    ) AS completion_rate_percent
FROM
    area a
    JOIN application app ON app.area_id = a.id
    JOIN doctor d ON app.doctor_id = d.id     -- doctor — это врач-участка от чьего имени отправляется заявка медицинской сестрой или самим врачом
WHERE
    app.submission_date AT TIME ZONE 'Asia/Yakutsk' 
        BETWEEN :start_date 
            AND :end_date
GROUP BY
    a.name_area
ORDER BY
    a.name_area;

-- ЗАПРОС 5: Количество выполненных дезинфекций по месяцам
-- Бизнес-вопрос:
--   Сколько дезинфекций было выполнено в каждом месяце за период?
--   Позволяет анализировать сезонную нагрузку на дезотдел.

-- Особенности:
--   - Учитывает часовой пояс Asia/Yakutsk (UTC+9)
--   - Фильтрует только завершённые заявки (status = 'completed')
--   - Группирует по номеру месяца

SELECT
    TO_CHAR(d.disinfection_date AT TIME ZONE 'Asia/Yakutsk', 'Month') AS month_name,
    EXTRACT(MONTH FROM d.disinfection_date AT TIME ZONE 'Asia/Yakutsk') AS month_num,
    COUNT(d.id) AS completed_count
FROM
    disinfection d
    JOIN application a ON d.application_id = a.id
WHERE
    d.disinfection_date BETWEEN :start_date AND :end_date
    AND a.status = 'completed'
GROUP BY
    month_num, month_name
ORDER BY
    month_num;