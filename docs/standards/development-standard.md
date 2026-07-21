# Development Standard

Version: v0.1

---

# General Principles

所有代码必须遵循：

- 可读性优先
- 模块化设计
- 单一职责原则（SRP）
- 不重复自己（DRY）
- 保持简单（KISS）

---

# Naming Rules

## 文件

使用：

snake_case

例如：

user_service.py

browser_manager.py

---

## 类

使用：

PascalCase

例如：

UserService

BrowserManager

---

## 方法

使用：

snake_case

例如：

create_account()

login_user()

---

# Function Rules

每个函数只负责一件事情。

函数长度建议：

- ≤ 50 行

复杂逻辑拆分为多个私有函数。

---

# Comments

代码应尽量自解释。

复杂业务逻辑必须添加注释。

---

# Error Handling

禁止忽略异常。

必须记录日志。

统一返回标准错误信息。

---

# Logging

统一使用日志系统。

禁止直接使用 print() 输出调试信息。

---

# Testing

新增功能必须编写测试。

修复 Bug 时应补充对应测试。

---

Version

v0.1