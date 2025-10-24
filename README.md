# Inventory-System
MHARSMC Inventory System

Steps to install:
1. Download vscode, python and postgresql
2. create .venv
3. create .env containing
    SECRET_KEY=django-insecure-!tc(1%#$w&v_fb$eg66v(2y)(y-g_^9xan^^0y*92u$jc5_+ss
    DB_NAME=inventory_system
    DB_USER=postgres
    DB_PASSWORD=admin
    DB_HOST=127.0.0.1
    DB_PORT=5432
4. create superadmin
5. run sql script for user permission:
    INSERT INTO public."Inventory_System_permissionoption" (id, name) VALUES
    (1, 'dashboard'),
    (2, 'equipment_management'),
    (3, 'equipment_tracking'),
    (4, 'maintenance_repairs'),
    (5, 'reports_audits'),
    (6, 'reference'),
    (7, 'user_role_management');
6. run sql script for service category:
    INSERT INTO public."Inventory_System_servicecategory" (id, name) VALUES
    (1, 'Repair of IT Equipment'),
    (2, 'Preventive Maintenance of IT Equipment'),
    (3, 'System Enhancement/Modification'),
    (4, 'Database Management and Administration (iHOMIS/iHOMIS+)'),
    (5, 'Network Installation'),
    (6, 'Internet Connections'),
    (7, 'Website Uploads'),
    (8, 'Technical Assistance'),
    (9, 'System Testing and Orientation'),
    (10, 'Training - iHOMIS Orientation/Computer Literacy'),
    (11, 'User Account Management'),
    (12, 'Others');


