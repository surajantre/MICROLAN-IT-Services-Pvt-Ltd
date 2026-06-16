import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function Dashboard({ setActiveTab }) {
  const [stats, setStats] = useState({
    totalCount: 0,
    averageConfidence: 0,
    languages: {},
    errorWarnings: 0,
  });
  const [recentItems, setRecentItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadDashboardData = async () => {
      try {
        const response = await api.getInvoices({ page: 1, pageSize: 5 });
        if (response) {
          const rawItems = response.items || [];
          setRecentItems(rawItems);
          
          // Compute statistical aggregates
          const count = response.total || rawItems.length;
          let sumConf = 0;
          let warningCount = 0;
          const langMap = {};

          // Request secondary sweep for statistics compiling if total records exceed current payload page boundaries
          const fullPull = await api.getInvoices({ page: 1, pageSize: 100 });
          const allInvoices = fullPull.items || [];

          allInvoices.forEach(inv => {
            sumConf += Number(inv.confidence_score || 0);
            if (inv.warnings) warningCount++;
            const ln = inv.language_detected || 'Unknown';
            langMap[ln] = (langMap[ln] || 0) + 1;
          });

          setStats({
            totalCount: count,
            averageConfidence: allInvoices.length ? (sumConf / allInvoices.length) * 100 : 0,
            languages: langMap,
            errorWarnings: warningCount,
          });
        }
      } catch (err) {
        console.error('Failed to load dashboard parameters.', err);
      } finally {
        setLoading(false);
      }
    };

    loadDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="h-96 flex items-center justify-center">
        <div className="text-center space-y-4">
          <svg className="animate-spin h-10 w-10 text-indigo-600 mx-auto" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
          </svg>
          <span className="text-sm font-semibold text-slate-500">Retrieving intelligence metrics...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      {/* KPI Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6">
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex items-center space-x-4">
          <div className="p-3.5 bg-indigo-50 text-indigo-600 rounded-xl">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Total Processed</p>
            <h3 className="text-2xl font-bold text-slate-800 mt-1">{stats.totalCount}</h3>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex items-center space-x-4">
          <div className="p-3.5 bg-emerald-50 text-emerald-600 rounded-xl">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Avg Confidence</p>
            <h3 className="text-2xl font-bold text-slate-800 mt-1">{stats.averageConfidence.toFixed(1)}%</h3>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex items-center space-x-4">
          <div className="p-3.5 bg-amber-50 text-amber-600 rounded-xl">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Anomalies Detected</p>
            <h3 className="text-2xl font-bold text-slate-800 mt-1">{stats.errorWarnings}</h3>
          </div>
        </div>

        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm flex items-center space-x-4">
          <div className="p-3.5 bg-purple-50 text-purple-600 rounded-xl">
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 11.37 7.363 16.155 3 18.001" />
            </svg>
          </div>
          <div>
            <p className="text-xs font-semibold text-slate-400 uppercase tracking-wider">Top Script Language</p>
            <h3 className="text-2xl font-bold text-slate-800 mt-1 capitalize">
              {Object.keys(stats.languages).length ? Object.keys(stats.languages).reduce((a, b) => stats.languages[a] > stats.languages[b] ? a : b) : 'N/A'}
            </h3>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Core Quick Action Center */}
        <div className="lg:col-span-2 bg-white p-8 rounded-2xl border border-slate-200/80 shadow-sm flex flex-col justify-between">
          <div>
            <h3 className="text-lg font-bold text-slate-800 mb-2">Multilingual Processing Engine</h3>
            <p className="text-sm text-slate-500 leading-relaxed max-w-xl">
              Convert raw, distorted handwritten bills and multilingual documents into validated JSON schemas. 
              The pipeline supports English, Hindi (हिन्दी), Marathi (मराठी), Gujarati (ગુજરાતી), Tamil (தமிழ்), and Telugu (తెలుగు) using self-correction logic.
            </p>
          </div>
          <div className="mt-8">
            <button
              onClick={() => setActiveTab('upload')}
              className="inline-flex items-center space-x-2 bg-indigo-600 hover:bg-indigo-700 text-white font-medium text-sm px-6 py-3.5 rounded-xl shadow-lg shadow-indigo-600/10 transition-all"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              <span>Process New Document</span>
            </button>
          </div>
        </div>

        {/* Language Spread */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
          <h3 className="text-base font-bold text-slate-800 mb-4">Volume by Script Language</h3>
          {Object.keys(stats.languages).length === 0 ? (
            <div className="h-44 flex items-center justify-center text-slate-400 text-sm">
              No language details logged yet
            </div>
          ) : (
            <div className="space-y-4">
              {Object.entries(stats.languages).map(([lang, val]) => {
                const pct = (val / stats.totalCount) * 100;
                return (
                  <div key={lang}>
                    <div className="flex justify-between text-xs font-semibold text-slate-600 mb-1">
                      <span className="capitalize">{lang}</span>
                      <span>{val} ({pct.toFixed(0)}%)</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                      <div className="bg-indigo-500 h-2 rounded-full" style={{ width: `${pct}%` }}></div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Recent Scans Overview */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="p-6 border-b border-slate-100">
          <h3 className="text-base font-bold text-slate-800">Recent Invoice Runs</h3>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                <th className="py-4 px-6">ID</th>
                <th className="py-4 px-6">Invoice Number</th>
                <th className="py-4 px-6">Confidence</th>
                <th className="py-4 px-6">Grand Total</th>
                <th className="py-4 px-6">Language</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm text-slate-600">
              {recentItems.length === 0 ? (
                <tr>
                  <td colSpan="5" className="py-8 text-center text-slate-400">
                    No run logs found in database repository.
                  </td>
                </tr>
              ) : (
                recentItems.map((inv) => (
                  <tr key={inv.id} className="hover:bg-slate-50/50">
                    <td className="py-4 px-6 font-semibold text-slate-800">#{inv.id}</td>
                    <td className="py-4 px-6 font-medium text-indigo-600">{inv.invoice_number || 'N/A'}</td>
                    <td className="py-4 px-6">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                        inv.confidence_score >= 0.85 ? 'bg-emerald-50 text-emerald-700' :
                        inv.confidence_score >= 0.70 ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700'
                      }`}>
                        {((inv.confidence_score || 0) * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="py-4 px-6 font-semibold">₹{(inv.grand_total || 0).toLocaleString('en-IN')}</td>
                    <td className="py-4 px-6 capitalize">{inv.language_detected || 'Unknown'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}