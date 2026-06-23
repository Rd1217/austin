# Real Estate CRM Blueprint

## A. Product Requirements Document

### Product Name
Four Square CRM

### Problem Statement
The business operates as a real-estate channel partner in Pune and PCMC, connecting buyers, brokers, and channel partners with verified developer projects. The current `/admin` CRM is only a lightweight contact tracker. The target system must behave like a Zoho-style operational CRM with real-estate-specific workflow enforcement, inventory awareness, partner management, booking progression, and reporting discipline.

### Business Objectives
- Capture leads from all digital and offline sources into a single system.
- Improve response SLA and conversion from lead to site visit to booking.
- Control sales execution through mandatory stage validations.
- Track builder inventory, pricing, bookings, payout, and developer reporting.
- Manage external brokers/channel partners with controlled portal access.
- Provide role-specific operational visibility for presales, sales, closing, finance, and management.

### Product Principles
- API-first and mobile-responsive.
- Strong workflow enforcement over free-form record movement.
- Multi-role, multi-team, tenancy-ready architecture.
- Auditability on pricing, reassignment, approvals, and booking-critical steps.
- Configurable automation comparable to Zoho workflow rules, cadence rules, and blueprint controls.

### In-Scope
- Leads, contacts, accounts, developers, projects, inventory, opportunities, site visits, bookings, payments, channel partners, activities, documents, approvals, reports, automations, portals, audit logs.
- Web lead capture, dedupe, assignment, cadence automation, SLA, reporting, backup/export.

### Out of Scope for Initial Release
- Full accounting ERP.
- Native telephony provider implementation for every vendor.
- AI lead scoring beyond a rules-based scoring engine.
- Marketplace syndication to every property portal on day one.

### Non-Functional Requirements
- PostgreSQL as system of record.
- JWT + refresh token auth with RBAC and field-level controls.
- Redis-backed async jobs for cadence, reminders, notifications, and syncs.
- S3-compatible document storage.
- Audit logging on all sensitive changes.
- OpenAPI-documented backend.
- Background workers, migrations, seed data, and test coverage for critical workflows.

## B. Module Breakdown

### Core Sales Modules
- Leads: entry point for every enquiry.
- Contacts: person records after qualification or conversion.
- Accounts: companies, investors, corporate buyers, institutions.
- Opportunities/Deals: project-linked revenue pipeline.
- Tasks/Calls/Meetings/Notes: activity management.
- Cadences: automated follow-up sequences.

### Real-Estate Domain Modules
- Developers/Builders: developer master and agreement data.
- Projects: launch and project metadata.
- Project Units/Inventory: sellable units and availability.
- Site Visits: visit scheduling and outcomes.
- Bookings: booking lifecycle control.
- Payments: token, installment, payout, commission collection.
- Channel Partners/Brokers: onboarding, lead source, payout, performance.

### Platform Modules
- Approvals: discount, pricing, reassignment, payout approvals.
- Documents: brochure, price sheet, KYC, booking forms, agreement docs.
- Campaigns/Sources: marketing attribution.
- Reports/Dashboards: operational and management visibility.
- User/Role/Permissions: RBAC and field/module access.
- Portal Access: external access for brokers and developers.
- Notifications: email, SMS, WhatsApp events.
- API/Integrations: webhooks, imports, exports, lead intake.
- Settings/Custom Fields/Layout Rules: admin configuration layer.
- Audit Logs/Event Log: critical activity trace.

### Recommended Build Order
1. Leads, users, roles, activities, contact capture.
2. Opportunities, projects, developers, stage controls.
3. Site visits, bookings, payments, inventory hold logic.
4. Channel partner portal, developer portal, approvals, automation builder.
5. Reporting, forecasting, advanced integrations, tenant readiness.

## C. Database Schema

### Architecture Notes
- Single PostgreSQL cluster.
- Row-level `tenant_id` on every business table.
- UUID public ids plus bigint internal ids if desired.
- `created_at`, `updated_at`, `created_by`, `updated_by` on all mutable tables.
- `deleted_at` soft-delete only where recovery matters.

