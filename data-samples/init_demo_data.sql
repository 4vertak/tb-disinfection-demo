
-- 0. УДАЛЕНИЕ СТАРЫХ ТЕСТОВЫХ ДАННЫХ (заявки с номерами >= 300)
DELETE FROM disinfection_disinfector 
WHERE disinfection_id IN (
    SELECT d.id FROM disinfection d 
    JOIN application a ON d.application_id = a.id 
    WHERE a.application_number >= 300
);
DELETE FROM disinfection 
WHERE application_id IN (SELECT id FROM application WHERE application_number >= 300);
DELETE FROM application WHERE application_number >= 300;

-- 1. ТЕСТОВЫЕ ПОЛЬЗОВАТЕЛИ
INSERT INTO "user" (login, name, password_hash, user_type)
SELECT 'admin', 'Администратор', 'scrypt:32768:8:1$GPDreGPvVMc1Ul3a$f62466dbeefb203db7e9e16d00f2ea048e4cafbb0c136aafd0990107d8608ba44b588000679c7f120be6f1003c04bf9eca5edde645e41b975fbc4b50524edd8e', 'admin'
WHERE NOT EXISTS (SELECT 1 FROM "user" WHERE login = 'admin');

INSERT INTO "user" (id, login, name, password_hash, user_type)
SELECT * FROM (
    VALUES 
        (2, 'doctor', 'Врач Иванов', 'scrypt:32768:8:1$YRXNnceujKTSk0Zf$2b80b8742f1219a81980b239ed499ad2acb3ea4ab697fd917b63ade7b7ffecc9a670495ec359bc7249a72038bcea80d4297f09b81821ee356d99439d7103f252', 'doctor'),
        (3, 'disinfector', 'Дезинфектор Антонов', 'scrypt:32768:8:1$Ia1WRu6k6t4Zj4t0$e4b7816151c16a555d883180bd66959b0bc88b0b125429f8dac7ab45a2cb2a821a881e03fe6357f2ddb20275ab29bad472a79892bceb3b1521a03f154a1d2a27', 'disinfector')
) AS new_users(id, login, name, password_hash, user_type)
WHERE NOT EXISTS (SELECT 1 FROM "user" WHERE "user".id = new_users.id);

SELECT setval('user_id_seq', (SELECT COALESCE(MAX(id), 1) FROM "user"));

-- 2. ВЫМЫШЛЕННЫЕ ВРАЧИ (справочник doctor) – формат "Фамилия И.О."
INSERT INTO doctor (full_name, area_id)
SELECT * FROM (
    VALUES 
        ('Абрамов А.А.', 1), ('Белова Б.Б.', 2), ('Ветров В.В.', 3),
        ('Громова Г.Г.', 4), ('Дубровин Д.Д.', 5), ('Емельянова Е.Е.', 6),
        ('Жуков Ж.Ж.', 7), ('Зайцева З.З.', 8), ('Игнатов И.И.', 9),
        ('Князева К.К.', 10), ('Ларин Л.Л.', 11), ('Морозова М.М.', 12)
) AS new_doctors(full_name, area_id)
WHERE NOT EXISTS (SELECT 1 FROM doctor WHERE doctor.full_name = new_doctors.full_name);

-- 3. ВЫМЫШЛЕННЫЕ ДЕЗИНФЕКТОРЫ (справочник disinfector) – формат "Фамилия И.О."
INSERT INTO disinfector (full_name)
SELECT * FROM (
    VALUES 
        ('Антонов А.А.'), ('Борисова Б.Б.'), ('Васильев В.В.'),
        ('Григорьева Г.Г.'), ('Дмитриев Д.Д.'), ('Егорова Е.Е.'),
        ('Журавлёв Ж.Ж.'), ('Зимина З.З.'), ('Исаев И.И.'), ('Козлова К.К.')
) AS new_disinf(full_name)
WHERE NOT EXISTS (SELECT 1 FROM disinfector WHERE disinfector.full_name = new_disinf.full_name);

