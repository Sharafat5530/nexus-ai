import React from 'react';
import { motion } from 'framer-motion';
import { Layers, ArrowRight } from 'lucide-react';
import { NavLink } from 'react-router-dom';

interface PlaceholderPageProps {
  title: string;
  description: string;
  phase: string;
  badge: string;
}

export const PlaceholderPage: React.FC<PlaceholderPageProps> = ({
  title,
  description,
  phase,
  badge
}) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2 }}
      className="p-8 bg-surface border border-border rounded-xl shadow-subtle max-w-3xl"
    >
      <div className="flex items-center space-x-2 mb-3">
        <span className="px-2.5 py-0.5 text-xs font-semibold rounded-full bg-teal-50 text-teal-700 border border-teal-200">
          {badge}
        </span>
        <span className="text-xs text-navy-400 font-medium">{phase}</span>
      </div>

      <h1 className="text-xl font-bold tracking-tight text-navy-900">{title}</h1>
      <p className="text-sm text-navy-500 mt-1 max-w-xl">{description}</p>

      <div className="mt-8 p-4 bg-canvas border border-border rounded-lg flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <Layers className="w-5 h-5 text-teal-600" />
          <div className="text-xs">
            <p className="font-semibold text-navy-900">Module Scaffolding Active</p>
            <p className="text-navy-500">FastAPI backend models and endpoints will connect in the subsequent phases.</p>
          </div>
        </div>

        <NavLink
          to="/"
          className="inline-flex items-center space-x-1 text-xs font-semibold text-teal-600 hover:text-teal-700"
        >
          <span>Return to Overview</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </NavLink>
      </div>
    </motion.div>
  );
};
