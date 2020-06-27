CREATE TABLE Users (
    user_id SERIAL PRIMARY KEY,
    username VARCHAR NOT NULL,
    password VARCHAR NOT NULL,
    email VARCHAR NULL
);

CREATE TABLE Books (
    book_id SERIAL PRIMARY KEY,
    isbn VARCHAR NOT NULL,
    title VARCHAR NOT NULL,
    author VARCHAR NOT NULL,
    year INTEGER NOT NULL
);

CREATE TABLE Reviews (
    review_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES Users NOT NULL,
    book_id INTEGER REFERENCES Books NOT NULL,
    review_rate INTEGER NOT NULL,
    review_content TEXT NOT NULL
);