-- 4. ФУНКЦИЯ ДЛЯ СЛУЧАЙНОЙ ДАТЫ
CREATE OR REPLACE FUNCTION random_date(start_date DATE, end_date DATE)
RETURNS DATE AS $$
BEGIN
    RETURN start_date + (random() * (end_date - start_date))::INT;
END;
$$ LANGUAGE plpgsql;

-- 5. ГЕНЕРАЦИЯ ЗАЯВОК (40 шт., январь–апрель 2026)
DO $$
DECLARE
    dates_array DATE[];
    sorted_dates DATE[];
    i INT;
    app_date DATE;
    app_status TEXT;
    reason TEXT;
    doc_id INT;
    doc_name TEXT;
    area_id_val INT;
    diag_id INT;
    gdu_val TEXT;
    focus_val INT;
    hosp_date DATE;
    hosp_place TEXT;
    disinf_date TIMESTAMP;
    area_size_val NUMERIC;
    swab INT;
    rejection_reason_text TEXT;
    fio_array TEXT[];
    street_array TEXT[];
    work_array TEXT[];
    position_array TEXT[];
    rel_array TEXT[];
    user_id_val INT;
    start_date DATE := '2026-01-01';
    end_date DATE := '2026-04-28';
    app_number INT;
    refusal_reasons TEXT[];
    disinfector_ids INT[];
