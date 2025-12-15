import os
import pymysql

db_user = os.environ.get("CLOUD_SQL_USERNAME", "root")
db_password = os.environ.get("CLOUD_SQL_PASSWORD")
db_name = os.environ.get("CLOUD_SQL_DATABASE_NAME", "ROBOPETY")
db_connection_name = os.environ.get("CLOUD_SQL_CONNECTION_NAME")


def open_connection():
    if not all([db_user, db_password, db_name, db_connection_name]):
        raise RuntimeError(
            "Database configuration missing required environment variables"
        )
    unix_socket = f"/cloudsql/{db_connection_name}"
    try:
        conn = pymysql.connect(
            user=db_user,
            password=db_password,
            unix_socket=unix_socket,
            db=db_name,
            cursorclass=pymysql.cursors.DictCursor,
            ssl_disabled=False,  # Enable SSL/TLS for secure connections
            ssl_verify_cert=False,  # Don't verify cert for Unix socket (Cloud SQL handles encryption)
        )
        return conn
    except pymysql.MySQLError as e:
        raise RuntimeError(f"Failed to connect to database: {e}") from e


def get_robots():
    conn = open_connection()
    try:
        with conn.cursor() as cursor:
            query = "SELECT id, name FROM robots"
            result = cursor.execute(query)
            robots = cursor.fetchall()
            if result > 0:
                return {"status": "success", "data": robots}
            else:
                return {"status": "fail", "error": "No robots in DB"}
    finally:
        conn.close()


def validate_user(email):
    conn = open_connection()
    try:
        with conn.cursor() as cursor:
            query = "SELECT * FROM users WHERE email = %s"
            result = cursor.execute(query, (email,))
            users = cursor.fetchall()
            if result > 0:
                return {"status": "success", "data": users[0]}
            else:
                return {"status": "fail", "error": "Credentials are not correct."}
    finally:
        conn.close()


def get_user_by_id(userId):
    conn = open_connection()
    try:
        with conn.cursor() as cursor:
            query = "SELECT username FROM users WHERE id = %s"
            result = cursor.execute(query, (userId,))
            rows = cursor.fetchall()
            if result > 0:
                return {"status": "success", "data": rows[0]}
            else:
                return {"status": "fail", "error": "User not found"}
    except pymysql.Error as e:
        return {"status": "fail", "error": str(e)}
    finally:
        conn.close()


def get_user_by_username(username):
    conn = open_connection()
    try:
        with conn.cursor() as cursor:
            query = "SELECT * FROM users WHERE username = %s"
            result = cursor.execute(query, (username,))
            rows = cursor.fetchall()
            if result > 0:
                return {"status": "success", "data": rows[0]}
            else:
                return {"status": "fail", "error": "User not found"}
    finally:
        conn.close()


def get_robot_by_id(robotId):
    conn = open_connection()
    try:
        with conn.cursor() as cursor:
            query = "SELECT name FROM robots WHERE id = %s"
            result = cursor.execute(query, (robotId,))
            rows = cursor.fetchall()
            if result > 0:
                return {"status": "success", "data": rows[0]}
            else:
                return {"status": "fail", "error": "Robot not found"}
    except pymysql.Error as e:
        return {"status": "fail", "error": str(e)}
    finally:
        conn.close()


def add_user(email, username, password):
    conn = open_connection()
    try:
        with conn.cursor() as cursor:
            # check if email already used
            query = "SELECT COUNT(*) as count FROM users WHERE email = %s"
            cursor.execute(query, (email,))
            count = cursor.fetchone()
            if count and count["count"] > 0:
                return {"status": "fail", "error": "email already used"}
            # insert
            insert_query = "INSERT INTO users (email, username, password) VALUES (%s, %s, %s)"
            cursor.execute(insert_query, (email, username, password))
            conn.commit()
            # return inserted user
            validate = validate_user(email)
            return validate
    finally:
        conn.close()


def get_users():
    conn = open_connection()
    try:
        with conn.cursor() as cursor:
            result = cursor.execute("SELECT * FROM users")
            users = cursor.fetchall()
            if result > 0:
                return {"status": "success", "data": users}
            else:
                return {"status": "failed", "error": "empty database"}
    finally:
        conn.close()


def get_user_robot_by_user(userid):
    conn = open_connection()
    try:
        with conn.cursor() as cursor:
            query = (
                "SELECT * FROM user_robots WHERE user_id = %s "
                "ORDER BY id DESC LIMIT 1"
            )
            result = cursor.execute(query, (userid,))
            rows = cursor.fetchall()
            if result > 0:
                return {"status": "success", "data": rows[0]}
            else:
                return {"status": "fail", "error": "User does not have a robot"}
    finally:
        conn.close()


def get_user_robot_by_robot(robotid):
    conn = open_connection()
    try:
        with conn.cursor() as cursor:
            query = (
                "SELECT * FROM user_robots WHERE robot_id = %s "
                "ORDER BY id DESC LIMIT 1"
            )
            result = cursor.execute(query, (robotid,))
            rows = cursor.fetchall()
            if result > 0:
                return {"status": "success", "data": rows[0]}
            else:
                return {"status": "fail", "error": "No one picked this robot"}
    finally:
        conn.close()


def select_pet(userId, robotId):
    conn = open_connection()
    try:
        with conn.cursor() as cursor:
            query = (
                "INSERT INTO user_robots (user_id, robot_id, action) "
                "VALUES(%s, %s, 'pick')"
            )
            cursor.execute(query, (userId, robotId))
            conn.commit()
            if cursor.rowcount > 0:
                return {"status": "success", "data": cursor.rowcount}
            else:
                return {"status": "fail", "error": "Something went wrong"}
    except pymysql.Error as e:
        if conn:
            conn.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        conn.close()


def return_pet(userId, robotId):
    conn = open_connection()
    try:
        with conn.cursor() as cursor:
            query = (
                "INSERT INTO user_robots (user_id, robot_id, action) "
                "VALUES(%s, %s, 'return')"
            )
            cursor.execute(query, (userId, robotId))
            conn.commit()
            if cursor.rowcount > 0:
                return {"status": "success", "data": cursor.rowcount}
            else:
                return {"status": "fail", "error": "Something went wrong"}
    except pymysql.Error as e:
        if conn:
            conn.rollback()
        return {"status": "error", "error": str(e)}
    finally:
        conn.close()
