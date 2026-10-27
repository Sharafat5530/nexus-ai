import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppShell } from '@/components/layout/AppShell';
import { OverviewPage } from '@/pages/OverviewPage';
import { PlaceholderPage } from '@/pages/PlaceholderPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<AppShell />}>
          <Route index element={<OverviewPage />} />
          
          <Route
            path="conversations"
            element={
              <PlaceholderPage
                title="Customer Conversations & Investigation"
                description="Live customer dialogue interface with real-time agent intent classification and multi-turn context extraction."
                phase="Phase 3 Integration"
                badge="Customer Ingestion"
              />
            }
          />

          <Route
            path="tasks"
            element={
              <PlaceholderPage
                title="Live Agent Tasks & Workflow Traces"
                description="LangGraph execution visualizer showing checkpoints, agent steps, and state transitions across specialized agents."
                phase="Phase 4 Integration"
                badge="LangGraph Runtime"
              />
            }
          />

          <Route
            path="sales"
            element={
              <PlaceholderPage
                title="Autonomous Sales Pipeline & Qualification"
                description="Lead qualification, meeting calendar availability validation, and CRM integration workflows."
                phase="Phase 7 Integration"
                badge="Sales AI"
              />
            }
          />

          <Route
            path="approvals"
            element={
              <PlaceholderPage
                title="Human Approval Queue"
                description="High-friction action gateway: view proposed mutations, evidence, policy rules, and grant cryptographically signed approvals."
                phase="Phase 5 Integration"
                badge="Zero-Trust Gate"
              />
            }
          />

          <Route
            path="verification"
            element={
              <PlaceholderPage
                title="Proof-of-Outcome Verification Engine"
                description="Authoritative read-back validator: compares expected outcomes with post-mutation system state to verify genuine completion."
                phase="Phase 6 Integration"
                badge="Proof Engine"
              />
            }
          />

          <Route
            path="knowledge"
            element={
              <PlaceholderPage
                title="Tenant Knowledge Base & Policy Repository"
                description="Vector-indexed support policies with pgvector semantic retrieval. Content is treated strictly as untrusted data."
                phase="Phase 4 Integration"
                badge="pgvector RAG"
              />
            }
          />

          <Route
            path="security"
            element={
              <PlaceholderPage
                title="Zero-Trust Security Center"
                description="Real-time audit log of prevented actions, prompt injection defenses, tenant boundary enforcement, and kill-switch controls."
                phase="Phase 5 Integration"
                badge="Policy Gateway"
              />
            }
          />

          <Route
            path="audit"
            element={
              <PlaceholderPage
                title="Tamper-Resistant Audit Trail"
                description="Comprehensive event stream detailing every agent decision, tool execution, idempotency key, and human sign-off."
                phase="Phase 2 Integration"
                badge="Compliance"
              />
            }
          />

          <Route
            path="settings"
            element={
              <PlaceholderPage
                title="Platform Settings & Integration Adapters"
                description="Configure CRM, Stripe, Shipping Carrier, and Calendar credentials alongside tenant policy definitions."
                phase="Phase 3 Integration"
                badge="System Config"
              />
            }
          />
        </Route>

        <Route
          path="/portal"
          element={
            <div className="min-h-screen bg-canvas p-8 flex flex-col items-center justify-center">
              <div className="max-w-md w-full bg-surface border border-border rounded-xl p-6 shadow-subtle text-center space-y-4">
                <div className="w-10 h-10 rounded-full bg-teal-50 text-teal-600 flex items-center justify-center mx-auto font-bold text-sm">
                  CP
                </div>
                <h2 className="text-lg font-bold text-navy-900">Customer Support Portal</h2>
                <p className="text-xs text-navy-500">
                  This standalone customer portal simulates incoming customer issues (e.g. "My order is delayed"). Built in Phase 3.
                </p>
                <NavLink
                  to="/"
                  className="inline-block text-xs font-semibold text-teal-600 hover:text-teal-700 pt-2"
                >
                  ← Return to Teammate Platform
                </NavLink>
              </div>
            </div>
          }
        />

        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </BrowserRouter>
  );
};

export default App;
