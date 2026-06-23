import { useCallback, useEffect, useMemo, useState } from 'react';

const API_BASE = import.meta.env.VITE_API_BASE_URL || '';

const services = [
  {
    id: 1,
    title: 'Residential Properties',
    description:
      'Find verified flats, apartments, and villas from trusted developers across Pune and PCMC.',
    icon: 'RP'
  },
  {
    id: 2,
    title: 'Commercial Properties',
    description:
      'Explore shops, office spaces, and commercial investments with strong growth and rental potential.',
    icon: 'CP'
  },
  {
    id: 3,
    title: 'Developer Tie-Ups',
    description:
      'Access direct developer pricing, new launches, and curated options through strong builder relationships.',
    icon: 'DT'
  },
  {
    id: 4,
    title: 'Property Consultation',
    description:
      'Get location, budget, and investment guidance based on your buying goal and timeline.',
    icon: 'PC'
  }
];

const metrics = {
  total_sales_generated: 5000000000,
  client_satisfaction: 98,
  years_experience: 15,
  team_members: 50
};

const leadershipProfiles = [
  {
    name: 'Umesh Kirodiwal',
    role: 'Founder & MD',
    quote:
      'From understanding the market to building a legacy within it.',
    image: '/team/umesh-kirodiwal.png'
  },
  {
    name: 'Abhishek Gharge',
    role: 'Founder & MD',
    quote:
      'Once chasing sales, now driving vision.',
    image: '/team/abhishek-gharge.png'
  },
  {
    name: 'Ashish Nalawade',
    role: 'Founder & MD',
    quote:
      'Built on ground experience, driven by entrepreneurial vision.',
    image: '/team/ashish-nalawade.png'
  },
  {
    name: 'Karan Dhankude',
    role: 'Founder & MD',
    quote:
      'Driven by a vision to build a landmark organization.',
    image: '/team/karan-dhankude.png'
  }
];

const featuredLocations = [
  {
    name: 'Hinjawadi',
    note: 'IT hub with strong rental demand and investor interest.'
  },
  {
    name: 'Baner',
    note: 'Premium residential market with lifestyle and business connectivity.'
  },
  {
    name: 'Tathawade',
    note: 'Fast-growing micro-market with strong future appreciation potential.'
  },
  {
    name: 'Ravet',
    note: 'Affordable housing destination with expanding connectivity.'
  },
  {
    name: 'Pimple Saudagar',
    note: 'Established neighborhood with balanced end-user and investor appeal.'
  }
];

const statusOptions = [
  'new_lead',
  'attempted',
  'contacted',
  'qualified',
  'visit_planned',
  'visit_done',
  'negotiation',
  'booking_in_progress',
  'booked',
  'lost',
  'nurture'
];

function formatSalesAmount(value) {
  if (!value) return '0';
  const bill = Number(value) / 1000000000;
  return `${bill.toFixed(0)}B+`;
}

function LogoBlock() {
  return (
    <div className="logo-block" aria-label="Four Square Group logo">
      <div className="logo-grid">
        <span className="sq sq-1" />
        <span className="sq sq-2" />
        <span className="sq sq-3" />
        <span className="sq sq-4" />
      </div>
      <p className="logo-title">FOUR SQUARE</p>
      <p className="logo-sub">GROUP</p>
      <p className="logo-tag">Structured To Succeed</p>
    </div>
  );
}

function useRevealAnimation() {
  useEffect(() => {
    const elements = document.querySelectorAll('.reveal');
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) entry.target.classList.add('revealed');
        });
      },
      { threshold: 0.2 }
    );

    elements.forEach((el) => observer.observe(el));
    return () => observer.disconnect();
  }, []);
}

