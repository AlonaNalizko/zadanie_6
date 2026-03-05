CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL,
    age INTEGER
);

INSERT INTO users (name, email, age) VALUES
    ('Вася', 'vasya@mail.ru', 25),
    ('Петя', 'petya@mail.ru', 30),
    ('Маша', 'masha@mail.ru', 22),
    ('Даша', 'dasha@mail.ru', 27);