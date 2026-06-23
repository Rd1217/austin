CREATE TABLE IF NOT EXISTS roles (
  id SERIAL PRIMARY KEY,
  system_role_key VARCHAR(80) UNIQUE NOT NULL,
  name VARCHAR(120) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS users (
  id SERIAL PRIMARY KEY,
  role_id INTEGER NOT NULL REFERENCES roles(id),
  username VARCHAR(120) UNIQUE NOT NULL,
  full_name VARCHAR(180) NOT NULL,
  email VARCHAR(180),
  phone VARCHAR(30),
  password_hash TEXT NOT NULL,
  is_active BOOLEAN NOT NULL DEFAULT TRUE,
  last_login_at TIMESTAMP NULL,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS leads (
  id SERIAL PRIMARY KEY,
  lead_number VARCHAR(40) UNIQUE,
  source VARCHAR(80) NOT NULL DEFAULT 'website',
  campaign VARCHAR(120),
  name VARCHAR(120) NOT NULL,
  phone VARCHAR(30),
  whatsapp_number VARCHAR(30),
  email VARCHAR(180),
  city VARCHAR(120) DEFAULT 'Pune',
  preferred_location VARCHAR(180),
  budget VARCHAR(180),
  property_type VARCHAR(80),
  buying_purpose VARCHAR(80),
  lead_status VARCHAR(40) NOT NULL DEFAULT 'new_lead',
  lead_score INTEGER NOT NULL DEFAULT 0,
  assigned_to_user_id INTEGER NULL REFERENCES users(id),
  interested_projects TEXT,
  last_follow_up_at TIMESTAMP NULL,
  next_follow_up_at TIMESTAMP NULL,
  lost_reason VARCHAR(400),
  lead_temperature VARCHAR(20) NOT NULL DEFAULT 'warm',
  message TEXT NOT NULL,
  inquiry_context TEXT,
  created_at TIMESTAMP NOT NULL DEFAULT NOW(),
  updated_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS lead_activities (
  id SERIAL PRIMARY KEY,
  lead_id INTEGER NOT NULL REFERENCES leads(id) ON DELETE CASCADE,
  actor_user_id INTEGER NULL REFERENCES users(id),
  activity_type VARCHAR(20) NOT NULL,
  subject VARCHAR(200) NOT NULL,
  details TEXT NOT NULL,
  due_at TIMESTAMP NULL,
  outcome VARCHAR(200),
  created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_roles_system_key ON roles(system_role_key);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE UNIQUE INDEX IF NOT EXISTS idx_leads_lead_number ON leads(lead_number);
CREATE INDEX IF NOT EXISTS idx_leads_created_at ON leads(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_status ON leads(lead_status);
CREATE INDEX IF NOT EXISTS idx_leads_email ON leads(email);
CREATE INDEX IF NOT EXISTS idx_leads_location ON leads(preferred_location);
CREATE INDEX IF NOT EXISTS idx_activities_lead_id ON lead_activities(lead_id, created_at DESC);
