# Git Workflow Standard

Version: v0.1

---

# Branch Strategy

默认分支：

main

开发分支：

develop

功能分支：

feature/功能名称

例如：

feature/login

feature/browser-manager

Bug 修复：

fix/问题名称

例如：

fix/login-error

---

# Commit Message

统一格式：

type: description

例如：

feat: add browser manager

fix: login failed

docs: update api standard

refactor: optimize account service

test: add login unit tests

---

# Pull Request

提交前必须：

- 代码可以运行
- 无明显 Bug
- 文档已同步更新
- 通过代码检查

---

# Version Tag

统一格式：

v1.0.0

v1.1.0

v1.1.1

---

# Release Rules

重大功能：

Minor Version

Bug 修复：

Patch Version

重大升级：

Major Version

---

Version

v0.1