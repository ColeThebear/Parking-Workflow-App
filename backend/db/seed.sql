INSERT INTO users (email, password_hash, role)
VALUES
('student1@suny.edu', '<argon2_hash_here>', 'PARKER'),
('student2@suny.edu', '<argon2_hash_here>', 'PARKER'),
('officer1@suny.edu', '<argon2_hash_here>', 'ENFORCEMENT'),
('operator@suny.edu', '<argon2_hash_here>', 'OPERATOR');

INSERT INTO parking_sessions (vehicle_plate, zone, active, started_at, ended_at, user_id)
VALUES
('ABC123',  'Student Lot A', false, NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour', NULL),
('SUNY456', 'Student Lot B', false, NOW() - INTERVAL '3 hours', NOW() - INTERVAL '2 hours', NULL),
('PARK789', 'Faculty Lot',   false, NOW() - INTERVAL '2 hours', NOW() - INTERVAL '1 hour', NULL),
('NYS102',  'Visitor Lot',   false, NOW() - INTERVAL '1 day',   NOW() - INTERVAL '23 hours', NULL);
