import os
from flask import Flask, request, jsonify
import psycopg2
import redis
import json
import logging
from prometheus_flask_exporter import PrometheusMetrics

app = Flask(__name__)

metrics = PrometheusMetrics(app)
metrics.info('app_info', 'Application info', version='1.0.0')

redis_client = redis.Redis(
    host=os.environ["REDIS_HOST"],
    port=int(os.environ["REDIS_PORT"]),
    db=int(os.environ.get("REDIS_DB", 0)),
    decode_responses=True
)

def get_db_connection():
    return psycopg2.connect(
        database=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],          
        password=os.environ["POSTGRES_PASSWORD"], 
        host=os.environ["POSTGRES_HOST"],
        port=os.environ["POSTGRES_PORT"]
    )

@app.route('/')
def home():
    return {
        "status": "ok",
        "service": "flask-app",
        "message": "Hello from Flask!"
    }, 200

@app.route("/create", methods=["POST"])
def new_user():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        "INSERT INTO users (name, email, age) VALUES (%s, %s, %s) RETURNING *",
        (data['name'], data['email'], data['age'])
    )
    new_user = cur.fetchone()
    conn.commit()
    
    cur.close()
    conn.close()
    
    redis_client.delete("users:all")

    return jsonify({
        'id': new_user[0],
        'name': new_user[1],
        'email': new_user[2],
        'age': new_user[3]
    }), 200


@app.route("/read", methods=["GET"])
def get_users():
    cached_users = redis_client.get("users:all")
    logging.info("HELLLOGGG")
    if cached_users:
        users = json.loads(cached_users)
        return jsonify({
            "source": "redis",
            "data": users
        })


    conn = get_db_connection()

    cur = conn.cursor()
    cur.execute('''SELECT * FROM users''')
    data = cur.fetchall()

    cur.close()
    conn.close()

    users = []
    for row in data:
        users.append({
            'id': row[0],
            'name': row[1],
            'email': row[2],
            'age': row[3]
        })
    
    redis_client.setex("users:all", 60, json.dumps(users))

    return jsonify({
        "source": "database",
        "data": users
    })


@app.route("/update/<int:user_id>", methods=["PUT"])
def upd_user(user_id):
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute(
        "UPDATE users SET name=%s, email=%s, age=%s WHERE id=%s RETURNING *",
        (data['name'], data['email'], data['age'], user_id)
    )
    upd_user = cur.fetchone()
    conn.commit()
    
    cur.close()
    conn.close()
    
    if upd_user:
        redis_client.delete("users:all")
        redis_client.delete(f"user:{user_id}")

        return jsonify({
            'id': upd_user[0],
            'name': upd_user[1],
            'email': upd_user[2],
            'age': upd_user[3]
        })
    else:
        return jsonify({'error': 'User not found'}), 404


@app.route("/delete/<int:user_id>", methods=["DELETE"])
def del_user(user_id):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("DELETE FROM users WHERE id=%s RETURNING id", (user_id,))
    del_user = cur.fetchone()
    conn.commit()
    
    cur.close()
    conn.close()
    
    if del_user:
        redis_client.delete("users:all")
        redis_client.delete(f"user:{user_id}")

        return jsonify({'message': f'User {user_id} deleted'})
    else:
        return jsonify({'error': 'User not found'}), 404


if __name__ == "__main__":
    app.run(debug=True)