### Core Identity and Security

#### `tenants`
- id
- name
- slug
- status
- created_at

#### `users`
- id
- tenant_id
- role_id
- full_name
- email
- phone
- password_hash
- is_active
- last_login_at
- created_at
- updated_at

#### `roles`
- id
- tenant_id
- name
- system_role_key
- description

#### `permissions`
- id
- module_key
- action_key
- field_key nullable

#### `role_permissions`
- id
- role_id
- permission_id

#### `refresh_tokens`
- id
- user_id
- token_hash
- expires_at
- revoked_at
- created_at

### CRM Master Data

#### `lead_sources`
- id
- tenant_id
- name
- category
- is_active

#### `campaigns`
- id
- tenant_id
- source_id
- name
- utm_source
- utm_campaign
- start_date
- end_date
- budget
- status

#### `custom_fields`
- id
- tenant_id
- module_name
- field_key
- field_label
- data_type
- is_required
- layout_name
- validation_json

### Leads and Contact Graph

#### `leads`
- id
- tenant_id
- source_id
- campaign_id
- lead_number
- name
- phone
- whatsapp_number
- email
- city
- preferred_location
- budget
- property_type
- bhk_type
- commercial_type
- buying_purpose
- lead_status
- lead_score
- lead_temperature
- assigned_user_id
- assigned_team_id
- channel_partner_id nullable
- last_follow_up_at
- next_follow_up_at
- lost_reason_id nullable
- duplicate_of_lead_id nullable
- dedupe_key_phone nullable
- dedupe_key_email nullable
- first_response_due_at
- first_response_at nullable
- converted_contact_id nullable
- converted_account_id nullable
- created_at
- updated_at

Indexes:
- `(tenant_id, phone)`
- `(tenant_id, email)`
- `(tenant_id, assigned_user_id, lead_status)`
- `(tenant_id, next_follow_up_at)`
- `(tenant_id, created_at desc)`

#### `lead_project_interests`
- id
- lead_id
- project_id
- priority

#### `contacts`
- id
- tenant_id
- lead_id nullable
- account_id nullable
- full_name
- phone
- whatsapp_number
- email
- city
- designation
- contact_type
- created_at
- updated_at

#### `accounts`
- id
- tenant_id
- account_name
- account_type
- industry
- city
- address
- owner_user_id
- created_at
- updated_at

### Developers and Projects

#### `developers`
- id
- tenant_id
- company_name
- spoc_name
- spoc_phone
- spoc_email
- rera_details
- office_address
- agreement_status
- inventory_sharing_mode
- commission_structure_json
- payment_terms_json
- is_active
- created_at
- updated_at

#### `projects`
- id
- tenant_id
- developer_id
- project_code
- project_name
- location
- micro_market
- project_type
- rera_number
- possession_date
- project_status
- amenities_json
- brochure_file_id nullable
- price_sheet_file_id nullable
- inventory_sync_method
- commission_plan_json
- project_approval_status
- created_at
- updated_at

#### `project_units`
- id
- tenant_id
- project_id
- tower_name
- unit_number
- floor
- configuration
- carpet_area
- built_up_area
- facing
- base_price
- all_in_price
- availability_status
- booking_status
- hold_expiry_at nullable
- held_by_user_id nullable
- last_synced_at
- updated_at

Indexes:
- `(tenant_id, project_id, availability_status)`
- `(tenant_id, project_id, unit_number)`
- `(tenant_id, hold_expiry_at)`

### Pipeline, Visits, and Bookings

#### `opportunities`
- id
- tenant_id
- opportunity_number
- lead_id nullable
- contact_id nullable
- account_id nullable
- project_id nullable
- unit_id nullable
- stage
- expected_revenue
- probability
- booking_amount
- assigned_manager_id
- expected_closure_date
- competitor
- lost_reason_id nullable
- source_attribution
- created_at
- updated_at