function HomePage() {
  useRevealAnimation();

  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    message: ''
  });
  const [submitStatus, setSubmitStatus] = useState('idle');

  const stats = useMemo(
    () => [
      { label: 'Client Satisfaction', value: `${metrics.client_satisfaction || 0}%` },
      { label: 'Project Value Guided', value: formatSalesAmount(metrics.total_sales_generated) },
      { label: 'Years in Market', value: `${metrics.years_experience || 0}+` },
      { label: 'Builder Connections', value: `${metrics.team_members || 0}+` }
    ],
    []
  );

  function onInputChange(event) {
    const { name, value } = event.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSubmitStatus('loading');

    try {
      const response = await fetch(`${API_BASE}/api/contact`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
      });

      if (!response.ok) throw new Error('Contact submission failed');

      setSubmitStatus('success');
      setFormData({ name: '', email: '', company: '', message: '' });
    } catch (error) {
      console.error(error);
      setSubmitStatus('error');
    }
  }

  return (
    <div className="page-shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />

      <header className="topbar">
        <a href="#home" className="brand">
          <span className="brand-grid" />
          Four Square Group
        </a>
        <nav>
          <a href="#services">Services</a>
          <a href="#locations">Locations</a>
          <a href="#leadership">Leadership</a>
          <a href="#contact">Contact</a>
        </nav>
      </header>

      <main>
        <section id="home" className="hero">
          <div className="hero-content reveal">
            <p className="eyebrow">Pune | PCMC Real Estate Partner</p>
            <h1>Find the Right Property Through Direct Developer Access</h1>
            <p>
              Four Square Group connects homebuyers and investors with verified residential and
              commercial projects across Pune and PCMC, backed by market guidance and trusted
              developer relationships.
            </p>
            <div className="hero-actions">
              <a href="#contact" className="btn-primary">
                Book Free Consultation
              </a>
              <a href="#locations" className="btn-secondary">
                Explore Locations
              </a>
            </div>
            <div className="capability-ribbon reveal">
              <span>Verified Projects</span>
              <span>Direct Developer Deals</span>
              <span>Site Visit Support</span>
            </div>
          </div>

          <div className="hero-side reveal">
            <LogoBlock />
            <div className="hero-grid">
              {stats.map((stat, idx) => (
                <article
                  key={stat.label}
                  className="stat-card reveal"
                  style={{ '--delay': `${idx * 0.09}s` }}
                >
                  <h3>{stat.value}</h3>
                  <p>{stat.label}</p>
                </article>
              ))}
            </div>
          </div>
        </section>

        <section id="services" className="section">
          <div className="section-header reveal">
            <p className="eyebrow">Core Services</p>
            <h2>Structured Property Guidance for Buyers, Investors, and Business Owners</h2>
          </div>
          <div className="card-grid">
            {services.map((service, idx) => (
              <article
                key={service.id}
                className="service-card reveal"
                style={{ '--delay': `${idx * 0.08}s` }}
              >
                <span className="service-icon">{service.icon}</span>
                <h3>{service.title}</h3>
                <p>{service.description}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="locations" className="section">
          <div className="section-header reveal">
            <p className="eyebrow">Featured Locations</p>
            <h2>Projects Across Pune and PCMC’s Most In-Demand Markets</h2>
          </div>
          <div className="card-grid">
            {featuredLocations.map((location, idx) => (
              <article
                key={location.name}
                className="service-card reveal"
                style={{ '--delay': `${idx * 0.08}s` }}
              >
                <span className="service-icon">LO</span>
                <h3>{location.name}</h3>
                <p>{location.note}</p>
              </article>
            ))}
          </div>
        </section>

        <section id="leadership" className="section">
          <div className="section-header reveal">
            <p className="eyebrow">Leadership</p>
            <h2>Founders Focused on Trusted Advisory, Strong Market Reach, and Buyer Confidence</h2>
          </div>
          <div className="leader-grid">
            {leadershipProfiles.map((leader, idx) => (
              <article
                key={leader.name}
                className="leader-card reveal"
                style={{ '--delay': `${idx * 0.1}s` }}
              >
                <div className="leader-portrait-wrap">
                  <img src={leader.image} alt={leader.name} loading="lazy" className="leader-portrait" />
                </div>
                <div className="leader-copy">
                  <p className="eyebrow">Founder Profile</p>
                  <h3>{leader.name}</h3>
                  <p className="customer-role">{leader.role}</p>
                  <blockquote>{leader.quote}</blockquote>
                </div>
              </article>
            ))}
          </div>
        </section>

        <section id="contact" className="section contact">
          <div className="section-header reveal">
            <p className="eyebrow">Contact Us</p>
            <h2>Get Best Price and Offers Direct From Developer</h2>
          </div>
          <div className="contact-layout">
            <form className="contact-form reveal" onSubmit={handleSubmit}>
              <input
                type="text"
                name="name"
                placeholder="Full Name"
                value={formData.name}
                onChange={onInputChange}
                required
              />
              <input
                type="email"
                name="email"
                placeholder="Email Address"
                value={formData.email}
                onChange={onInputChange}
                required
              />
              <input
                type="text"
                name="company"
                placeholder="Budget / Preferred Location"
                value={formData.company}
                onChange={onInputChange}
                required
              />
              <textarea
                name="message"
                rows="5"
                placeholder="Tell us what kind of property you are looking for"
                value={formData.message}
                onChange={onInputChange}
                required
              />
              <button type="submit" disabled={submitStatus === 'loading'}>
                {submitStatus === 'loading' ? 'Submitting...' : 'Send Message'}
              </button>
              {submitStatus === 'success' && (
                <p className="feedback success">Thank you. We received your request.</p>
              )}
              {submitStatus === 'error' && (
                <p className="feedback error">Submission failed. Please try again.</p>
              )}
            </form>

            <aside className="contact-card reveal">
              <h3>Your Trusted Real Estate Partner</h3>
              <p>Direct developer connections for residential and commercial projects.</p>
              <p>Focused on Pune and PCMC locations including Baner, Hinjawadi, Tathawade, Ravet, and Pimple Saudagar.</p>
              <p>Book a consultation, compare projects, and plan your site visit with our team.</p>
            </aside>
          </div>
        </section>
      </main>

      <footer>
        <p>© {new Date().getFullYear()} Four Square Group. All rights reserved.</p>
      </footer>
    </div>
  );
}

function AdminPage() {
  const [loginForm, setLoginForm] = useState({ username: '', password: '' });
  const [token, setToken] = useState(localStorage.getItem('crm_token') || '');
  const [adminName, setAdminName] = useState(localStorage.getItem('crm_admin') || '');
  const [adminRole, setAdminRole] = useState(localStorage.getItem('crm_role') || '');
  const [adminError, setAdminError] = useState('');

  const [leads, setLeads] = useState([]);
  const [users, setUsers] = useState([]);
  const [timelineByLead, setTimelineByLead] = useState({});
  const [activityDrafts, setActivityDrafts] = useState({});
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loadingContacts, setLoadingContacts] = useState(false);
  const [totalLeads, setTotalLeads] = useState(0);
  const [page, setPage] = useState(0);
  const limit = 10;

  const loadUsers = useCallback(async () => {
    if (!token) return;
    try {
      const res = await fetch(`${API_BASE}/api/admin/users`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!res.ok) throw new Error('Could not load users');
      const data = await res.json();
      setUsers(data.users || []);
    } catch (err) {
      console.error(err);
    }
  }, [token]);

  const loadLeads = useCallback(async () => {
    if (!token) return;
    setLoadingContacts(true);
    try {
      const params = new URLSearchParams();
      params.set('limit', String(limit));
      params.set('offset', String(page * limit));
      if (statusFilter) params.set('lead_status', statusFilter);
      if (search.trim()) params.set('q', search.trim());

      const res = await fetch(`${API_BASE}/api/admin/leads?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
      });

      if (res.status === 401) {
        localStorage.removeItem('crm_token');
        localStorage.removeItem('crm_admin');
        localStorage.removeItem('crm_role');
        setToken('');
        setAdminName('');
        setAdminRole('');
        setLeads([]);
        return;
      }

      if (!res.ok) throw new Error('Could not load leads');

      const data = await res.json();
      setLeads(data.leads || []);
      setTotalLeads(data.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingContacts(false);
    }
  }, [token, page, statusFilter, search]);

  useEffect(() => {
    loadUsers();
  }, [loadUsers]);

  useEffect(() => {
    loadLeads();
  }, [loadLeads]);

  useEffect(() => {
    if (!token) return undefined;
    const id = setInterval(() => {
      loadLeads();
    }, 900000);
    return () => clearInterval(id);
  }, [token, loadLeads]);

  async function handleAdminLogin(event) {
    event.preventDefault();
    setAdminError('');

    try {
      const res = await fetch(`${API_BASE}/api/admin/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(loginForm)
      });

      if (!res.ok) throw new Error('Login failed');

      const data = await res.json();
      setToken(data.access_token);
      setAdminName(data.admin.username);
      setAdminRole(data.admin.role_name || data.admin.role_key);
      localStorage.setItem('crm_token', data.access_token);
      localStorage.setItem('crm_admin', data.admin.username);
      localStorage.setItem('crm_role', data.admin.role_name || data.admin.role_key);
      setPage(0);
    } catch (err) {
      setAdminError('Invalid credentials or too many attempts.');
    }
  }

  function logout() {
    setToken('');
    setAdminName('');
    setAdminRole('');
    setLeads([]);
    localStorage.removeItem('crm_token');
    localStorage.removeItem('crm_admin');
    localStorage.removeItem('crm_role');
  }

  async function loadTimeline(leadId) {
    try {
      const res = await fetch(`${API_BASE}/api/admin/leads/${leadId}/timeline`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Could not load timeline');
      const data = await res.json();
      setTimelineByLead((prev) => ({ ...prev, [leadId]: data.timeline || [] }));
    } catch (err) {
      console.error(err);
    }
  }

  async function updateLead(leadId, patchData) {
    try {
      const res = await fetch(`${API_BASE}/api/admin/leads/${leadId}`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify(patchData)
      });

      if (!res.ok) throw new Error('Could not update contact');

      const data = await res.json();
      setLeads((prev) =>
        prev.map((item) =>
          item.id === leadId ? { ...item, ...data.lead } : item
        )
      );
    } catch (err) {
      console.error(err);
    }
  }

  async function addActivity(leadId) {
    const draft = activityDrafts[leadId];
    if (!draft?.subject || !draft?.details) return;

    try {
      const res = await fetch(`${API_BASE}/api/admin/leads/${leadId}/activities`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          activity_type: draft.activity_type || 'note',
          subject: draft.subject,
          details: draft.details
        })
      });
      if (!res.ok) throw new Error('Could not add activity');
      const data = await res.json();
      setTimelineByLead((prev) => ({
        ...prev,
        [leadId]: [data.activity, ...(prev[leadId] || [])]
      }));
      setActivityDrafts((prev) => ({
        ...prev,
        [leadId]: { activity_type: 'note', subject: '', details: '' }
      }));
      await loadLeads();
    } catch (err) {
      console.error(err);
    }
  }

  async function downloadBackup() {
    try {
      const res = await fetch(`${API_BASE}/api/admin/backup`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (!res.ok) throw new Error('Backup failed');
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `crm-backup-${Date.now()}.zip`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error(err);
    }
  }

  const totalPages = Math.max(1, Math.ceil(totalLeads / limit));

  return (
    <div className="page-shell">
      <div className="ambient ambient-a" />
      <div className="ambient ambient-b" />

      <header className="topbar">
        <a href="/" className="brand">
          <span className="brand-grid" />
          Four Square Group CRM
        </a>
      </header>

      <main>
        <section className="section" style={{ paddingTop: '7rem' }}>
          <div className="section-header reveal revealed">
            <p className="eyebrow">Admin CRM</p>
            <h2>Secure Contact Pipeline Management</h2>
          </div>

          {!token ? (
            <form className="admin-login reveal revealed" onSubmit={handleAdminLogin}>
              <h3>Administrator Login</h3>
              <input
                type="text"
                placeholder="Username"
                value={loginForm.username}
                onChange={(e) => setLoginForm((prev) => ({ ...prev, username: e.target.value }))}
                required
              />
              <input
                type="password"
                placeholder="Password"
                value={loginForm.password}
                onChange={(e) => setLoginForm((prev) => ({ ...prev, password: e.target.value }))}
                required
              />
              <button type="submit">Login Securely</button>
              {adminError && <p className="feedback error">{adminError}</p>}
            </form>
          ) : (
            <div className="crm-panel reveal revealed">
              <div className="crm-toolbar">
                <p>
                  Logged in as <strong>{adminName}</strong> ({adminRole})
                </p>
                <div className="crm-actions">
                  <button onClick={downloadBackup}>Download Backup ZIP</button>
                  <button className="btn-secondary" onClick={logout}>
                    Logout
                  </button>
                </div>
              </div>

              <div className="crm-filters">
                <input
                  type="text"
                  placeholder="Search lead, email, location"
                  value={search}
                  onChange={(e) => setSearch(e.target.value)}
                />
                <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value)}>
                  <option value="">All Lead Status</option>
                  {statusOptions.map((s) => (
                    <option key={s} value={s}>
                      {s}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => {
                    setPage(0);
                    loadLeads();
                  }}
                >
                  Apply Filters
                </button>
              </div>

              {loadingContacts ? (
                <p>Loading leads...</p>
              ) : (
                <div className="crm-list">
                  {leads.map((lead) => (
                    <article
                      key={lead.id}
                      className="crm-card"
                      onMouseEnter={() => {
                        if (!timelineByLead[lead.id]) loadTimeline(lead.id);
                      }}
                    >
                      <div className="crm-card-head">
                        <h3>{lead.name}</h3>
                        <span>{lead.lead_number}</span>
                      </div>
                      <p>
                        <strong>Email:</strong> {lead.email || '-'}
                      </p>
                      <p>
                        <strong>Source:</strong> {lead.source}
                      </p>
                      <p>
                        <strong>Location:</strong> {lead.preferred_location || '-'}
                      </p>
                      <p>
                        <strong>Budget:</strong> {lead.budget || '-'}
                      </p>
                      <p>
                        <strong>Property Type:</strong> {lead.property_type || '-'}
                      </p>
                      <p>
                        <strong>Message:</strong> {lead.message}
                      </p>

                      <div className="crm-update-grid">
                        <select
                          value={lead.lead_status}
                          onChange={(e) => updateLead(lead.id, { lead_status: e.target.value })}
                        >
                          {statusOptions.map((s) => (
                            <option key={s} value={s}>
                              {s}
                            </option>
                          ))}
                        </select>
                        <select
                          value={lead.lead_temperature}
                          onChange={(e) => updateLead(lead.id, { lead_temperature: e.target.value })}
                        >
                          <option value="cold">cold</option>
                          <option value="warm">warm</option>
                          <option value="hot">hot</option>
                        </select>
                        <select
                          value={lead.assigned_to_user_id || ''}
                          onChange={(e) =>
                            updateLead(lead.id, {
                              assigned_to_user_id: e.target.value ? Number(e.target.value) : null
                            })
                          }
                        >
                          <option value="">Unassigned</option>
                          {users.map((crmUser) => (
                            <option key={crmUser.id} value={crmUser.id}>
                              {crmUser.full_name}
                            </option>
                          ))}
                        </select>
                      </div>

                      <div className="crm-update-grid">
                        <input
                          type="datetime-local"
                          value={lead.next_follow_up_at ? lead.next_follow_up_at.slice(0, 16) : ''}
                          onChange={(e) =>
                            updateLead(lead.id, {
                              next_follow_up_at: e.target.value || null
                            })
                          }
                        />
                        <input
                          type="text"
                          value={lead.buying_purpose || ''}
                          placeholder="Buying purpose"
                          onChange={(e) =>
                            setLeads((prev) =>
                              prev.map((item) =>
                                item.id === lead.id ? { ...item, buying_purpose: e.target.value } : item
                              )
                            )
                          }
                          onBlur={(e) => updateLead(lead.id, { buying_purpose: e.target.value })}
                        />
                      </div>

                      <div className="crm-activity-form">
                        <select
                          value={activityDrafts[lead.id]?.activity_type || 'note'}
                          onChange={(e) =>
                            setActivityDrafts((prev) => ({
                              ...prev,
                              [lead.id]: {
                                ...(prev[lead.id] || {}),
                                activity_type: e.target.value
                              }
                            }))
                          }
                        >
                          <option value="note">note</option>
                          <option value="call">call</option>
                          <option value="task">task</option>
                          <option value="meeting">meeting</option>
                          <option value="whatsapp">whatsapp</option>
                          <option value="email">email</option>
                        </select>
                        <input
                          type="text"
                          placeholder="Activity subject"
                          value={activityDrafts[lead.id]?.subject || ''}
                          onChange={(e) =>
                            setActivityDrafts((prev) => ({
                              ...prev,
                              [lead.id]: {
                                ...(prev[lead.id] || {}),
                                subject: e.target.value
                              }
                            }))
                          }
                        />
                        <textarea
                          placeholder="Add note, call summary, or next step"
                          value={activityDrafts[lead.id]?.details || ''}
                          onChange={(e) =>
                            setActivityDrafts((prev) => ({
                              ...prev,
                              [lead.id]: {
                                ...(prev[lead.id] || {}),
                                details: e.target.value
                              }
                            }))
                          }
                        />
                        <button onClick={() => addActivity(lead.id)}>Add Activity</button>
                      </div>

                      <div className="crm-timeline">
                        <p className="customer-role">
                          Assigned to: {lead.assigned_to_name || 'Unassigned'}
                        </p>
                        <p className="customer-role">
                          Updated: {lead.updated_at ? new Date(lead.updated_at).toLocaleString() : '-'}
                        </p>
                        {(timelineByLead[lead.id] || []).slice(0, 4).map((entry) => (
                          <div key={entry.id} className="crm-timeline-item">
                            <strong>{entry.activity_type}</strong>: {entry.subject}
                            <p>{entry.details}</p>
                          </div>
                        ))}
                      </div>
                    </article>
                  ))}
                </div>
              )}

              <div className="crm-pagination">
                <button disabled={page <= 0} onClick={() => setPage((p) => p - 1)}>
                  Previous
                </button>
                <span>
                  Page {page + 1} of {totalPages}
                </span>
                <button disabled={page + 1 >= totalPages} onClick={() => setPage((p) => p + 1)}>
                  Next
                </button>
              </div>
            </div>
          )}
        </section>
      </main>
    </div>
  );
}

function App() {
  const isAdminRoute = window.location.pathname.startsWith('/admin');
  return isAdminRoute ? <AdminPage /> : <HomePage />;
}

export default App;
