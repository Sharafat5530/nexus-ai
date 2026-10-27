import { LucideIcon } from 'lucide-react';

export interface NavItem {
  title: string;
  href: string;
  icon: LucideIcon;
  badge?: number | string;
  badgeVariant?: 'default' | 'teal' | 'amber' | 'blue';
  section?: 'operations' | 'governance' | 'configuration';
}

export interface BreadcrumbItem {
  label: string;
  href?: string;
}
