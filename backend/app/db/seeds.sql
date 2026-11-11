-- =============================================================================
-- Society Savings & Loan Management Platform
-- Initial Seed Data (Demo Society, Standard Chart of Accounts, Roles & Test Users)
-- =============================================================================

-- 1. Standard Permissions
INSERT INTO permissions (id, key, description, module) VALUES
    ('b0000000-0000-0000-0000-000000000001', 'society:manage', 'Manage society settings and policies', 'society'),
    ('b0000000-0000-0000-0000-000000000002', 'member:invite', 'Generate member invitation links', 'membership'),
    ('b0000000-0000-0000-0000-000000000003', 'member:view', 'View members directory and profiles', 'membership'),
    ('b0000000-0000-0000-0000-000000000004', 'member:update_role', 'Assign committee roles to members', 'membership'),
    ('b0000000-0000-0000-0000-000000000005', 'contribution:view', 'View member contribution obligations', 'contribution'),
    ('b0000000-0000-0000-0000-000000000006', 'contribution:record', 'Record confirmed member contribution payments', 'contribution'),
    ('b0000000-0000-0000-0000-000000000007', 'ledger:view', 'Inspect society double-entry cashbook and ledger', 'ledger'),
    ('b0000000-0000-0000-0000-000000000008', 'ledger:post_entry', 'Post manual double-entry adjustments', 'ledger'),
    ('b0000000-0000-0000-0000-000000000009', 'loan:apply', 'Apply for a member loan from the pool', 'loan'),
    ('b0000000-0000-0000-0000-000000000010', 'loan:approve', 'Approve or reject member loan applications', 'loan'),
    ('b0000000-0000-0000-0000-000000000011', 'loan:disburse', 'Disburse approved and reserved loans', 'loan'),
    ('b0000000-0000-0000-0000-000000000012', 'loan:view', 'View loan portfolio and FIFO queue', 'loan'),
    ('b0000000-0000-0000-0000-000000000013', 'report:view', 'Generate collection registers, arrears and statements', 'reports'),
    ('b0000000-0000-0000-0000-000000000014', 'audit:view', 'Access immutable audit logs', 'audit')
ON CONFLICT (key) DO NOTHING;

-- 2. Demo Society
INSERT INTO societies (id, legal_name, display_name, registration_number, address, jurisdiction, currency, timezone, financial_year_start, status) VALUES
    ('a0000000-0000-0000-0000-000000000001', 'Greenwood Mutual Aid & Thrift Society', 'Greenwood Society', 'REG-2026-GW-001', '12 Community Square, Mumbai, MH', 'Maharashtra, India', 'INR', 'Asia/Kolkata', '04-01', 'ACTIVE')
ON CONFLICT (id) DO NOTHING;

