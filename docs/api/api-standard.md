# API Standard

Version: v0.1

---

# API Design Principles

所有 API 必须遵循 RESTful 风格。

---

# URL Naming

正确：

GET /api/users

GET /api/users/{id}

POST /api/users

PUT /api/users/{id}

DELETE /api/users/{id}

禁止：

getUser

deleteUser

updateUser

---

# Response Format

成功：

```json
{
    "success": true,
    "message": "OK",
    "data": {}
}
```

失败：

```json
{
    "success": false,
    "message": "Error",
    "error": {}
}
```

---

# Status Code

200 OK

201 Created

400 Bad Request

401 Unauthorized

403 Forbidden

404 Not Found

500 Server Error

---

# Version

统一使用：

/api/v1/