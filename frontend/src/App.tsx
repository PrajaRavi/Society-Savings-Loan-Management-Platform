import React from 'react';
import { useQuery } from '@tanstack/react-query';
import { Layout } from './components/common/Layout';
import { fetchHealthCheck } from './services/api';
import {
  Activity,
  CheckCircle2,
  AlertCircle,
  Database,
  Layers,
  ArrowRight,
  ShieldCheck,
  Coins,
  Scale,
  Users,
} from 'lucide-react';

export const App: React.FC = () => {
  const { data: health, isLoading, isError } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealthCheck,
    retry: 2,
    refetchInterval: 30000,
  });

  return (
    <Layout>
      <div className="space-y-6">
        {/* Welcome Banner */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6 sm:p-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <div className="inline-flex items-center space-x-2 text-xs font-semibold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 mb-3">
                <ShieldCheck className="w-3.5 h-3.5" />
                <span>Feature 1: Project Scaffolding & Foundation</span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">
                Society Savings & Loan Management Platform
              </h1>
              <p className="mt-2 text-sm text-gray-600 max-w-3xl">
                A multi-tenant SaaS platform engineered for mutual aid societies, chits, and savings groups.
                Featuring deterministic FIFO lending, strict double-entry ledger accounting, and asynchronous queuing.
              </p>
            </div>

            {/* Backend Health Badge */}
            <div className="bg-gray-50 border border-gray-200 rounded-lg p-4 sm:min-w-[220px]">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Backend API</span>
                <span className="relative flex h-2.5 w-2.5">
                  <span
                    className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                      isLoading ? 'bg-amber-400' : isError ? 'bg-red-400' : 'bg-emerald-400'
                    }`}
                  ></span>
                  <span
                    className={`relative inline-flex rounded-full h-2.5 w-2.5 ${
                      isLoading ? 'bg-amber-500' : isError ? 'bg-red-500' : 'bg-emerald-500'
                    }`}
                  ></span>
                </span>
              </div>

              <div className="mt-2">
                {isLoading && (
                  <div className="flex items-center text-xs text-amber-600">
                    <Activity className="w-3.5 h-3.5 animate-spin mr-1.5" />
                    <span>Connecting to API...</span>
                  </div>
                )}
                {isError && (
                  <div className="flex items-center text-xs text-red-600">
                    <AlertCircle className="w-3.5 h-3.5 mr-1.5" />
                    <span>API Offline / Unreachable</span>
                  </div>
                )}
                {health && (
                  <div>
                    <div className="flex items-center text-xs font-semibold text-emerald-700">
                      <CheckCircle2 className="w-3.5 h-3.5 mr-1.5" />
                      <span>Online ({health.status})</span>
                    </div>
                    <div className="text-[11px] text-gray-500 mt-1">
                      Env: <span className="font-mono text-gray-700">{health.environment}</span> | v{health.version}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* Core Architectural Pillars */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm hover:border-emerald-300 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center mb-4">
              <Users className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-gray-900 text-sm">Multi-Tenancy</h3>
            <p className="mt-1 text-xs text-gray-500">
              Complete tenant isolation. Membership by cryptographically signed, single-use invite tokens.
            </p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm hover:border-emerald-300 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center mb-4">
              <Scale className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-gray-900 text-sm">Double-Entry Ledger</h3>
            <p className="mt-1 text-xs text-gray-500">
              Balanced debits and credits. All monetary balances calculated dynamically in minor currency units (paise).
            </p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm hover:border-emerald-300 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-purple-50 text-purple-600 flex items-center justify-center mb-4">
              <Coins className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-gray-900 text-sm">Strict FIFO Queue</h3>
            <p className="mt-1 text-xs text-gray-500">
              Transaction-locked fair queue ordering with strict all-or-nothing allocation. No queue jumping allowed.
            </p>
          </div>

          <div className="bg-white p-5 rounded-xl border border-gray-200 shadow-sm hover:border-emerald-300 transition-colors">
            <div className="w-10 h-10 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center mb-4">
              <Database className="w-5 h-5" />
            </div>
            <h3 className="font-semibold text-gray-900 text-sm">Celery + Redis Engine</h3>
            <p className="mt-1 text-xs text-gray-500">
              Asynchronous worker fleets executing reservation sweeps, monthly obligations, and overdue notifications.
            </p>
          </div>
        </div>

        {/* Feature 1 Status Checklist */}
        <div className="bg-white rounded-xl shadow-sm border border-gray-200 p-6">
          <div className="flex items-center space-x-2 pb-4 mb-4 border-b border-gray-100">
            <Layers className="w-5 h-5 text-emerald-600" />
            <h2 className="text-base font-semibold text-gray-900">
              Foundation Deliverables & Verification
            </h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              <div className="flex items-start space-x-3 text-xs">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="font-semibold text-gray-800">Backend App Shell:</span>
                  <p className="text-gray-500">FastAPI 0.115.5 with CORS middleware, Pydantic v2 settings, and health check route.</p>
                </div>
              </div>

              <div className="flex items-start space-x-3 text-xs">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="font-semibold text-gray-800">Dependencies & Virtualenv:</span>
                  <p className="text-gray-500">Locked versions (SQLAlchemy, Celery, Redis, asyncpg, passlib, httpx) in Python 3.12 venv.</p>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-start space-x-3 text-xs">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="font-semibold text-gray-800">Frontend React 18 & Vite:</span>
                  <p className="text-gray-500">TypeScript 5.6, Tailwind CSS v3 forms, Lucide icons, TanStack Query, and Axios client.</p>
                </div>
              </div>

              <div className="flex items-start space-x-3 text-xs">
                <CheckCircle2 className="w-4 h-4 text-emerald-600 mt-0.5 flex-shrink-0" />
                <div>
                  <span className="font-semibold text-gray-800">Repository Standards:</span>
                  <p className="text-gray-500">Clean .env.example, .gitignore, and responsive layout shell with mobile drawer.</p>
                </div>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-4 border-t border-gray-100 flex items-center justify-between text-xs text-gray-500">
            <span>Next Milestone: <strong className="text-gray-800">Feature 2 — Database Schema & Read-Heavy Indexing</strong></span>
            <span className="inline-flex items-center text-emerald-600 font-medium">
              Ready <ArrowRight className="w-3.5 h-3.5 ml-1" />
            </span>
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default App;