-- 3. Standard Roles for Demo Society
INSERT INTO roles (id, society_id, name, description, is_system) VALUES
    ('c0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'President', 'Chief Executive Officer with comprehensive oversight and loan approval authority', TRUE),
    ('c0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'Vice President', 'Executive oversight and secondary approval quorum', TRUE),
    ('c0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'Secretary', 'Administrative workflows, invitations, notices and meetings', TRUE),
    ('c0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001', 'Treasurer', 'Financial custodian: ledger, collections, disbursements, and statements', TRUE),
    ('c0000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000001', 'Member', 'General society participant: monthly savings and loan borrower', TRUE)
ON CONFLICT (id) DO NOTHING;

-- 4. Role Permissions Mapping
-- President: All permissions
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'c0000000-0000-0000-0000-000000000001', id FROM permissions
ON CONFLICT DO NOTHING;

-- Treasurer: Financial permissions + member view + reports + audit
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'c0000000-0000-0000-0000-000000000004', id FROM permissions 
WHERE key IN ('contribution:view', 'contribution:record', 'ledger:view', 'ledger:post_entry', 'loan:disburse', 'loan:view', 'report:view', 'audit:view', 'member:view')
ON CONFLICT DO NOTHING;

-- Secretary: Member management + invitations + reports
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'c0000000-0000-0000-0000-000000000003', id FROM permissions 
WHERE key IN ('member:invite', 'member:view', 'member:update_role', 'loan:view', 'report:view')
ON CONFLICT DO NOTHING;

-- Member: Apply loan, view own contributions and permitted reports
INSERT INTO role_permissions (role_id, permission_id)
SELECT 'c0000000-0000-0000-0000-000000000005', id FROM permissions 
WHERE key IN ('loan:apply', 'loan:view', 'contribution:view')
ON CONFLICT DO NOTHING;

-- 5. Standard Chart of Accounts for Greenwood Society
INSERT INTO ledger_accounts (id, society_id, account_code, account_name, account_type, currency, is_active) VALUES
    ('d0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', '1010', 'Cash / Bank Main Pool', 'ASSET', 'INR', TRUE),
    ('d0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', '1020', 'Loan Receivables (Principal)', 'ASSET', 'INR', TRUE),
    ('d0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', '2010', 'Pending Loan Reserves', 'LIABILITY', 'INR', TRUE),
    ('d0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001', '3010', 'Member Contributions Capital', 'EQUITY', 'INR', TRUE),
    ('d0000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000001', '4010', 'Loan Interest Income', 'INCOME', 'INR', TRUE),
    ('d0000000-0000-0000-0000-000000000006', 'a0000000-0000-0000-0000-000000000001', '4020', 'Late Fee & Penalty Income', 'INCOME', 'INR', TRUE)
ON CONFLICT (id) DO NOTHING;

-- 6. Demo Users (Corresponding to Dev Personas)
INSERT INTO users (id, email, full_name, account_status) VALUES
    ('e0000000-0000-0000-0000-000000000000', 'admin@platform.local', 'Platform Super Administrator', 'ACTIVE'),
    ('e0000000-0000-0000-0000-000000000001', 'president@society.local', 'Rajesh Sharma (President)', 'ACTIVE'),
    ('e0000000-0000-0000-0000-000000000002', 'treasurer@society.local', 'Kavita Iyer (Treasurer)', 'ACTIVE'),
    ('e0000000-0000-0000-0000-000000000003', 'secretary@society.local', 'Sunil Verma (Secretary)', 'ACTIVE'),
    ('e0000000-0000-0000-0000-000000000004', 'member1@society.local', 'Arjun Patel (Member 1)', 'ACTIVE'),
    ('e0000000-0000-0000-0000-000000000005', 'member2@society.local', 'Priya Deshmukh (Member 2)', 'ACTIVE')
ON CONFLICT (email) DO NOTHING;

-- 7. Society Memberships
INSERT INTO society_memberships (id, society_id, user_id, member_number, status) VALUES
    ('f0000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000001', 'MEM-001', 'ACTIVE'),
    ('f0000000-0000-0000-0000-000000000002', 'a0000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000002', 'MEM-002', 'ACTIVE'),
    ('f0000000-0000-0000-0000-000000000003', 'a0000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000003', 'MEM-003', 'ACTIVE'),
    ('f0000000-0000-0000-0000-000000000004', 'a0000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000004', 'MEM-004', 'ACTIVE'),
    ('f0000000-0000-0000-0000-000000000005', 'a0000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000005', 'MEM-005', 'ACTIVE')
ON CONFLICT (society_id, user_id) DO NOTHING;

-- 8. Assign Roles to Memberships
INSERT INTO membership_roles (membership_id, role_id) VALUES
    ('f0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001'), -- President
    ('f0000000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000004'), -- Treasurer
    ('f0000000-0000-0000-0000-000000000003', 'c0000000-0000-0000-0000-000000000003'), -- Secretary
    ('f0000000-0000-0000-0000-000000000004', 'c0000000-0000-0000-0000-000000000005'), -- Member 1
    ('f0000000-0000-0000-0000-000000000005', 'c0000000-0000-0000-0000-000000000005')  -- Member 2
ON CONFLICT DO NOTHING;

-- 9. Default Policies for Greenwood Society
-- Monthly Contribution: ₹2,000 (200,000 paise)
INSERT INTO contribution_policies (id, society_id, amount_minor, currency, frequency, due_day, grace_period_days, late_fee_minor, status) VALUES
    ('10000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 200000, 'INR', 'MONTHLY', 5, 5, 10000, 'ACTIVE')
ON CONFLICT (id) DO NOTHING;

-- Loan Policy: 8% Annual Reducing Balance, ₹10,000 to ₹100,000, 1-24 months
INSERT INTO loan_policies (id, society_id, interest_rate, interest_period, interest_method, calculation_convention, min_amount_minor, max_amount_minor, min_tenure_months, max_tenure_months, allocation_rule, partial_allocation_allowed, status) VALUES
    ('20000000-0000-0000-0000-000000000001', 'a0000000-0000-0000-0000-000000000001', 0.0800, 'ANNUAL', 'REDUCING_BALANCE', 'MONTHLY_AMORTIZATION', 1000000, 10000000, 1, 24, 'STRICT_FIFO', FALSE, 'ACTIVE')
ON CONFLICT (id) DO NOTHING;
