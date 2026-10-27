import React, { useState } from 'react';
import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import {
  LayoutDashboard,
  MessageSquare,
  GitBranch,
  ShieldAlert,
  CheckCircle2,
  TrendingUp,
  BookOpen,
  Lock,
  FileText,
  Settings,
  ExternalLink,
  ChevronRight,
  ShieldCheck,
  Bell,
  Menu,
  X,
  Sparkles
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { NavItem } from '@/types/navigation';

const navItems: NavItem[] = [
  { title: 'Overview', href: '/', icon: LayoutDashboard, section: 'operations' },
  { title: 'Customer Chats', href: '/conversations', icon: MessageSquare, badge: 3, badgeVariant: 'blue', section: 'operations' },
  { title: 'Live Agent Tasks', href: '/tasks', icon: GitBranch, badge: '5 Active', badgeVariant: 'teal', section: 'operations' },
  { title: 'Sales Pipeline', href: '/sales', icon: TrendingUp, section: 'operations' },
  { title: 'Approval Queue', href: '/approvals', icon: ShieldAlert, badge: 2, badgeVariant: 'amber', section: 'governance' },
  { title: 'Outcome Verification', href: '/verification', icon: CheckCircle2, section: 'governance' },
  { title: 'Knowledge Base', href: '/knowledge', icon: BookOpen, section: 'governance' },
  { title: 'Security Center', href: '/security', icon: Lock, section: 'configuration' },
  { title: 'Audit Trail', href: '/audit', icon: FileText, section: 'configuration' },
  { title: 'System Settings', href: '/settings', icon: Settings, section: 'configuration' },
];

export const AppShell: React.FC = () => {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const location = useLocation();
  const currentItem = navItems.find(item => item.href === location.pathname) || { title: 'Dashboard' };

  return (
    <div className="min-h-screen bg-canvas flex flex-col md:flex-row antialiased text-navy-900">
      <div className="md:hidden flex items-center justify-between px-4 py-3 bg-surface border-b border-border sticky top-0 z-40">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 rounded-lg bg-teal-600 flex items-center justify-center text-white shadow-sm">
            <Sparkles className="w-4 h-4" />
          </div>
          <span className="font-bold tracking-tight text-navy-900">NEXUS<span className="text-teal-600 font-semibold ml-0.5">AI</span></span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-md hover:bg-navy-100 text-navy-700 focus-visible:outline-none"
          aria-label="Toggle Navigation Menu"
        >
          {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      <aside
        className={cn(
          "fixed inset-y-0 left-0 z-50 w-64 bg-surface border-r border-border flex flex-col transition-transform duration-200 ease-in-out md:translate-x-0 md:static md:h-screen",
          mobileMenuOpen ? "translate-x-0 shadow-lifted" : "-translate-x-full"
        )}
      >
        <div className="h-16 flex items-center justify-between px-5 border-b border-border">
          <div className="flex items-center space-x-2.5">
            <div className="w-9 h-9 rounded-lg bg-teal-600 flex items-center justify-center text-white shadow-sm">
              <Sparkles className="w-5 h-5" />
            </div>
            <div>
              <div className="flex items-center space-x-1.5">
                <span className="font-bold tracking-tight text-navy-900 text-base">NEXUS</span>
                <span className="text-xs px-1.5 py-0.5 bg-teal-50 text-teal-700 font-semibold rounded border border-teal-200">
                  PLATFORM
                </span>
              </div>
              <p className="text-[11px] text-navy-500 font-medium leading-none mt-0.5">Verified Autonomous Teammates</p>
            </div>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto px-3 py-4 space-y-6">
          <div>
            <div className="px-3 mb-2 text-[11px] font-semibold tracking-wider text-navy-400 uppercase">
              Operations & Tasks
            </div>
            <nav className="space-y-1">
              {navItems.filter(i => i.section === 'operations').map((item) => (
                <SidebarNavLink key={item.href} item={item} onClick={() => setMobileMenuOpen(false)} />
              ))}
            </nav>
          </div>

          <div>
            <div className="px-3 mb-2 text-[11px] font-semibold tracking-wider text-navy-400 uppercase">
              Governance & Proof
            </div>
            <nav className="space-y-1">
              {navItems.filter(i => i.section === 'governance').map((item) => (
                <SidebarNavLink key={item.href} item={item} onClick={() => setMobileMenuOpen(false)} />
              ))}
            </nav>
          </div>

          <div>
            <div className="px-3 mb-2 text-[11px] font-semibold tracking-wider text-navy-400 uppercase">
              Platform & Control
            </div>
            <nav className="space-y-1">
              {navItems.filter(i => i.section === 'configuration').map((item) => (
                <SidebarNavLink key={item.href} item={item} onClick={() => setMobileMenuOpen(false)} />
              ))}
            </nav>
          </div>
        </div>

        <div className="p-3 border-t border-border bg-canvas/60">
          <NavLink
            to="/portal"
            className="flex items-center justify-between px-3 py-2 text-xs font-medium text-navy-700 rounded-lg hover:bg-surface border border-border transition-colors group"
          >
            <div className="flex items-center space-x-2">
              <span className="w-2 h-2 rounded-full bg-teal-500 animate-pulse" />
              <span>Customer Demo Portal</span>
            </div>
            <ExternalLink className="w-3.5 h-3.5 text-navy-400 group-hover:text-teal-600 transition-colors" />
          </NavLink>
        </div>

        <div className="p-3 border-t border-border flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="w-8 h-8 rounded-full bg-navy-800 text-white flex items-center justify-center font-semibold text-xs">
              AD
            </div>
            <div className="overflow-hidden">
              <p className="text-xs font-semibold text-navy-900 truncate">Alex Dunhill</p>
              <p className="text-[11px] text-navy-500 truncate">Acme Global (Admin)</p>
            </div>
          </div>
          <span className="w-2 h-2 rounded-full bg-teal-500" title="Deterministic Gateway Active" />
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0 md:h-screen md:overflow-y-auto">
        <header className="h-16 bg-surface border-b border-border px-6 flex items-center justify-between sticky top-0 z-30">
          <div className="flex items-center space-x-2 text-sm text-navy-600">
            <span className="text-navy-400">Teammate Platform</span>
            <ChevronRight className="w-4 h-4 text-navy-400" />
            <span className="font-semibold text-navy-900">{currentItem.title}</span>
          </div>

          <div className="flex items-center space-x-4">
            <div className="hidden sm:flex items-center space-x-2 px-3 py-1 rounded-full bg-teal-50 border border-teal-200 text-teal-700 text-xs font-medium">
              <ShieldCheck className="w-3.5 h-3.5 text-teal-600" />
              <span>Policy Gateway: Active & Enforced</span>
            </div>

            <button
              className="relative p-2 rounded-lg text-navy-500 hover:text-navy-900 hover:bg-canvas transition-colors"
              aria-label="View approvals and notifications"
            >
              <Bell className="w-4 h-4" />
              <span className="absolute top-1.5 right-1.5 w-2 h-2 rounded-full bg-amber-500 ring-2 ring-surface" />
            </button>
          </div>
        </header>

        <main className="flex-1 p-6 md:p-8 max-w-7xl w-full mx-auto">
          <Outlet />
        </main>
      </div>

      <AnimatePresence>
        {mobileMenuOpen && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={() => setMobileMenuOpen(false)}
            className="fixed inset-0 bg-navy-900/30 backdrop-blur-xs z-40 md:hidden"
          />
        )}
      </AnimatePresence>
    </div>
  );
};

interface SidebarNavLinkProps {
  item: NavItem;
  onClick: () => void;
}

const SidebarNavLink: React.FC<SidebarNavLinkProps> = ({ item, onClick }) => {
  return (
    <NavLink
      to={item.href}
      onClick={onClick}
      className={({ isActive }) =>
        cn(
          "relative flex items-center justify-between px-3 py-2 rounded-lg text-xs font-medium transition-colors",
          isActive
            ? "text-teal-700 font-semibold bg-teal-50/80"
            : "text-navy-600 hover:text-navy-900 hover:bg-canvas"
        )
      }
    >
      {({ isActive }) => (
        <>
          <div className="flex items-center space-x-3">
            <item.icon className={cn("w-4 h-4", isActive ? "text-teal-600" : "text-navy-500")} />
            <span>{item.title}</span>
          </div>

          {item.badge !== undefined && (
            <span
              className={cn(
                "px-2 py-0.5 text-[10px] font-semibold rounded-full border",
                item.badgeVariant === 'amber' && "bg-amber-50 text-amber-700 border-amber-200",
                item.badgeVariant === 'teal' && "bg-teal-50 text-teal-700 border-teal-200",
                item.badgeVariant === 'blue' && "bg-blue-50 text-blue-700 border-blue-200",
                !item.badgeVariant && "bg-navy-100 text-navy-700 border-border"
              )}
            >
              {item.badge}
            </span>
          )}

          {isActive && (
            <motion.div
              layoutId="sidebar-active-indicator"
              className="absolute left-0 top-1.5 bottom-1.5 w-1 bg-teal-600 rounded-r"
              transition={{ type: "spring", stiffness: 350, damping: 30 }}
            />
          )}
        </>
      )}
    </NavLink>
  );
};
