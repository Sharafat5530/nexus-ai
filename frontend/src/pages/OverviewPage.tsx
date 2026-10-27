import { ChevronRight } from "lucide-react";
import React from 'react';
import { motion } from 'framer-motion';
import {
  CheckCircle2,
  Clock,
  ShieldCheck,
  AlertTriangle,
  ArrowUpRight,
  Cpu,
  Layers,
  ArrowRight
} from 'lucide-react';
import { NavLink } from 'react-router-dom';

export const OverviewPage: React.FC = () => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25 }}
      className="space-y-8"
    >
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-navy-900">Teammate Operations Overview</h1>
          <p className="text-sm text-navy-500 mt-1">
            Real-time execution telemetry, autonomous completion rates, and active human approval gates.
          </p>
        </div>

        <div className="flex items-center space-x-3">
          <NavLink
            to="/tasks"
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-medium text-navy-700 bg-surface border border-border rounded-lg hover:bg-canvas transition-colors shadow-subtle"
          >
            <Layers className="w-3.5 h-3.5 text-navy-500" />
            <span>Task Stream</span>
          </NavLink>
          <NavLink
            to="/approvals"
            className="inline-flex items-center space-x-1.5 px-3.5 py-2 text-xs font-semibold text-white bg-teal-600 rounded-lg hover:bg-teal-700 transition-colors shadow-subtle"
          >
            <span>Review Approvals (2)</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </NavLink>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 bg-surface border border-border rounded-xl shadow-subtle">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-navy-500">Verified Completion Rate</span>
            <span className="p-1.5 rounded-md bg-teal-50 text-teal-600">
              <CheckCircle2 className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold tracking-tight text-navy-900">94.8%</span>
            <span className="text-xs font-semibold text-teal-700 flex items-center">
              <ArrowUpRight className="w-3 h-3" /> +2.3%
            </span>
          </div>
          <p className="text-[11px] text-navy-400 mt-1">Confirmed by authoritative system read-back</p>
        </div>

        <div className="p-5 bg-surface border border-border rounded-xl shadow-subtle">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-navy-500">Autonomous vs Human Ratio</span>
            <span className="p-1.5 rounded-md bg-blue-50 text-blue-600">
              <Cpu className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold tracking-tight text-navy-900">81 / 19</span>
            <span className="text-xs font-semibold text-blue-600">Automated</span>
          </div>
          <p className="text-[11px] text-navy-400 mt-1">19% escalated for business policy review</p>
        </div>

        <div className="p-5 bg-surface border border-border rounded-xl shadow-subtle">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-navy-500">Avg Resolution Time</span>
            <span className="p-1.5 rounded-md bg-navy-100 text-navy-700">
              <Clock className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold tracking-tight text-navy-900">42s</span>
            <span className="text-xs text-navy-500 font-medium">end-to-end</span>
          </div>
          <p className="text-[11px] text-navy-400 mt-1">Investigation, gate, mutation & proof</p>
        </div>

        <div className="p-5 bg-surface border border-border rounded-xl shadow-subtle">
          <div className="flex items-center justify-between">
            <span className="text-xs font-medium text-navy-500">Zero-Trust Interventions</span>
            <span className="p-1.5 rounded-md bg-amber-50 text-amber-700">
              <ShieldCheck className="w-4 h-4" />
            </span>
          </div>
          <div className="mt-3 flex items-baseline space-x-2">
            <span className="text-2xl font-bold tracking-tight text-navy-900">14</span>
            <span className="text-xs font-semibold text-amber-700">Blocked Safely</span>
          </div>
          <p className="text-[11px] text-navy-400 mt-1">Policy violations & prompt injections prevented</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="bg-surface border border-border rounded-xl p-6 shadow-subtle">
            <div className="flex items-center justify-between pb-4 border-b border-border">
              <div className="flex items-center space-x-3">
                <span className="w-3 h-3 rounded-full bg-teal-500 animate-pulse" />
                <div>
                  <h3 className="text-sm font-bold text-navy-900">Active Workflow: Delayed Order Resolution</h3>
                  <p className="text-xs text-navy-500">Task ID: <code className="text-navy-700">tsk_982e01df</code> • Customer: Marcus Vance</p>
                </div>
              </div>
              <span className="px-2.5 py-1 text-xs font-semibold rounded-full bg-amber-50 text-amber-800 border border-amber-200">
                Awaiting Human Approval
              </span>
            </div>

            <div className="py-6">
              <div className="text-xs font-medium text-navy-500 mb-4">Multi-Agent Orchestration Sequence:</div>
              <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
                <div className="p-3 rounded-lg bg-teal-50/50 border border-teal-200">
                  <div className="flex items-center space-x-2 text-teal-700 text-xs font-semibold mb-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>1. Support Agent</span>
                  </div>
                  <p className="text-[11px] text-navy-600">Investigated customer ticket & verified order #ORD-4491.</p>
                </div>

                <div className="p-3 rounded-lg bg-teal-50/50 border border-teal-200">
                  <div className="flex items-center space-x-2 text-teal-700 text-xs font-semibold mb-1">
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    <span>2. Ops & Policy</span>
                  </div>
                  <p className="text-[11px] text-navy-600">Carrier delay confirmed. Policy allows up to $50 goodwill credit.</p>
                </div>

                <div className="p-3 rounded-lg bg-amber-50 border border-amber-200 ring-2 ring-amber-400/20">
                  <div className="flex items-center space-x-2 text-amber-800 text-xs font-bold mb-1">
                    <AlertTriangle className="w-3.5 h-3.5" />
                    <span>3. Policy Gateway</span>
                  </div>
                  <p className="text-[11px] text-amber-900">Proposed action ($35 refund) flagged for employee review.</p>
                </div>

                <div className="p-3 rounded-lg bg-canvas border border-dashed border-border opacity-70">
                  <div className="flex items-center space-x-2 text-navy-500 text-xs font-semibold mb-1">
                    <Clock className="w-3.5 h-3.5" />
                    <span>4. Verification</span>
                  </div>
                  <p className="text-[11px] text-navy-400">Post-execution ledger check & customer notification.</p>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-border flex items-center justify-between">
              <span className="text-xs text-navy-500">Proposed Action: <strong className="text-navy-900 font-semibold">Stripe Partial Refund ($35.00)</strong></span>
              <NavLink
                to="/approvals"
                className="text-xs font-semibold text-teal-600 hover:text-teal-700 flex items-center space-x-1"
              >
                <span>Open Approval Gate</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </NavLink>
            </div>
          </div>

          <div className="bg-surface border border-border rounded-xl shadow-subtle overflow-hidden">
            <div className="px-6 py-4 border-b border-border flex items-center justify-between">
              <h3 className="text-sm font-bold text-navy-900">Recent Task Stream</h3>
              <NavLink to="/tasks" className="text-xs font-medium text-navy-500 hover:text-navy-900">View all</NavLink>
            </div>

            <div className="divide-y divide-border">
              <div className="px-6 py-3.5 flex items-center justify-between hover:bg-canvas/50 transition-colors text-xs">
                <div className="flex items-center space-x-3">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <div>
                    <span className="font-semibold text-navy-900">Shipment Priority Upgrade</span>
                    <span className="text-navy-400 ml-2">#ORD-8812</span>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-emerald-50 text-emerald-700 border border-emerald-200">
                    Verified Complete
                  </span>
                  <span className="text-navy-400">2m ago</span>
                </div>
              </div>

              <div className="px-6 py-3.5 flex items-center justify-between hover:bg-canvas/50 transition-colors text-xs">
                <div className="flex items-center space-x-3">
                  <span className="w-2 h-2 rounded-full bg-blue-500" />
                  <div>
                    <span className="font-semibold text-navy-900">Inbound Sales Lead Qualified</span>
                    <span className="text-navy-400 ml-2">CloudTech Inc ($48k ARR)</span>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-blue-50 text-blue-700 border border-blue-200">
                    Meeting Booked
                  </span>
                  <span className="text-navy-400">14m ago</span>
                </div>
              </div>

              <div className="px-6 py-3.5 flex items-center justify-between hover:bg-canvas/50 transition-colors text-xs">
                <div className="flex items-center space-x-3">
                  <span className="w-2 h-2 rounded-full bg-rose-500" />
                  <div>
                    <span className="font-semibold text-navy-900">Unauthorized Refund Attempt</span>
                    <span className="text-navy-400 ml-2">Prompt Injection Detected</span>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <span className="px-2 py-0.5 rounded-full text-[11px] font-medium bg-rose-50 text-rose-700 border border-rose-200">
                    Gateway Blocked
                  </span>
                  <span className="text-navy-400">1h ago</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="space-y-6">
          <div className="bg-surface border border-border rounded-xl p-6 shadow-subtle">
            <h3 className="text-sm font-bold text-navy-900 mb-1">Architecture Integrity</h3>
            <p className="text-xs text-navy-500 mb-4">Autonomous execution safety guarantees:</p>

            <div className="space-y-3">
              <div className="flex items-start space-x-2.5 text-xs">
                <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-navy-900">Zero Direct Database Writes</span>
                  <p className="text-navy-500 text-[11px]">Agents propose actions; only deterministic adapters mutate state.</p>
                </div>
              </div>

              <div className="flex items-start space-x-2.5 text-xs">
                <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-navy-900">Independent Verification</span>
                  <p className="text-navy-500 text-[11px]">Tasks are verified only after reading back the authoritative system record.</p>
                </div>
              </div>

              <div className="flex items-start space-x-2.5 text-xs">
                <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-navy-900">Tenant Scoped Isolation</span>
                  <p className="text-navy-500 text-[11px]">Every query and tool execution is scoped to the verified tenant ID.</p>
                </div>
              </div>

              <div className="flex items-start space-x-2.5 text-xs">
                <CheckCircle2 className="w-4 h-4 text-teal-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold text-navy-900">Idempotency Locks</span>
                  <p className="text-navy-500 text-[11px]">Eliminates duplicate refunds or meetings on network timeouts.</p>
                </div>
              </div>
            </div>

            <div className="mt-6 pt-4 border-t border-border">
              <NavLink
                to="/security"
                className="w-full inline-flex items-center justify-center space-x-1 text-xs font-semibold text-teal-700 bg-teal-50 hover:bg-teal-100 py-2 rounded-lg border border-teal-200 transition-colors"
              >
                <span>Inspect Security Policies</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </NavLink>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
