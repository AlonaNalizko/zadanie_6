wrk.method = "POST"
wrk.body = '{"name": "Test User", "email": "test@example.com", "age": 25}'
wrk.headers["Content-Type"] = "application/json"