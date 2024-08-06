work_india_inshorts_M_Pavan_Ganesh
API  round for workindia



- Clone this repo on your desktop
- Open command line/terminal in your machine
- install all the necessary files
- 
- Run the command ``` python app.py ``` 

- Open a browser(Chrome, firefox etc)

- Go to "http://localhost:5000"

- To sign up as an go to "http://localhost:5000/api/signup"

- To authenticate and login go to "http://localhost:5000/api/login"

- To create a shorts go to "http://localhost:5000/api/shorts/create"

- To see the shorts feed go to "(http://localhost:5000/api/shorts/feed)"

- To see the shorts filter go to "http://localhost:5000/api/shorts/filter"
  
-install mysql and create the databases as below

databases created as:
users:
CREATE TABLE users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    role ENUM('admin', 'user') DEFAULT 'user'
);

shorts:
CREATE TABLE shorts (
    short_id INT AUTO_INCREMENT PRIMARY KEY,
    category VARCHAR(50),
    title VARCHAR(255) NOT NULL,
    author VARCHAR(255),
    publish_date DATETIME,
    content TEXT,
    actual_content_link VARCHAR(255),
    image VARCHAR(255),
    upvote INT DEFAULT 0,
    downvote INT DEFAULT 0
);



