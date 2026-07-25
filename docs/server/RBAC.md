# RBAC

Permissions are stable strings and evaluation is explicit through `AuthorizationService`. Missing assignments deny access. Built-in roles are `super_admin`, `organization_admin`, `publisher_manager`, `package_manager`, and `viewer`; `super_admin` owns every defined permission.
