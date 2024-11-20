CREATE DATABASE project1;

CREATE TABLE admin (
	id INT PRIMARY KEY AUTO_INCREMENT,
    username CHAR(50) NOT NULL UNIQUE,
    pword CHAR(250) NOT NULL,
    email CHAR(100) NOT NULL UNIQUE
);

CREATE TABLE user (
	id INT PRIMARY KEY AUTO_INCREMENT,
    username CHAR(50) NOT NULL UNIQUE,
    pword CHAR(250) NOT NULL,
    email CHAR(100) NOT NULL UNIQUE,
    address CHAR(255) NOT NULL
);

CREATE TABLE inventory (
	id INT PRIMARY KEY AUTO_INCREMENT,
    productName CHAR(50) NOT NULL UNIQUE,
    userID INT NOT NULL,
    description CHAR(255),
    price DECIMAL(5, 2) NOT NULL,
    quantity INT NOT NULL DEFAULT 0,
    FOREIGN KEY (userID) REFERENCES user(id)
);

INSERT INTO admin (username, pword, email) VALUES ('ocean', 'ocean', 'a@a.com');
SELECT * FROM admin;
SELECT * FROM user;
SELECT * FROM inventory;