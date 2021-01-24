
                                         	/* Имя             	            Тип	     		Обязательное	*/

/* Фильмы */
CREATE TABLE films(
  id INT AUTO_INCREMENT PRIMARY KEY,
  film_name VARCHAR(20) NOT NULL,			/* название	                      	VARCHAR	      	Да				*/
  descrip TEXT NOT NULL,            		/* описание	                      	TEXT	      	Да				*/
  year_of_production YEAR NOT NULL,     	/* год производства	              	YEAR	      	Да				*/
  country VARCHAR(20) NOT NULL,         	/* страна	                       	VARCHAR	      	Да				*/
  director VARCHAR(20) NOT NULL,        	/* режиссёр	                      	VARCHAR	      	Да      		*/
  scenar VARCHAR(20) NOT NULL,          	/* сценарист	                   	VARCHAR	     	Да				*/
  actors VARCHAR(20) NOT NULL,          	/* актёры	                      	VARCHAR	      	Да      		*/
  duration_min INT NOT NULL             	/* продолжительность (в минутах)	INT	          	Да				*/
);

/* Постеры */
CREATE TABLE posters(
    id INT AUTO_INCREMENT PRIMARY KEY,  
    poster_name VARCHAR(20) NOT NULL,   	/* название файла         			VARCHAR		    Да  			*/
    mime_t VARCHAR(20) NOT NULL,        	/* MIME-тип             	      	VARCHAR		    Да  			*/
    md5_h VARCHAR(20) NOT NULL,         	/* MD5-хэш             	          	VARCHAR		    Да  			*/
    film INT NOT NULL,               		/* фильм             	          	Внешний ключ	Да  			*/
	FOREIGN KEY(film) REFERENCES films(id) ON DELETE CASCADE
 );

/* Роли */
 CREATE TABLE roles(
    id INT AUTO_INCREMENT PRIMARY KEY,  
    role_name VARCHAR(20) NOT NULL,     	/* названние         				VARCHAR			Да  			*/
    descrip TEXT NOT NULL     				/* описание            	    		TEXT			Да  			*/
 );

/* Пользователи */
 CREATE TABLE users(
    id INT AUTO_INCREMENT PRIMARY KEY,  
    login VARCHAR(20) NOT NULL,       		/* логин         					VARCHAR			Да  			*/
    password_hash VARCHAR(256) NOT NULL, 	/* хэш пароля             	    	VARCHAR			Да  			*/
    last_name VARCHAR(20) NOT NULL,     	/* фамилия             	          	VARCHAR		    Да  			*/
    first_name VARCHAR(20) NOT NULL,    	/* имя             	          		VARCHAR			Да  			*/
	middle_name VARCHAR(20),				/* отчество            	    		VARCHAR			Да  			*/
	role INT NOT NULL,						/* роль								Внешний ключ	Да				*/
    FOREIGN KEY(role) REFERENCES roles(id)
 );

/* Рецензии */
 CREATE TABLE reviews(
    id INT AUTO_INCREMENT PRIMARY KEY,  
    film INT NOT NULL,       				/* фильм         					Внешний ключ	Да  			*/
    user INT NOT NULL,            			/* пользователь             	    Внешний ключ	Да  			*/
    mark INT NOT NULL,             			/* оценка             	          	INT		    	Да  			*/
    review TEXT NOT NULL,               	/* текст             	          	TEXT			Да  			*/
	date_of_create TIMESTAMP NOT NULL,		/* дата добавления             	    TIMESTAMP		Да  			*/
	FOREIGN KEY(film) REFERENCES films(id) ON DELETE CASCADE,
	FOREIGN KEY(user) REFERENCES users(id)
);

/* Жанры */
 CREATE TABLE genres(
    id INT AUTO_INCREMENT PRIMARY KEY,  
    genre_name VARCHAR(20) NOT NULL UNIQUE /* названние         				VARCHAR			Да  			*/
 );

/* Фильм-Жанр */
 CREATE TABLE film_genre(
    film INT,  
    genre INT,
	PRIMARY KEY (film, genre),
	FOREIGN KEY(film) REFERENCES films(id) ON DELETE CASCADE,
    FOREIGN KEY(genre) REFERENCES genres(id)
 );