#### `site_visits`
- id
- tenant_id
- lead_id
- opportunity_id nullable
- project_id
- visit_date
- visit_type
- pickup_required
- cab_status
- sales_person_id
- visit_outcome
- customer_feedback
- created_at
- updated_at

#### `bookings`
- id
- tenant_id
- booking_number
- opportunity_id
- project_id
- unit_id
- booking_date
- booking_form_file_id nullable
- kyc_status
- token_received
- token_received_at nullable
- agreement_stage
- loan_stage
- booking_status
- developer_confirmation_status
- developer_confirmation_at nullable
- commission_expected
- commission_received
- created_at
- updated_at

#### `payments`
- id
- tenant_id
- booking_id
- payment_type
- amount
- payment_date
- reference_number
- received_by
- status
- notes

### Partner and External Ecosystem

#### `channel_partners`
- id
- tenant_id
- broker_company_name
- registration_status
- primary_contact_name
- primary_contact_phone
- primary_contact_email
- territory
- payout_status
- lead_contribution
- performance_score
- created_at
- updated_at

#### `channel_partner_project_access`
- id
- channel_partner_id
- project_id
- access_status

#### `developer_portal_shares`
- id
- tenant_id
- developer_id
- project_id
- report_type
- visibility_rules_json
- last_shared_at

### Activities and Collaboration

#### `tasks`
- id
- tenant_id
- module_name
- record_id
- owner_user_id
- task_type
- subject
- due_at
- priority
- status
- created_via_workflow_rule_id nullable
- created_at
- updated_at

#### `calls`
- id
- tenant_id
- module_name
- record_id
- owner_user_id
- direction
- started_at
- ended_at
- outcome
- notes
- telephony_provider
- external_call_id

#### `meetings`
- id
- tenant_id
- module_name
- record_id
- owner_user_id
- subject
- meeting_at
- duration_minutes
- location
- outcome
- notes

#### `notes`
- id
- tenant_id
- module_name
- record_id
- author_user_id
- content
- is_system_generated
- created_at

#### `documents`
- id
- tenant_id
- module_name
- record_id
- file_name
- mime_type
- storage_key
- uploaded_by
- created_at

### Automation and Governance

#### `workflow_rules`
- id
- tenant_id
- module_name
- rule_name
- description
- trigger_type
- trigger_event
- criteria_json
- is_active
- execution_order

#### `workflow_actions`
- id
- workflow_rule_id
- action_type
- delay_minutes nullable
- config_json

#### `blueprints`
- id
- tenant_id
- module_name
- name
- is_active

#### `blueprint_states`
- id
- blueprint_id
- state_key
- state_label
- sequence_no

#### `blueprint_transitions`
- id
- blueprint_id
- from_state
- to_state
- validation_rules_json
- required_fields_json
- approval_required

#### `cadences`
- id
- tenant_id
- name
- module_name
- stop_conditions_json
- is_active

#### `cadence_steps`
- id
- cadence_id
- step_no
- delay_days
- action_type
- action_config_json

#### `approvals`
- id
- tenant_id
- module_name
- record_id
- approval_type
- requested_by
- approver_id
- status
- reason
- created_at
- acted_at nullable

### Reporting and Traceability

#### `audit_logs`
- id
- tenant_id
- user_id nullable
- module_name
- record_id
- action
- before_json
- after_json
- ip_address
- user_agent
- created_at

#### `integration_events`
- id
- tenant_id
- event_type
- module_name
- record_id
- destination
- status
- payload_json
- response_json
- created_at

#### Materialized Views
- `mv_lead_source_performance`
- `mv_salesperson_productivity`
- `mv_project_funnel`
- `mv_channel_partner_summary`
- `mv_booking_forecast`

## D. Workflow Rules

### Zoho-Style Workflow Model
Per Zoho’s workflow model, the CRM should support:
- Trigger on create, edit, specific field change, delete, date-based event, or note action.
- Rule criteria evaluation.
- Instant actions: task, notification, field update, webhook, create record.
- Scheduled actions: delayed task, reminder, cadence step, escalation.