BEGIN
    -- Инициализация массивов
    fio_array := ARRAY[
        'Соколов Сокол Соколович', 'Лебедева Лебедь Лебедевна', 'Орлов Орёл Орлович',
        'Сорокина Сорока Сороковна', 'Воробьёв Воробей Воробьёвич', 'Голубева Голубка Голубевна',
        'Синицын Синица Синицынович', 'Павлова Пава Павловна', 'Королёв Король Королёвич',
        'Царева Царица Царевна', 'Князев Князь Князевич', 'Бояринова Боярыня Бояриновна',
        'Купец Купеческий Купецович', 'Мещерякова Мещера Мещеряковна', 'Крестьянов Крестьянин Крестьянович',
        'Дворянкина Дворянка Дворянкина', 'Воин Воинственный Воинович', 'Ремесленников Ремесло Ремесленникович',
        'Певцова Певица Певцовна', 'Плясунова Плясунья Плясуновна', 'Умнова Умница Умновна',
        'Силачев Силач Силачевич', 'Добрякова Добрячка Добрякова', 'Хитрова Хитреца Хитрова',
        'Скромнин Скромник Скромнинович', 'Веселова Веселуха Веселова', 'Хмуров Хмурый Хмурович'
    ];
    street_array := ARRAY['Ленина', 'Победы', 'Дзержинского', 'Кирова', 'Советская', 'Октябрьская', 'Гагарина', 'Лермонтова'];
    work_array := ARRAY['ООО "Север"', 'МУП "Якутскэнерго"', 'АО "Сахатранснефтегаз"', 'СВФУ', 'пенсионер', 'не работает'];
    position_array := ARRAY['инженер', 'бухгалтер', 'водитель', 'сварщик', 'студент', 'пенсионер', 'не работает'];
    rel_array := ARRAY['Сын', 'Дочь', 'Мать', 'Отец', 'Муж', 'Жена', 'Брат', 'Сестра'];
    refusal_reasons := ARRAY[
        'Пациент от госпитализации отказался',
        'Пациент переезжает в другой регион',
        'Пациент скрылся от медицинского наблюдения',
        'Отсутствует электричество в квартире для проведения дезинфекции',
        'Пациент не открывает дверь',
        'Пациент находится на стационарном лечении в другом учреждении',
        'Жильё признано аварийным, дезинфекция не требуется'
    ];

    -- Генерируем 40 случайных дат
    FOR i IN 1..40 LOOP
        dates_array := array_append(dates_array, random_date(start_date, end_date));
    END LOOP;
    
    -- Сортируем даты по возрастанию
    SELECT array_agg(d ORDER BY d) INTO sorted_dates FROM unnest(dates_array) AS d;
    
    -- Перебираем отсортированные даты, присваиваем номера 300..339
    FOR i IN 1..40 LOOP
        app_date := sorted_dates[i];
        app_number := 299 + i;
        
        -- Статус (70% completed, 20% refusal, 10% incompleted)
        CASE floor(random() * 10)
            WHEN 0,1 THEN app_status := 'refusal';
            WHEN 2 THEN app_status := 'incompleted';
            ELSE app_status := 'completed';
        END CASE;
        
        -- Причина заявки
        IF random() < 0.6 THEN reason := 'hospitalization'; ELSE reason := 'scheduled'; END IF;
        
        -- Внешние ключи
        SELECT id, full_name INTO doc_id, doc_name FROM doctor ORDER BY random() LIMIT 1;
        SELECT id INTO area_id_val FROM area ORDER BY random() LIMIT 1;
        SELECT id INTO diag_id FROM diagnosis ORDER BY random() LIMIT 1;
        SELECT id INTO user_id_val FROM "user" WHERE user_type IN ('doctor', 'disinfector') ORDER BY random() LIMIT 1;
        
        gdu_val := (ARRAY['IА-МБТ+', 'IА-МБТ-', 'IБ-МБТ+', 'IIА-МБТ+', 'III', '0-МБТ+'])[floor(random() * 6) + 1];
        focus_val := floor(random() * 4) + 1;
        
        -- Госпитализация (только если completed и hospitalization)
        IF app_status = 'completed' AND reason = 'hospitalization' AND random() < 0.7 THEN
            hosp_date := app_date + (floor(random() * 5))::INT;
            hosp_place := (ARRAY['ОТОД', 'ОМЛУ-1', 'ОМЛУ-2', 'ОАРИТ', 'ОДБТ №1', 'Дневной стационар'])[floor(random() * 6) + 1];
        ELSE
            hosp_date := NULL;
            hosp_place := NULL;
        END IF;
        
        -- ВСТАВКА ЗАЯВКИ
        INSERT INTO application (
            application_number, submission_date, patient_full_name, birth_date, address,
            contact_phone, relative_contact_phone, workplace, "position",
            registration_date, diagnosis_id, gdu, focus_id, reason_application,
            status, user_id, doctor_id, doctor_full_name, area_id,
            hospitalization_date, place_of_hospitalization
        ) VALUES (
            app_number, app_date,
            fio_array[floor(random() * array_length(fio_array, 1)) + 1],
            ('1950-01-01'::DATE + (random() * 20000)::INT),
            'г Якутск, ул ' || street_array[floor(random() * array_length(street_array, 1)) + 1] 
                || ', д ' || floor(random()*150+1) || ', кв ' || floor(random()*200+1),
            '+7 (914) ' || lpad(floor(random()*10000000)::TEXT, 7, '0'),
            '+7 (924) ' || lpad(floor(random()*10000000)::TEXT, 7, '0') || '&' ||
                rel_array[floor(random() * array_length(rel_array, 1)) + 1] || ' ' ||
                (ARRAY['Иванов','Петров','Сидоров','Кузнецов','Смирнов'])[floor(random()*5)+1],
            work_array[floor(random() * array_length(work_array, 1)) + 1],
            position_array[floor(random() * array_length(position_array, 1)) + 1],
            app_date,
            diag_id, gdu_val, focus_val, reason,
            app_status, user_id_val, doc_id, doc_name, area_id_val,
            hosp_date, hosp_place
        );
        
        -- ОБЯЗАТЕЛЬНОЕ СОЗДАНИЕ ЗАПИСИ В disinfection ДЛЯ КАЖДОЙ ЗАЯВКИ
        IF app_status = 'completed' THEN
            -- Полная дезинфекция
            disinf_date := (app_date + (random() * interval '12 days') + interval '4 hours')::TIMESTAMP;
            -- Исправлено: безопасное округление через NUMERIC
            area_size_val := (20 + random() * 180)::NUMERIC(10,2);
            swab := CASE WHEN random() < 0.8 THEN 0 ELSE floor(random() * 3) + 1 END;
            
            INSERT INTO disinfection (
                application_id, rejection_reason, disinfection_date,
                area_size, volume_size, spraying_time, user_id, swab_testing
            ) VALUES (
                currval('application_id_seq'), 'completed',
                disinf_date, area_size_val, area_size_val * 3,
                floor(area_size_val * 0.15)::TEXT || ' мин ' || floor(random()*60)::TEXT || ' с',
                user_id_val, swab
            );
            
            -- Назначение дезинфекторов (от 1 до 3)
            FOR j IN 1..(floor(random() * 3) + 1) LOOP
                INSERT INTO disinfection_disinfector (disinfection_id, disinfector_id)
                SELECT currval('disinfection_id_seq'), id 
                FROM disinfector 
                ORDER BY random() 
                LIMIT 1
                ON CONFLICT (disinfection_id, disinfector_id) DO NOTHING;
            END LOOP;
            
        ELSIF app_status = 'incompleted' THEN
            -- Только дата = дате заявки, остальные поля NULL
            INSERT INTO disinfection (
                application_id, rejection_reason, disinfection_date,
                area_size, volume_size, spraying_time, user_id, swab_testing
            ) VALUES (
                currval('application_id_seq'), NULL, app_date, NULL, NULL, NULL, NULL, NULL
            );
            
        ELSIF app_status = 'refusal' THEN
            -- Отказ: дата отказа >= даты заявки, заполненная причина
            disinf_date := (app_date + (random() * interval '7 days') + interval '1 hour')::TIMESTAMP;
            rejection_reason_text := refusal_reasons[floor(random() * array_length(refusal_reasons, 1)) + 1];
            
            INSERT INTO disinfection (
                application_id, rejection_reason, disinfection_date,
                area_size, volume_size, spraying_time, user_id, swab_testing
            ) VALUES (
                currval('application_id_seq'), rejection_reason_text, disinf_date,
                NULL, NULL, NULL, user_id_val, NULL
            );

            -- Назначение дезинфекторов (от 1 до 3)
            FOR j IN 1..(floor(random() * 3) + 1) LOOP
                INSERT INTO disinfection_disinfector (disinfection_id, disinfector_id)
                SELECT currval('disinfection_id_seq'), id 
                FROM disinfector 
                ORDER BY random() 
                LIMIT 1
                ON CONFLICT (disinfection_id, disinfector_id) DO NOTHING;
            END LOOP;
            
        END IF;
    END LOOP;
