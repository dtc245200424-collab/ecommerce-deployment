from flask import Flask, jsonify, Response, request
import os
import psycopg2
from prometheus_client import Counter, generate_latest, CONTENT_TYPE_LATEST

app = Flask(__name__)
http_requests_total = Counter(
    "ecommerce_http_requests_total",
    "Tong so yeu cau HTTP den ung dung",
    ["method", "endpoint", "status"]
)
@app.after_request
def count_requests(response):
    http_requests_total.labels(
        request.method,
        request.endpoint or "unknown",
        str(response.status_code)
    ).inc()
    return response


@app.route("/metrics")
def metrics():
    return Response(
        generate_latest(),
        mimetype=CONTENT_TYPE_LATEST
    )
def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "db"),
        database=os.getenv("DB_NAME", "ecommerce"),
        user=os.getenv("DB_USER", "ecommerce"),
        password=os.getenv("DB_PASSWORD", "change_me"),
        connect_timeout=3,
    )

@app.route("/")
def home():
    return """
    <h1>Website Thương mại điện tử</h1>
    <p>Đề tài 9 - Triển khai và Quản trị Hệ thống Phần mềm</p>
    <p>Ứng dụng Flask đang hoạt động.</p>
    <a href="/health">Kiểm tra trạng thái</a> |
    <a href="/products">Danh sách sản phẩm</a>
    """

@app.route("/health")
def health():
    try:
        conn = get_db_connection()
        conn.close()
        return jsonify(status="ok", database="connected")
    except Exception:
        app.logger.exception("Database health check failed")
        return jsonify(status="error", database="disconnected"), 503

@app.route("/products")
def products():
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "CREATE TABLE IF NOT EXISTS products ("
            "id SERIAL PRIMARY KEY, "
            "name VARCHAR(150) NOT NULL, "
            "price NUMERIC(12,2) NOT NULL)"
        )
        cur.execute("SELECT COUNT(*) FROM products")
        count = cur.fetchone()[0]
        if count == 0:
            cur.executemany(
                "INSERT INTO products (name, price) VALUES (%s, %s)",
                [
                    ("Áo thun", 150000),
                    ("Giày thể thao", 450000),
                    ("Balo", 220000),
                ],
            )
        conn.commit()
        cur.execute("SELECT id, name, price FROM products ORDER BY id")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify([
            {"id": row[0], "name": row[1], "price": float(row[2])}
            for row in rows
        ])
    except Exception:
        app.logger.exception("Product query failed")
        return jsonify(error="Unable to load products"), 503

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