### Lead Capture Workflow
- Trigger: lead created from website, ads, portal, WhatsApp, API, manual, broker.
- Conditions: always.
- Actions:
- Deduplicate on phone, WhatsApp, email.
- If exact duplicate found: create lead interaction row, increment lead touch count, do not block create.
- Auto-assign based on geography, budget, source, or round robin.
- Send acknowledgement via WhatsApp/SMS/email.
- Create first-call task due in 2 hours.
- Set `first_response_due_at`.

### First-Call SLA Workflow
- Trigger: lead created.
- Scheduled action: if `first_response_at` is null after 2 hours, notify presales manager and sales head.
- Escalation: reassign if no action within SLA threshold.

### Qualification Blueprint
- Stages:
- `new_lead`
- `attempted`
- `contacted`
- `qualified`
- `visit_planned`
- `visit_done`
- `negotiation`
- `booking_in_progress`
- `booked`
- `lost`
- `nurture`

Mandatory controls:
- Cannot move to `visit_planned` without `project_id` and `visit_date`.
- Cannot move to `visit_done` without `visit_outcome` and `customer_feedback`.
- Cannot move to `booking_in_progress` without `unit_id` and `token_received`.
- Cannot move to `booked` without booking form document and developer confirmation.
- Cannot move to `lost` without lost reason and competitor capture.

### Lead Nurture Cadence
- Day 0: acknowledgement.
- Day 1: call task.
- Day 2: WhatsApp message.
- Day 4: brochure email.
- Day 7: revisit intent task.
- Stop if: booked, lost, DND, invalid contact, manually exited.

### Site Visit Workflow
- Schedule visit.
- Send confirmation.
- Reminder at T-24h and T-2h.
- Mark completed with feedback.
- Auto-create next action task after visit completion.

### Booking Workflow
- Selected unit.
- Unit hold created with expiry.
- Token payment recorded.
- KYC/documents collected.
- Loan stage tracking.
- Agreement stage tracking.
- Developer confirmation.
- Commission expectation and payout follow-up.

### Approval Workflows
- Discount approval.
- Special pricing approval.
- Lead reassignment approval above configured threshold.
- Channel partner payout approval.

### Developer Reporting Workflow
- Scheduled project-wise lead report.
- Scheduled site visit report.
- Scheduled booking report.
- Source-wise conversion report.

### Inventory Workflow
- Unit sync or manual update.
- Lock unit on hold.
- Release hold on expiry or rejection.
- Mark sold on developer confirmation.

## E. Permission Matrix

### Super Admin
- Full platform control, settings, roles, workflows, reports, exports, approvals.

### Sales Head
- Team-wide lead/deal access, reassignment, reports, forecast, approvals except infra settings.

### Presales Executive
- Create/edit leads, tasks, calls, meetings, notes.
- Can qualify leads and plan visits.
- Cannot approve pricing or manage payouts.

### Closing Manager
- Manage booking pipeline, token, KYC, agreement stages, developer confirmation tracking.

### Channel Partner Manager
- Manage brokers, project access, broker lead mapping, partner performance, payout recommendations.

### Developer/Builder Support Team
- Manage developer records, project metadata, inventory updates, report sharing.

### Telecaller
- Create/edit assigned leads, tasks, call outcomes, next follow-up.
- No pricing approval, booking approval, or payout access.

### Relationship Manager
- Own post-visit to booking conversion, customer communication, site visit and negotiation updates.

### Accounts/Finance
- Payment records, commission, payout approvals, booking financial reports.

### External Channel Partner / Broker
- Portal-only access to own leads, assigned projects, limited inventory visibility, payout statements.

### Builder / Developer Contact
- Restricted portal access to project-wise reports and booked/visit summaries for permitted projects.

### Field-Level Controls
- Telecaller cannot edit `commission_expected`, `discount`, `special_pricing`.
- Finance can edit payout and commission fields only.
- Developer users cannot see unrelated broker commissions or internal lead notes.
- Broker users cannot see leads not generated by them.

## F. API Routes

