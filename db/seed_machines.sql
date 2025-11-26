-- seed_machines.sql
-- Seed the dim_machines table with some example machines.

INSERT INTO dim_machines (machine_id, location, model, install_date) VALUES
    (1, 'Plant A', 'X1000', '2022-01-15'),
    (2, 'Plant A', 'X1000', '2022-03-10'),
    (3, 'Plant B', 'Y2000', '2021-11-05'),
    (4, 'Plant B', 'Y2000', '2023-02-20'),
    (5, 'Plant C', 'Z3000', '2020-07-01')
ON CONFLICT (machine_id) DO NOTHING;
