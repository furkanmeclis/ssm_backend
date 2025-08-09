-- Begin a transaction to ensure data integrity
BEGIN;

-- Define a Common Table Expression (CTE) to calculate TestType for each question
WITH TestTypeCTE AS (
    SELECT 
        q.id AS question_id,
        et.name AS exam_type,
        ey.year AS exam_year,
        s.name AS subject,
        q.question_number,
        (
            CASE 
                -- Handling AYT Exam Type with specific exceptions
                WHEN et.name = 'AYT' THEN 
                    CASE 
                        WHEN s.name = 'Tarih' AND q.question_number >= 25 THEN 'turkdili-edebiyat-testi'
                        WHEN s.name = 'Tarih' THEN 'sosyal-testi'
                        WHEN s.name = 'Coğrafya' AND q.question_number >= 35 THEN 'turkdili-edebiyat-testi'
                        WHEN s.name = 'Coğrafya' THEN 'sosyal-testi'
                        WHEN s.name IN ('Türkçe', 'Edebiyat') THEN 'turkdili-edebiyat-testi'
                        WHEN s.name IN ('Felsefe', 'Psikoloji', 'Mantık', 'Din Kültürü', 'Sosyoloji') THEN 'sosyal-testi'
                        WHEN s.name IN ('Matematik', 'Geometri') THEN 'matematik-testi'
                        WHEN s.name IN ('Fizik', 'Kimya', 'Biyoloji') THEN 'fen-testi'
                        ELSE lower(replace(s.name, ' ', '-')) || '-testi'
                    END

                -- Handling TYT Exam Type
                WHEN et.name = 'TYT' THEN 
                    CASE 
                        WHEN s.name = 'Türkçe' THEN 'turkce-testi'
                        WHEN s.name IN ('Matematik', 'Geometri') THEN 'matematik-testi'
                        WHEN s.name IN ('Fizik', 'Kimya', 'Biyoloji') THEN 'fen-testi'
                        WHEN s.name IN ('Coğrafya', 'Tarih', 'Felsefe', 'Din Kültürü') THEN 'sosyal-bilimler-testi'
                        ELSE lower(replace(s.name, ' ', '-')) || '-testi'
                    END

                -- Handling KPSS Exam Type
                WHEN et.name = 'KPSS' THEN 
                    CASE 
                        WHEN s.name IN ('Türkçe', 'Matematik', 'Geometri') THEN 'genel-yetenek-testi'
                        WHEN s.name IN ('Tarih', 'Coğrafya', 'Vatandaşlık', 'Genel Kültür') THEN 'genel-kultur-testi'
                        ELSE lower(replace(s.name, ' ', '-')) || '-testi'
                    END

                -- Handling MSÜ Exam Type
                WHEN et.name = 'MSÜ' THEN 
                    CASE 
                        WHEN s.name = 'Türkçe' THEN 'turkce-testi'
                        WHEN s.name IN ('Matematik', 'Geometri') THEN 'matematik-testi'
                        WHEN s.name IN ('Fizik', 'Kimya', 'Biyoloji') THEN 'fen-testi'
                        WHEN s.name IN ('Coğrafya', 'Tarih', 'Felsefe', 'Din Kültürü') THEN 'sosyal-bilimler-testi'
                        ELSE lower(replace(s.name, ' ', '-')) || '-testi'
                    END

                -- Handling YDT Exam Type
                WHEN et.name = 'YDT' THEN 
                    CASE 
                        WHEN s.name = 'İngilizce' THEN 'ingilizce-testi'
                        WHEN s.name = 'Almanca' THEN 'almanca-testi'
                        WHEN s.name = 'Fransızca' THEN 'fransizca-testi'
                        WHEN s.name = 'Arapça' THEN 'arapca-testi'
                        WHEN s.name = 'Rusça' THEN 'rusca-testi'
                        ELSE lower(replace(s.name, ' ', '-')) || '-testi'
                    END

                -- Handling YGS Exam Type
                WHEN et.name = 'YGS' THEN 
                    CASE 
                        WHEN s.name = 'Türkçe' THEN 'turkce-testi'
                        WHEN s.name IN ('Matematik', 'Geometri') THEN 'matematik-testi'
                        WHEN s.name IN ('Fizik', 'Kimya', 'Biyoloji') THEN 'fen-testi'
                        WHEN s.name IN ('Coğrafya', 'Tarih', 'Felsefe', 'Din Kültürü') THEN 'sosyal-bilimler-testi'
                        ELSE lower(replace(s.name, ' ', '-')) || '-testi'
                    END

                -- Handling LYS Exam Type
                WHEN et.name = 'LYS' THEN 
                    CASE 
                        -- Special handling for 2017
                        WHEN ey.year = 2017 AND s.name IN ('Matematik', 'Geometri') THEN 'sayisal-testi'
                        -- Other subjects for all years, including 2017
                        WHEN s.name = 'Matematik' THEN 'matematik-testi'
                        WHEN s.name = 'Geometri' THEN 'geometri-testi'
                        WHEN s.name = 'Kimya' THEN 'kimya-testi'
                        WHEN s.name = 'Biyoloji' THEN 'biyoloji-testi'
                        WHEN s.name = 'Fizik' THEN 'fizik-testi'
                        WHEN s.name = 'Coğrafya' THEN 'cografya-testi'
                        WHEN s.name IN ('Türkçe', 'Edebiyat') THEN 'turkdili-edebiyat-testi'
                        WHEN s.name IN ('Sosyoloji', 'Psikoloji', 'Mantık', 'Din Kültürü') THEN 'sosyal-bilimler-testi'
                        WHEN s.name = 'Tarih' THEN 'tarih-testi'
                        ELSE lower(replace(s.name, ' ', '-')) || '-testi'
                    END

                -- Handling ALES Exam Type
                WHEN et.name = 'ALES' THEN
                    CASE
                        -- ALES 2013
                        WHEN ey.year = 2013 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 1 AND 50 THEN 'ales-1-sayisal-1-testi'
                        WHEN ey.year = 2013 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 51 AND 100 THEN 'ales-1-sayisal-2-testi'
                        WHEN ey.year = 2013 AND s.name = 'Türkçe' AND q.question_number BETWEEN 101 AND 150 THEN 'ales-1-sozel-1-testi'
                        WHEN ey.year = 2013 AND s.name = 'Türkçe' AND q.question_number BETWEEN 151 AND 200 THEN 'ales-1-sozel-2-testi'
                        WHEN ey.year = 2013 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 201 AND 250 THEN 'ales-2-sayisal-1-testi'
                        WHEN ey.year = 2013 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 251 AND 300 THEN 'ales-2-sayisal-2-testi'
                        WHEN ey.year = 2013 AND s.name = 'Türkçe' AND q.question_number BETWEEN 301 AND 350 THEN 'ales-2-sozel-1-testi'
                        WHEN ey.year = 2013 AND s.name = 'Türkçe' AND q.question_number BETWEEN 351 AND 400 THEN 'ales-2-sozel-2-testi'

                        -- ALES 2014
                        WHEN ey.year = 2014 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 1 AND 40 THEN 'ales-1-sayisal-1-testi'
                        WHEN ey.year = 2014 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 41 AND 80 THEN 'ales-1-sayisal-2-testi'
                        WHEN ey.year = 2014 AND s.name = 'Türkçe' AND q.question_number BETWEEN 81 AND 120 THEN 'ales-1-sozel-1-testi'
                        WHEN ey.year = 2014 AND s.name = 'Türkçe' AND q.question_number BETWEEN 121 AND 160 THEN 'ales-1-sozel-2-testi'
                        WHEN ey.year = 2014 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 161 AND 200 THEN 'ales-2-sayisal-1-testi'
                        WHEN ey.year = 2014 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 201 AND 240 THEN 'ales-2-sayisal-2-testi'
                        WHEN ey.year = 2014 AND s.name = 'Türkçe' AND q.question_number BETWEEN 241 AND 280 THEN 'ales-2-sozel-1-testi'
                        WHEN ey.year = 2014 AND s.name = 'Türkçe' AND q.question_number BETWEEN 281 AND 320 THEN 'ales-2-sozel-2-testi'

                        -- ALES 2015
                        WHEN ey.year = 2015 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 1 AND 40 THEN 'ales-1-sayisal-1-testi'
                        WHEN ey.year = 2015 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 41 AND 80 THEN 'ales-1-sayisal-2-testi'
                        WHEN ey.year = 2015 AND s.name = 'Türkçe' AND q.question_number BETWEEN 81 AND 120 THEN 'ales-1-sozel-1-testi'
                        WHEN ey.year = 2015 AND s.name = 'Türkçe' AND q.question_number BETWEEN 121 AND 160 THEN 'ales-1-sozel-2-testi'
                        WHEN ey.year = 2015 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 161 AND 200 THEN 'ales-2-sayisal-1-testi'
                        WHEN ey.year = 2015 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 201 AND 240 THEN 'ales-2-sayisal-2-testi'
                        WHEN ey.year = 2015 AND s.name = 'Türkçe' AND q.question_number BETWEEN 241 AND 280 THEN 'ales-2-sozel-1-testi'
                        WHEN ey.year = 2015 AND s.name = 'Türkçe' AND q.question_number BETWEEN 281 AND 320 THEN 'ales-2-sozel-2-testi'

                        -- ALES 2016
                        WHEN ey.year = 2016 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 1 AND 40 THEN 'ales-1-sayisal-1-testi'
                        WHEN ey.year = 2016 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 41 AND 80 THEN 'ales-1-sayisal-2-testi'
                        WHEN ey.year = 2016 AND s.name = 'Türkçe' AND q.question_number BETWEEN 81 AND 120 THEN 'ales-1-sozel-1-testi'
                        WHEN ey.year = 2016 AND s.name = 'Türkçe' AND q.question_number BETWEEN 121 AND 160 THEN 'ales-1-sozel-2-testi'
                        WHEN ey.year = 2016 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 161 AND 200 THEN 'ales-2-sayisal-1-testi'
                        WHEN ey.year = 2016 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 201 AND 240 THEN 'ales-2-sayisal-2-testi'
                        WHEN ey.year = 2016 AND s.name = 'Türkçe' AND q.question_number BETWEEN 241 AND 280 THEN 'ales-2-sozel-1-testi'
                        WHEN ey.year = 2016 AND s.name = 'Türkçe' AND q.question_number BETWEEN 281 AND 319 THEN 'ales-2-sozel-2-testi'

                        -- ALES 2017
                        WHEN ey.year = 2017 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 1 AND 40 THEN 'ales-1-sayisal-1-testi'
                        WHEN ey.year = 2017 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 41 AND 80 THEN 'ales-1-sayisal-2-testi'
                        WHEN ey.year = 2017 AND s.name = 'Türkçe' AND q.question_number BETWEEN 81 AND 120 THEN 'ales-1-sozel-1-testi'
                        WHEN ey.year = 2017 AND s.name = 'Türkçe' AND q.question_number BETWEEN 121 AND 160 THEN 'ales-1-sozel-2-testi'
                        WHEN ey.year = 2017 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 161 AND 210 THEN 'ales-2-sayisal-1-testi'
                        WHEN ey.year = 2017 AND s.name = 'Türkçe' AND q.question_number BETWEEN 211 AND 260 THEN 'ales-2-sozel-1-testi'

                        -- ALES 2018
                        WHEN ey.year = 2018 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 1 AND 50 THEN 'ales-1-sayisal-1-testi'
                        WHEN ey.year = 2018 AND s.name = 'Türkçe' AND q.question_number BETWEEN 51 AND 100 THEN 'ales-1-sozel-1-testi'
                        WHEN ey.year = 2018 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 101 AND 150 THEN 'ales-2-sayisal-1-testi'
                        WHEN ey.year = 2018 AND s.name = 'Türkçe' AND q.question_number BETWEEN 151 AND 200 THEN 'ales-2-sozel-1-testi'
                        WHEN ey.year = 2018 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 201 AND 250 THEN 'ales-3-sayisal-1-testi'
                        WHEN ey.year = 2018 AND s.name = 'Türkçe' AND q.question_number BETWEEN 251 AND 300 THEN 'ales-3-sozel-1-testi'

                        -- ALES 2019
                        WHEN ey.year = 2019 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 1 AND 50 THEN 'ales-1-sayisal-1-testi'
                        WHEN ey.year = 2019 AND s.name = 'Türkçe' AND q.question_number BETWEEN 51 AND 100 THEN 'ales-1-sozel-1-testi'
                        WHEN ey.year = 2019 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 101 AND 150 THEN 'ales-2-sayisal-1-testi'
                        WHEN ey.year = 2019 AND s.name = 'Türkçe' AND q.question_number BETWEEN 151 AND 200 THEN 'ales-2-sozel-1-testi'
                        WHEN ey.year = 2019 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 201 AND 250 THEN 'ales-3-sayisal-1-testi'
                        WHEN ey.year = 2019 AND s.name = 'Türkçe' AND q.question_number BETWEEN 251 AND 300 THEN 'ales-3-sozel-1-testi'

                        -- ALES 2020
                        WHEN ey.year = 2020 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 1 AND 50 THEN 'ales-1-sayisal-1-testi'
                        WHEN ey.year = 2020 AND s.name = 'Türkçe' AND q.question_number BETWEEN 51 AND 100 THEN 'ales-1-sozel-1-testi'
                        WHEN ey.year = 2020 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 101 AND 150 THEN 'ales-2-sayisal-1-testi'
                        WHEN ey.year = 2020 AND s.name = 'Türkçe' AND q.question_number BETWEEN 151 AND 200 THEN 'ales-2-sozel-1-testi'

                        -- ALES 2021
                        WHEN ey.year = 2021 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 1 AND 50 THEN 'ales-1-sayisal-1-testi'
                        WHEN ey.year = 2021 AND s.name = 'Türkçe' AND q.question_number BETWEEN 51 AND 100 THEN 'ales-1-sozel-1-testi'
                        WHEN ey.year = 2021 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 101 AND 150 THEN 'ales-2-sayisal-1-testi'
                        WHEN ey.year = 2021 AND s.name = 'Türkçe' AND q.question_number BETWEEN 151 AND 200 THEN 'ales-2-sozel-1-testi'
                        WHEN ey.year = 2021 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 201 AND 250 THEN 'ales-3-sayisal-1-testi'
                        WHEN ey.year = 2021 AND s.name = 'Türkçe' AND q.question_number BETWEEN 251 AND 300 THEN 'ales-3-sozel-1-testi'

                        -- ALES 2022
                        WHEN ey.year = 2022 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 1 AND 50 THEN 'ales-1-sayisal-1-testi'
                        WHEN ey.year = 2022 AND s.name = 'Türkçe' AND q.question_number BETWEEN 51 AND 100 THEN 'ales-1-sozel-1-testi'
                        WHEN ey.year = 2022 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 101 AND 150 THEN 'ales-2-sayisal-1-testi'
                        WHEN ey.year = 2022 AND s.name = 'Türkçe' AND q.question_number BETWEEN 151 AND 200 THEN 'ales-2-sozel-1-testi'
                        WHEN ey.year = 2022 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 201 AND 250 THEN 'ales-3-sayisal-1-testi'
                        WHEN ey.year = 2022 AND s.name = 'Türkçe' AND q.question_number BETWEEN 251 AND 300 THEN 'ales-3-sozel-1-testi'

                        -- ALES 2023
                        WHEN ey.year = 2023 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 1 AND 50 THEN 'ales-1-sayisal-1-testi'
                        WHEN ey.year = 2023 AND s.name = 'Türkçe' AND q.question_number BETWEEN 51 AND 100 THEN 'ales-1-sozel-1-testi'
                        WHEN ey.year = 2023 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 101 AND 150 THEN 'ales-2-sayisal-1-testi'
                        WHEN ey.year = 2023 AND s.name = 'Türkçe' AND q.question_number BETWEEN 151 AND 200 THEN 'ales-2-sozel-1-testi'
                        WHEN ey.year = 2023 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 201 AND 250 THEN 'ales-3-sayisal-1-testi'
                        WHEN ey.year = 2023 AND s.name = 'Türkçe' AND q.question_number BETWEEN 251 AND 300 THEN 'ales-3-sozel-1-testi'

                        -- ALES 2024
                        WHEN ey.year = 2024 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 1 AND 50 THEN 'ales-1-sayisal-1-testi'
                        WHEN ey.year = 2024 AND s.name = 'Türkçe' AND q.question_number BETWEEN 51 AND 100 THEN 'ales-1-sozel-1-testi'
                        WHEN ey.year = 2024 AND s.name IN ('Matematik', 'Geometri') AND q.question_number BETWEEN 101 AND 150 THEN 'ales-2-sayisal-1-testi'
                        WHEN ey.year = 2024 AND s.name = 'Türkçe' AND q.question_number BETWEEN 151 AND 200 THEN 'ales-2-sozel-1-testi'

                        ELSE lower(replace(s.name, ' ', '-')) || '-testi'
                    END

                ELSE 
                    lower(replace(s.name, ' ', '-')) || '-testi'
            END
        ) AS test_type
    FROM
        questions_question q
    JOIN questions_examtype et ON q.exam_type_id = et.id
    JOIN questions_examyear ey ON q.exam_year_id = ey.id
    JOIN questions_subject s ON q.subject_id = s.id
)

-- Perform the UPDATE using the CTE
UPDATE questions_question
SET image_url = 'https://storage.sinavsorularimerkezi.com/question-images/' 
                || cte.exam_type || '/' 
                || cte.exam_year || '/' 
                || cte.test_type || '/' 
                || questions_question.question_number || '.png'
FROM TestTypeCTE cte
WHERE questions_question.id = cte.question_id
  AND cte.test_type IS NOT NULL
  AND (questions_question.image_url IS NULL OR questions_question.image_url = '');

-- Commit the transaction to apply changes
COMMIT;
