import React, { useState, useEffect } from 'react';
import { api } from '../services/api';

export default function InvoiceDetailModal({ invoiceId, onClose }) {
  const [invoice, setInvoice] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchDetail = async () => {
      try {
        const data = await api.getInvoiceById(invoiceId);
        if (data) {
          setInvoice(data);
        }
      } catch (err) {
        console.error('Failed to resolve system detail', err);
      } finally {
        setLoading(false);
      }
    };
    fetchDetail();
  }, [invoiceId]);

  // Safely parse semicolon separated warnings back to array
  const parseWarnings = (warnStr) => {
    if (!warnStr) return [];
    return warnStr.split(';').map(w => w.trim()).filter(Boolean);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/60 backdrop-blur-sm p-4 overflow-y-auto">
      <div className="bg-white rounded-2xl w-full max-w-4xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]">
        
        {/* Modal Header */}
        <div className="p-6 border-b border-slate-100 flex items-center justify-between bg-slate-900 text-white">
          <div>
            <h3 className="text-lg font-extrabold">Invoice Details Record</h3>
            <p className="text-xs text-slate-400">Database Entry Index: #{invoiceId}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 text-slate-400 hover:text-white rounded-lg hover:bg-slate-800 transition-all"
          >
            <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Modal Scroll Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {loading ? (
            <div className="py-20 flex justify-center">
              <svg className="animate-spin h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
            </div>
          ) : invoice ? (
            <div className="grid grid-cols-1 md:grid-cols-12 gap-6">
              
              {/* Image & System Attributes */}
              <div className="md:col-span-5 space-y-6">
                <div className="border border-slate-200 rounded-xl overflow-hidden bg-slate-50 p-4 flex items-center justify-center">
                  {/* Dynamic absolute path pointer to raw backend storage if served static */}
                  {invoice.invoice_image ? (
                    <div className="text-center space-y-2">
                      <span className="text-xs text-slate-500 block break-all font-mono">Image reference path:</span>
                      <code className="text-[10px] bg-slate-200 p-1.5 rounded block text-slate-700 break-all">{invoice.invoice_image}</code>
                    </div>
                  ) : (
                    <span className="text-xs text-slate-400 font-medium py-8">No visual snapshot attached.</span>
                  )}
                </div>

                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs space-y-3 font-medium">
                  <h4 className="font-extrabold text-slate-800 uppercase tracking-wider text-[10px]">Processing Context</h4>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Scan Execution Time:</span>
                    <span className="text-slate-700 font-bold">{new Date(invoice.created_at).toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Confidence Rating:</span>
                    <span className="text-slate-700 font-bold">{((invoice.confidence_score || 0) * 100).toFixed(1)}%</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-400">Language Detected:</span>
                    <span className="text-slate-700 font-bold uppercase">{invoice.language_detected || 'Unknown'}</span>
                  </div>
                </div>
              </div>

              {/* Parsed Items Summary */}
              <div className="md:col-span-7 space-y-6">
                <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
                  <div className="flex justify-between items-center mb-2">
                    <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Invoice Identifier Reference</span>
                    <span className="text-xs font-bold text-indigo-600">{invoice.invoice_number || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-xs text-slate-400 font-bold uppercase tracking-wider">Summed Grand Total</span>
                    <span className="text-lg font-black text-emerald-600">₹{(invoice.grand_total || 0).toLocaleString('en-IN')}</span>
                  </div>
                </div>

                {invoice.warnings && (
                  <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-xl text-xs">
                    <h5 className="font-bold text-amber-800 mb-1">Warnings Logged</h5>
                    <ul className="list-disc pl-5 text-amber-700 space-y-0.5">
                      {parseWarnings(invoice.warnings).map((w, i) => (
                        <li key={i}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}

                <div className="bg-white rounded-xl border border-slate-200 overflow-hidden">
                  <div className="p-4 border-b border-slate-100 bg-slate-50">
                    <h4 className="text-xs font-extrabold text-slate-700 uppercase tracking-wider">Line Itemization Breakdown</h4>
                  </div>
                  <table className="w-full text-left text-xs border-collapse font-medium">
                    <thead>
                      <tr className="bg-slate-50/50 border-b border-slate-100 text-slate-400 uppercase tracking-wider font-bold">
                        <th className="py-3 px-4">Item Name</th>
                        <th className="py-3 px-4 text-center">Qty</th>
                        <th className="py-3 px-4 text-right">Price</th>
                        <th className="py-3 px-4 text-right">Subtotal</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-600">
                      {invoice.items && invoice.items.length > 0 ? (
                        invoice.items.map((item) => (
                          <tr key={item.id} className="hover:bg-slate-50/20">
                            <td className="py-3 px-4 font-bold text-slate-800">{item.product_name}</td>
                            <td className="py-3 px-4 text-center">{item.quantity}</td>
                            <td className="py-3 px-4 text-right">₹{Number(item.unit_price).toLocaleString('en-IN')}</td>
                            <td className="py-3 px-4 text-right font-bold text-indigo-600">₹{Number(item.total_amount).toLocaleString('en-IN')}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="4" className="py-4 text-center text-slate-400">No item values.</td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>

                {/* Collapsible raw string section inside database detail retrieval */}
                <div className="bg-slate-950 p-4 rounded-xl text-emerald-400 font-mono text-[11px] leading-relaxed max-h-44 overflow-auto">
                  <span className="text-slate-500 font-bold uppercase block mb-1 tracking-wider text-[9px]">Captured Raw String Block</span>
                  {invoice.raw_text || 'No raw strings recorded.'}
                </div>

              </div>

            </div>
          ) : (
            <p className="text-center text-slate-500 font-medium">Record retrieval issues encountered.</p>
          )}
        </div>

        {/* Modal Action Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-slate-200 hover:bg-slate-300 text-slate-800 text-xs font-bold rounded-xl shadow-sm transition-all"
          >
            Dismiss View
          </button>
        </div>

      </div>
    </div>
  );
}