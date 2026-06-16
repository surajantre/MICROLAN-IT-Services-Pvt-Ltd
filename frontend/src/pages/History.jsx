import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import InvoiceDetailModal from '../components/InvoiceDetailModal';

export default function History() {
  const [invoices, setInvoices] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(10);
  const [search, setSearch] = useState('');
  const [sortBy, setSortBy] = useState('created_at');
  const [sortDir, setSortDir] = useState('desc');
  const [loading, setLoading] = useState(true);
  const [selectedInvoice, setSelectedInvoice] = useState(null);

  const fetchInvoices = async () => {
    setLoading(true);
    try {
      const response = await api.getInvoices({ page, pageSize, search, sortBy, sortDir });
      if (response) {
        setInvoices(response.items || []);
        setTotal(response.total || 0);
      }
    } catch (err) {
      console.error('Database query operation failure:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchInvoices();
  }, [page, sortBy, sortDir]);

  const handleSearchSubmit = (e) => {
    e.preventDefault();
    setPage(1);
    fetchInvoices();
  };

  const handleDelete = async (id, e) => {
    e.stopPropagation();
    if (!window.confirm(`Permanently remove Invoice #${id}? This cannot be undone.`)) return;

    try {
      await api.deleteInvoice(id);
      fetchInvoices();
    } catch (err) {
      alert('Delete operation encountered errors: ' + err.message);
    }
  };

  const handleSort = (field) => {
    if (sortBy === field) {
      setSortDir(sortDir === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(field);
      setSortDir('desc');
    }
    setPage(1);
  };

  const totalPages = Math.ceil(total / pageSize) || 1;

  return (
    <div className="space-y-6 animate-fade-in">
      {/* Search Header Area */}
      <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
        <form onSubmit={handleSearchSubmit} className="flex flex-wrap gap-4 items-center justify-between">
          <div className="flex-1 min-w-[280px] relative">
            <input
              type="text"
              placeholder="Search by invoice number or language script..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-3 rounded-xl border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium"
            />
            <svg className="w-5 h-5 absolute left-3.5 top-3.5 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          </div>
          <button
            type="submit"
            className="px-6 py-3 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-sm rounded-xl shadow-lg shadow-indigo-600/10 transition-all"
          >
            Apply Query Filter
          </button>
        </form>
      </div>

      {/* Primary History Grid Container */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
        <div className="overflow-x-auto font-medium">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-100 text-xs font-semibold text-slate-500 uppercase tracking-wider select-none">
                <th onClick={() => handleSort('id')} className="py-4 px-6 cursor-pointer hover:bg-slate-100">ID {sortBy === 'id' ? (sortDir === 'asc' ? '▲' : '▼') : ''}</th>
                {/* <th onClick={() => handleSort('invoice_number')} className="py-4 px-6 cursor-pointer hover:bg-slate-100">Invoice Ref {sortBy === 'invoice_number' ? (sortDir === 'asc' ? '▲' : '▼') : ''}</th> */}
                <th onClick={() => handleSort('created_at')} className="py-4 px-6 cursor-pointer hover:bg-slate-100">Scan Date {sortBy === 'created_at' ? (sortDir === 'asc' ? '▲' : '▼') : ''}</th>
                <th onClick={() => handleSort('language_detected')} className="py-4 px-6 cursor-pointer hover:bg-slate-100">Language {sortBy === 'language_detected' ? (sortDir === 'asc' ? '▲' : '▼') : ''}</th>
                <th onClick={() => handleSort('confidence_score')} className="py-4 px-6 cursor-pointer hover:bg-slate-100">Confidence {sortBy === 'confidence_score' ? (sortDir === 'asc' ? '▲' : '▼') : ''}</th>
                <th onClick={() => handleSort('grand_total')} className="py-4 px-6 cursor-pointer hover:bg-slate-100 text-right">Grand Total {sortBy === 'grand_total' ? (sortDir === 'asc' ? '▲' : '▼') : ''}</th>
                <th className="py-4 px-6 text-center">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm text-slate-600">
              {loading ? (
                <tr>
                  <td colSpan="7" className="py-20 text-center">
                    <svg className="animate-spin h-8 w-8 text-indigo-600 mx-auto" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                  </td>
                </tr>
              ) : invoices.length === 0 ? (
                <tr>
                  <td colSpan="7" className="py-12 text-center text-slate-400">
                    No matching database records found.
                  </td>
                </tr>
              ) : (
                invoices.map((inv) => (
                  <tr
                    key={inv.id}
                    onClick={() => setSelectedInvoice(inv)}
                    className="hover:bg-slate-50/50 cursor-pointer transition-all"
                  >
                    <td className="py-4 px-6 font-bold text-slate-800">#{inv.id}</td>
                    {/* <td className="py-4 px-6 font-semibold text-indigo-600">{inv.invoice_number || 'N/A'}</td> */}
                    <td className="py-4 px-6 text-xs font-semibold text-slate-500">
                      {new Date(inv.created_at).toLocaleDateString(undefined, { dateStyle: 'long' })}
                    </td>
                    <td className="py-4 px-6 uppercase text-xs font-bold">{inv.language_detected || 'Unknown'}</td>
                    <td className="py-4 px-6">
                      <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold ${
                        inv.confidence_score >= 0.85 ? 'bg-emerald-50 text-emerald-700' :
                        inv.confidence_score >= 0.70 ? 'bg-amber-50 text-amber-700' : 'bg-red-50 text-red-700'
                      }`}>
                        {((inv.confidence_score || 0) * 100).toFixed(0)}%
                      </span>
                    </td>
                    <td className="py-4 px-6 text-right font-black text-slate-800">
                      ₹{(inv.grand_total || 0).toLocaleString('en-IN')}
                    </td>
                    <td className="py-4 px-6">
                      <div className="flex items-center justify-center space-x-2">
                        <button
                          type="button"
                          onClick={(e) => { e.stopPropagation(); setSelectedInvoice(inv); }}
                          className="p-1.5 hover:bg-slate-100 rounded-lg text-slate-500 hover:text-slate-700"
                          title="View Details"
                        >
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                          </svg>
                        </button>
                        <button
                          type="button"
                          onClick={(e) => handleDelete(inv.id, e)}
                          className="p-1.5 hover:bg-red-50 rounded-lg text-slate-400 hover:text-red-600"
                          title="Delete Record"
                        >
                          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Controls */}
        <div className="p-4 bg-slate-50 border-t border-slate-100 flex items-center justify-between">
          <span className="text-xs font-semibold text-slate-500">
            Total items detected: {total} (Page {page} of {totalPages})
          </span>
          <div className="flex space-x-2">
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-4 py-2 border border-slate-200 bg-white text-slate-700 text-xs font-bold rounded-lg shadow-sm hover:bg-slate-50 disabled:opacity-40"
            >
              Previous
            </button>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              className="px-4 py-2 border border-slate-200 bg-white text-slate-700 text-xs font-bold rounded-lg shadow-sm hover:bg-slate-50 disabled:opacity-40"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {selectedInvoice && (
        <InvoiceDetailModal
          invoiceId={selectedInvoice.id}
          onClose={() => setSelectedInvoice(null)}
        />
      )}
    </div>
  );
}