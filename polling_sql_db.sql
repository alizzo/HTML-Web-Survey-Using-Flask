CREATE TABLE user (
    username varchar(50) NOT NULL,
	firstName varchar(50) NOT NULL,
	mi varchar(1) DEFAULT NULL,
	lastName varchar(50) DEFAULT NULL,
	emailaddress varchar(50) NOT NULL,
	password varchar(30) NOT NULL,
	role varchar(20) NOT NULL,
	PRIMARY KEY (username)
	);


CREATE TABLE question(
	questionID int (6) NOT NULL AUTO_INCREMENT,
	questionTitle varchar (20) NOT NULL,
	askQuestion varchar (200) NOT NULL,
	ansQuestionResponse1 varchar (200) NOT NULL,
    ansQuestionResponse2 varchar (200) NOT NULL,
    ansQuestionResponse3 varchar (200) NOT NULL,
    ansQuestionResponse4 varchar (200) NOT NULL,
    response varchar(200),
	PRIMARY KEY (questionID)
	);



CREATE TABLE answer (
	username varchar(50) NOT NULL,
	questionID int (6) NOT NULL,
	answerChoiceSelected varchar (1) NOT NULL,
	PRIMARY KEY (username, questionID)
	);



