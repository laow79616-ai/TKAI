# Database Standard

Version: v0.1

---

# Database Principles

所有项目统一采用 PostgreSQL。

必须支持：

- Migration
- Index
- Foreign Key
- Transaction

---

# Naming Rules

Table

使用：

snake_case

例如：

user_account

email_account

proxy_pool

task_queue

禁止：

UserTable

userTable

---

# Primary Key

统一：

id

类型：

UUID

---

# Time Fields

所有表必须包含：

created_at

updated_at

---

# Delete Strategy

默认：

Soft Delete

字段：

deleted_at

---

# Index Rules

必须建立索引：

- Email
- Username
- TaskID
- Foreign Key

---

# Relationship

One To One

One To Many

Many To Many

统一使用外键。

---

# Migration

统一：

Alembic

禁止手工修改数据库。

---

# Version

v0.1