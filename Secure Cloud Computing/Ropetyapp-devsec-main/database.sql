create database if not exists ROBOPETY;

use ROBOPETY;


-- this is the table for the user
-- the user will have a username, password, and email
-- the username and email must be unique
-- the id will be auto incremented
create table if not exists users (
    id int not null auto_increment,
    username varchar(255) not null,
    password varchar(255) not null,
    email varchar(255) not null,
    primary key (id)
);


-- this is the table for the robots
-- the robot will have a name and a photo_url
-- the id will be auto incremented
create table if not exists robots (
    id int not null auto_increment,
    name varchar(255) not null,
    photo_url varchar(255) not null,
    primary key (id)
);


-- this is the table for the user_robots
-- the user_robots will have a user_id and a robot_id
-- the user_id and robot_id will be foreign keys
-- the action field tracks whether user picked or returned the robot
-- the id will be auto incremented
create table if not exists user_robots (
    id int not null auto_increment,
    user_id int not null,
    robot_id int not null,
    action varchar(50) not null,
    primary key (id),
    foreign key (user_id) references users(id),
    foreign key (robot_id) references robots(id)
);