### Auth
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/logout`
- `GET /api/v1/auth/me`

### Leads
- `GET /api/v1/leads`
- `POST /api/v1/leads`
- `GET /api/v1/leads/:id`
- `PATCH /api/v1/leads/:id`
- `POST /api/v1/leads/:id/assign`
- `POST /api/v1/leads/:id/convert`
- `POST /api/v1/leads/:id/mark-lost`
- `POST /api/v1/leads/webforms`
- `POST /api/v1/leads/import`
- `GET /api/v1/leads/export`

### Contacts and Accounts
- `GET /api/v1/contacts`
- `POST /api/v1/contacts`
- `GET /api/v1/accounts`
- `POST /api/v1/accounts`

### Developers and Projects
- `GET /api/v1/developers`
- `POST /api/v1/developers`
- `GET /api/v1/projects`
- `POST /api/v1/projects`
- `GET /api/v1/projects/:id/inventory`
- `PATCH /api/v1/projects/:id/inventory-sync`

### Opportunities
- `GET /api/v1/opportunities`
- `POST /api/v1/opportunities`
- `PATCH /api/v1/opportunities/:id/stage`
- `PATCH /api/v1/opportunities/:id`
- `GET /api/v1/opportunities/kanban`

### Site Visits
- `GET /api/v1/site-visits`
- `POST /api/v1/site-visits`
- `PATCH /api/v1/site-visits/:id`
- `POST /api/v1/site-visits/:id/complete`

### Bookings and Payments
- `GET /api/v1/bookings`
- `POST /api/v1/bookings`
- `PATCH /api/v1/bookings/:id`
- `POST /api/v1/bookings/:id/confirm`
- `GET /api/v1/payments`
- `POST /api/v1/payments`

### Channel Partners
- `GET /api/v1/channel-partners`
- `POST /api/v1/channel-partners`
- `PATCH /api/v1/channel-partners/:id`
- `GET /api/v1/channel-partners/:id/payouts`

### Activities
- `POST /api/v1/tasks`
- `POST /api/v1/calls`
- `POST /api/v1/meetings`
- `POST /api/v1/notes`
- `GET /api/v1/timeline/:module/:id`

### Documents
- `POST /api/v1/documents/presign`
- `POST /api/v1/documents`
- `GET /api/v1/documents/:id`

### Workflows and Automation
- `GET /api/v1/workflows`
- `POST /api/v1/workflows`
- `PATCH /api/v1/workflows/:id`
- `GET /api/v1/blueprints`
- `POST /api/v1/blueprints`
- `GET /api/v1/cadences`
- `POST /api/v1/cadences`

### Approvals
- `GET /api/v1/approvals`
- `POST /api/v1/approvals`
- `POST /api/v1/approvals/:id/approve`
- `POST /api/v1/approvals/:id/reject`

### Reporting
- `GET /api/v1/reports/lead-source-performance`
- `GET /api/v1/reports/lead-aging`
- `GET /api/v1/reports/response-sla`
- `GET /api/v1/reports/project-funnel`
- `GET /api/v1/reports/channel-partner-performance`
- `GET /api/v1/reports/forecast`

### Portals
- `GET /api/v1/portal/broker/leads`
- `GET /api/v1/portal/broker/projects`
- `GET /api/v1/portal/broker/payouts`
- `GET /api/v1/portal/developer/reports`

## G. UI Pages/Components

### Internal App Navigation
- Dashboard
- Leads
- Contacts
- Accounts
- Developers
- Projects
- Inventory
- Opportunities
- Site Visits
- Bookings
- Payments
- Channel Partners
- Activities
- Documents
- Reports
- Approvals
- Automations
- Settings

### Key Screens
- Lead list with saved filters and duplicate indicators.
- Lead detail page with full timeline and qualification panel.
- Opportunity kanban board.
- Site visit scheduler/calendar.
- Booking detail screen with compliance checklist.
- Inventory grid with hold and availability badges.
- Channel partner portal dashboard.
- Developer reporting dashboard.
- Workflow builder.
- Cadence builder.
- Blueprint stage designer.
- Approval inbox.
- Audit/event log viewer.

### Core Components
- Smart search bar.
- Saved filter builder.
- Timeline composer.
- Activity quick-add panel.
- Duplicate alert banner.
- SLA badge.
- Stage gate modal.
- Role-aware action bar.
- Document upload drawer.
- Approval drawer.
- Reporting widgets.

## H. Automation Engine Design

### Execution Model
- Event-driven architecture.
- Core events published on create/update/delete/stage transition/note added.
- Worker queue executes instant and scheduled actions.
- Every automation run writes to `integration_events` and audit log.

### Engine Components
- Rule evaluator.
- Trigger registry.
- Criteria parser.
- Action dispatcher.
- Scheduler for time-based and cadence actions.
- Blueprint validator for mandatory stage rules.
- Approval gateway for approval-required transitions.

### Supported Actions
- Field update.
- Create task.
- Create note.
- Send email.
- Send WhatsApp webhook.
- Send SMS webhook.
- Slack/Cliq webhook.
- Reassign owner.
- Create related record.
- Trigger custom function.

### Recommended Tech
- If staying Python: Django + DRF + Celery + Redis.
- If shifting Node: NestJS + BullMQ + Redis.
- Current codebase is Python/FastAPI, so the lower-risk path is: FastAPI retained for v1 APIs, then move to modular FastAPI services or Django if admin/config complexity grows.

## I. Reporting Design

### Reporting Layer
- Operational tables for live views.
- Materialized views refreshed by worker for dashboard-heavy reports.
- Snapshot tables for monthly forecast and stage aging.

### Core Reports
- Lead source performance.
- Lead aging.
- First response SLA compliance.
- Presales and salesperson productivity.
- Project-wise funnel.
- Visit-to-booking conversion.
- Booking value by month.
- Channel partner performance.
- Developer-wise business summary.
- Commission and payout summary.
- Stage-wise forecast by month.

### Dashboard Views
- Super Admin dashboard.
- Sales Head dashboard.
- Presales dashboard.
- Finance payout dashboard.
- Channel partner manager dashboard.
- Developer-facing report share dashboard.

## J. Sprint Plan

### Sprint 1
- Auth, users, roles, permissions.
- Lead capture APIs.
- Lead list/detail.
- Activities.
- Duplicate detection.
- Audit log baseline.

### Sprint 2
- Lead assignment engine.
- SLA tracking.
- Opportunity pipeline.
- Projects and developers master.
- Initial dashboards.

### Sprint 3
- Site visits.
- Inventory and unit hold logic.
- Stage validations.
- Booking module.
- Document storage.

### Sprint 4
- Payments, commission, payout tracking.
- Channel partner module and restricted portal.
- Approval engine.
- Builder reporting.

### Sprint 5
- Workflow builder.
- Cadence builder.
- Blueprint builder.
- Notifications/webhooks.
- CSV import/export.

### Sprint 6
- Forecasting.
- Advanced reports.
- Mobile polish.
- Test automation.
- Tenant-readiness and deployment hardening.

## K. Risks and Scope Exclusions

### Risks
- Inventory accuracy depends on disciplined builder sync or integration contracts.
- Telephony/WhatsApp providers vary widely; integration abstraction is required.
- Approval logic can become brittle without a configurable policy engine.
- External portal access raises data-isolation and permission complexity.
- Large report workloads require disciplined analytics design, not ad hoc queries.

### Scope Exclusions for v1
- Full marketing automation suite.
- Deep AI recommendations.
- Native ERP-grade accounting.
- Full omnichannel contact-center stack.

### Mapping to Current `/admin`
- Current `/admin` already provides login, contact listing, contact updates, and backup export.
- That existing admin should be treated as the seed for:
- `Leads` list/detail.
- activity timeline.
- role-aware access shell.
- CRM dashboard shell.
- The next implementation step is not cosmetic; it is schema expansion plus module decomposition around `leads`, `projects`, `opportunities`, `site_visits`, `bookings`, `payments`, and `channel_partners`.
