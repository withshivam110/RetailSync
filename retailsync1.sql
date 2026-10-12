-- 1. Drop tables if re-running script from scratch (optional cleanup)
DROP TABLE IF EXISTS billing CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS inventory CASCADE;

-- 2. Create Tables
CREATE TABLE orders(
    order_id SERIAL PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date DATE NOT NULL,
    total_amount NUMERIC(10,2) NOT NULL CHECK(total_amount >= 0),
    status VARCHAR(15) DEFAULT 'pending',

    CONSTRAINT chk_order_status
        CHECK(status IN ('pending', 'shipped', 'delivered', 'cancelled', 'done'))
); 

CREATE TABLE inventory (
    product_id SERIAL PRIMARY KEY,
    quantity INT NOT NULL CHECK(quantity >= 0),
    restock_date DATE DEFAULT CURRENT_DATE,
    location VARCHAR(20) NOT NULL	
);

CREATE TABLE billing(
    bill_id SERIAL PRIMARY KEY,
    order_id INT NOT NULL,
    amount NUMERIC(10,2) NOT NULL CHECK(amount >= 0),
    bill_status VARCHAR(15) DEFAULT 'unpaid',
    bill_date DATE DEFAULT CURRENT_DATE,

    CONSTRAINT fk_billing_order
        FOREIGN KEY (order_id)
        REFERENCES orders(order_id)
        ON DELETE CASCADE,
    CONSTRAINT chk_billing_status
        CHECK (bill_status IN ('paid', 'unpaid', 'pending'))
);

-- 3. Insert into Orders (Creates order_id 1 through 20)
INSERT INTO orders(customer_id, order_date, total_amount, status)
VALUES
(101, '2026-05-23', 399.00, 'done'),
(102, '2026-05-29', 564.50, 'shipped'),
(103, '2026-06-02', 500.00, 'delivered'),
(104, '2026-06-05', 7500.00, 'pending'),
(105, '2026-06-12', 5320.00, 'pending'),
(106, '2026-06-12', 52000.00, 'cancelled'),
(107, '2026-06-18', 5320.20, 'delivered'),
(108, '2026-06-20', 300.00, 'delivered'),
(109, '2026-06-20', 7500.00, 'pending'),
(110, '2026-06-21', 7100.00, 'delivered'),
(111, '2026-07-25', 8200.00, 'delivered'),
(112, '2026-07-26', 1250.00, 'pending'),
(113, '2026-07-28', 999.00, 'shipped'),
(114, '2026-08-01', 4300.00, 'delivered'),
(115, '2026-08-03', 15000.00, 'cancelled'),
(116, '2026-08-05', 620.00, 'delivered'),
(117, '2026-08-07', 2100.00, 'pending'),
(118, '2026-08-10', 890.00, 'shipped'),
(119, '2026-08-12', 3300.00, 'delivered'),
(120, '2026-08-15', 450.00, 'done');

-- 4. Insert into Billing (Matches order_id 1 through 20)
INSERT INTO billing (order_id, amount, bill_status, bill_date)
VALUES
(1, 399.00, 'paid', DEFAULT),
(2, 564.50, 'paid', DEFAULT),
(3, 500.00, 'paid', DEFAULT),
(4, 7500.00, 'unpaid', DEFAULT),
(5, 5320.00, 'pending', DEFAULT),
(6, 52000.00, 'unpaid', DEFAULT),
(7, 5320.20, 'paid', DEFAULT),
(8, 300.00, 'paid', DEFAULT),
(9, 7500.00, 'pending', DEFAULT),
(10, 7100.00, 'paid', DEFAULT),
(11, 8200.00, 'paid', DEFAULT),
(12, 1250.00, 'pending', DEFAULT),
(13, 999.00, 'unpaid', DEFAULT),
(14, 4300.00, 'paid', DEFAULT),
(15, 15000.00, 'unpaid', DEFAULT),
(16, 620.00, 'paid', DEFAULT),
(17, 2100.00, 'pending', DEFAULT),
(18, 890.00, 'unpaid', DEFAULT),
(19, 3300.00, 'paid', DEFAULT),
(20, 450.00, 'paid', DEFAULT);

-- 5. Insert into Inventory
INSERT INTO inventory (quantity, restock_date, location)
VALUES
(60, DEFAULT, 'Store 1'),
(20, DEFAULT, 'Store 2'),
(85, DEFAULT, 'Store 1'),
(10, DEFAULT, 'Store 5'),
(20, DEFAULT, 'Store 2'),
(35, DEFAULT, 'Store 2'),
(20, DEFAULT, 'Store 2'),
(45, '2026-07-01', 'Store 3'),
(12, '2026-07-05', 'Store 4'),
(90, DEFAULT, 'Store 1'),
(5,  '2026-08-01', 'Store 2'),
(30, DEFAULT, 'Store 5'),
(75, DEFAULT, 'Store 3'),
(18, '2026-08-10', 'Store 4'),
(60, DEFAULT, 'Store 1'),
(22, DEFAULT, 'Store 2'),
(0,  '2026-09-01', 'Store 3'),
(40, DEFAULT, 'Store 5'),
(15, DEFAULT, 'Store 4'),
(50, '2026-09-10', 'Store 1');

-- 6. Verification Selects
SELECT * FROM orders;
SELECT * FROM billing;
SELECT * FROM inventory;

-- 7. Constraints Inspection
SELECT conname, pg_get_constraintdef(oid) 
FROM pg_constraint; 

-- 8. Test Updates and Queries
UPDATE orders SET total_amount = 6000 WHERE customer_id = 101;

-- 9. Performance Analysis (EXPLAIN ANALYZE)
EXPLAIN ANALYZE
SELECT billing.order_id, billing.bill_status, orders.total_amount
FROM billing
JOIN orders ON billing.order_id = orders.order_id
WHERE billing.bill_status = 'unpaid';

-- 10. Create Indices for Optimization
CREATE INDEX idx_billing_status ON billing(bill_status);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_inventory_quantity ON inventory(quantity);
