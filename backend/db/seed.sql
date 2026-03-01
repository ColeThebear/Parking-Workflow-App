INSERT INTO users (email, password_hash, role)
VALUES
('student1@suny.edu', 'hash_here', 'PARKER'), -- Replace 'hash_here' with actual hashed passwords
('student2@suny.edu', 'hash_here', 'PARKER'), -- Add more student users as needed
('officer1@suny.edu', 'hash_here', 'ENFORCEMENT'),
('operator@suny.edu', 'hash_here', 'OPERATOR');

INSERT INTO parking_sessions (vehicle_plate, zone, active, started_at, ended_at)
VALUES
('ABC123', 'Student Lot A', true, NOW() - INTERVAL '20 minutes', NULL),
('SUNY456', 'Student Lot B', true, NOW() - INTERVAL '5 minutes', NULL),
('PARK789', 'Faculty Lot', false, NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour'),
('NYS102', 'Visitor Lot', false, NOW() - INTERVAL '1 day', NOW() - INTERVAL '23 hours');

