-- Схема и тестовые данные для базы bugboard.
-- Скрипт выполняется автоматически при первом запуске контейнера db.

CREATE TABLE IF NOT EXISTS bugs (
    id          SERIAL PRIMARY KEY,
    title       VARCHAR(200) NOT NULL,
    description TEXT DEFAULT '',
    severity    VARCHAR(10)  NOT NULL DEFAULT 'medium'
                CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    status      VARCHAR(12)  NOT NULL DEFAULT 'open'
                CHECK (status IN ('open', 'in_progress', 'closed')),
    created_at  TIMESTAMP    NOT NULL DEFAULT now()
);

INSERT INTO bugs (title, description, severity, status) VALUES
 ('Не работает вход по почте', 'После ввода пароля страница перезагружается', 'critical', 'open'),
 ('Кривая вёрстка на телефоне', 'Таблица вылезает за экран при ширине 375px', 'medium', 'in_progress'),
 ('Опечатка на главной', 'Написано "Добавть" вместо "Добавить"', 'low', 'closed'),
 ('Долго грузится список задач', 'При 500+ записях ответ больше 3 секунд', 'high', 'open'),
 ('Письмо приходит без темы', 'Уведомление о регистрации без Subject', 'medium', 'open');