END $$;

-- 6. НЕКОНСИСТЕНТНОСТЬ ФИО – заявки 901..904 с разными вариантами заполнения одного пациента
DO $$
DECLARE
    base_fio TEXT := 'Соколов Сокол Соколович';
    base_birth DATE := '1980-05-15';
    base_addr TEXT := 'г Якутск, ул Ленина, д 10, кв 5';
    base_phone TEXT := '+7 (914) 1234567';
    base_rel_phone TEXT := '+7 (924) 7654321&Сын Петров';
    base_work TEXT := 'ООО "Север"';
    base_pos TEXT := 'инженер';
    base_diag INTEGER;
    base_gdu TEXT := 'IА-МБТ+';
    base_focus INTEGER := 2;
    base_reason TEXT := 'hospitalization';
    base_user INTEGER;
    base_doctor_id INTEGER;
    base_doctor_name TEXT;
    base_area INTEGER;
BEGIN
    SELECT id INTO base_diag FROM diagnosis ORDER BY random() LIMIT 1;
    SELECT id INTO base_user FROM "user" WHERE user_type IN ('doctor', 'disinfector') ORDER BY random() LIMIT 1;
    SELECT id, full_name INTO base_doctor_id, base_doctor_name FROM doctor ORDER BY random() LIMIT 1;
    SELECT id INTO base_area FROM area ORDER BY random() LIMIT 1;
    
    INSERT INTO application (application_number, submission_date, patient_full_name, birth_date, address,
        contact_phone, relative_contact_phone, workplace, "position", registration_date,
        diagnosis_id, gdu, focus_id, reason_application, status, user_id, doctor_id, doctor_full_name, area_id,
        hospitalization_date, place_of_hospitalization)
    VALUES
        (901, '2025-12-28', base_fio, base_birth, base_addr, base_phone, base_rel_phone,
         base_work, base_pos, '2025-12-28', base_diag, base_gdu, base_focus, base_reason,
         'completed', base_user, base_doctor_id, base_doctor_name, base_area, '2025-12-29', 'ОТОД'),
        (902, '2026-01-15', 'Соколов Сокол Соколовыч', base_birth, base_addr, base_phone, base_rel_phone,
         base_work, base_pos, '2026-01-15', base_diag, base_gdu, base_focus, base_reason,
         'completed', base_user, base_doctor_id, base_doctor_name, base_area, '2026-01-16', 'ОМЛУ-1'),
        (903, '2026-02-20', 'Соколов С. С.', base_birth, base_addr, base_phone, base_rel_phone,
         base_work, base_pos, '2026-02-20', base_diag, base_gdu, base_focus, base_reason,
         'refusal', base_user, base_doctor_id, base_doctor_name, base_area, NULL, NULL),
        (904, '2026-04-05', 'Сокол Соколович Соколов', base_birth, base_addr, base_phone, base_rel_phone,
         base_work, base_pos, '2026-04-05', base_diag, base_gdu, base_focus, base_reason,
         'incompleted', base_user, base_doctor_id, base_doctor_name, base_area, NULL, NULL);
    
    -- Дезинфекция для заявки 901 (completed)
    INSERT INTO disinfection (application_id, disinfection_date, area_size, volume_size, spraying_time, user_id, swab_testing)
    VALUES (currval('application_id_seq')-3, '2025-12-29 10:00:00', 45.5, 136.5, '08 мин 12 с', base_user, 0);
    INSERT INTO disinfection_disinfector (disinfection_id, disinfector_id)
    SELECT currval('disinfection_id_seq')-1, id FROM disinfector LIMIT 1;
    
    -- Дезинфекция для заявки 902 (completed)
    INSERT INTO disinfection (application_id, disinfection_date, area_size, volume_size, spraying_time, user_id, swab_testing)
    VALUES (currval('application_id_seq')-2, '2026-01-16 11:30:00', 62.0, 186.0, '11 мин 10 с', base_user, 1);
    INSERT INTO disinfection_disinfector (disinfection_id, disinfector_id)
    SELECT currval('disinfection_id_seq')-1, id FROM disinfector ORDER BY random() LIMIT 2;
    
    -- Дезинфекция для заявки 903 (refusal)
    INSERT INTO disinfection (application_id, rejection_reason, disinfection_date)
    VALUES (currval('application_id_seq')-1, 'Пациент от госпитализации и дезинфекции отказался', '2026-02-21 09:00:00');
    
    -- Дезинфекция для заявки 904 (incompleted)
    INSERT INTO disinfection (application_id, disinfection_date)
    VALUES (currval('application_id_seq'), '2026-04-05');
END $$;


-- 7. ОБНОВЛЕНИЕ СЧЁТЧИКА ЗАЯВОК
UPDATE application_counter SET last_number = 904 WHERE year = 2026;
INSERT INTO application_counter (year, last_number) SELECT 2026, 904 WHERE NOT EXISTS (SELECT 1 FROM application_counter WHERE year = 2026);