import React, { useState } from 'react';
import { api } from '../services/api';

const SUPPORTED_LANGS = [
  { code: 'auto', name: 'Auto-Detect Language' },
  { code: 'en', name: 'English (Default)' },
  { code: 'hi', name: 'Hindi (हिन्दी)' },
  { code: 'mr', name: 'Marathi (मराठी)' },
  { code: 'gu', name: 'Gujarati (ગુજરાતી)' },
  { code: 'ta', name: 'Tamil (தமிழ்)' },
  { code: 'te', name: 'Telugu (తెలుగు)' }
];

export default function Upload() {
  const [file, setFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [lang, setLang] = useState('auto');
  const [loading, setLoading] = useState(false);
  const [progressMsg, setProgressMsg] = useState('');
  const [result, setResult] = useState(null);
  const [errorMsg, setErrorMsg] = useState('');
  const [showRawText, setShowRawText] = useState(false);

  const handleFileChange = (e) => {
    const selected = e.target.files[0];
    if (selected) {
      if (selected.size > 10 * 1024 * 1024) {
        setErrorMsg('File sizes must not exceed 10MB.');
        return;
      }
      setFile(selected);
      setPreviewUrl(URL.createObjectURL(selected));
      setErrorMsg('');
      setResult(null);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) {
      if (droppedFile.size > 10 * 1024 * 1024) {
        setErrorMsg('File size must not exceed 10MB limit.');
        return;
      }
      setFile(droppedFile);
      setPreviewUrl(URL.createObjectURL(droppedFile));
      setErrorMsg('');
      setResult(null);
    }
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setErrorMsg('');
    
    // Process step progression labels
    const stages = [
      'Sending payload to server...',
      'Running OpenCV image preprocessing (Denoising & Deskewing)...',
      'Executing multilingual neural OCR layers...',
      'Validating mathematical integrity checks...',
      'Parsing structured item results...'
    ];
    let step = 0;
    setProgressMsg(stages[0]);

    const interval = setInterval(() => {
      if (step < stages.length - 1) {
        step++;
        setProgressMsg(stages[step]);
      }
    }, 1500);

    try {
      const response = await api.uploadInvoice(file, lang);
      clearInterval(interval);
      if (response && response.success) {
        setResult(response.data);
      } else {
        setErrorMsg('Failed to process. No output returned.');
      }
    } catch (err) {
      clearInterval(interval);
      setErrorMsg(err.message || 'Processing failed.');
    } finally {
      setLoading(false);
      setProgressMsg('');
    }
  };

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Control Column (Drop zone & configuration parameters) */}
        <div className="lg:col-span-5 space-y-6">
          <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm">
            <h3 className="text-base font-bold text-slate-800 mb-4">Invoice Acquisition Panel</h3>
            
            <form onSubmit={handleUpload} className="space-y-4">
              {/* Language Selection Block */}
              <div>
                <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide block mb-1">
                  Language Context Hint
                </label>
                <select
                  value={lang}
                  onChange={(e) => setLang(e.target.value)}
                  className="w-full px-3 py-2.5 bg-slate-50 rounded-lg border border-slate-200 text-sm outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all font-medium text-slate-700"
                >
                  {SUPPORTED_LANGS.map(l => (
                    <option key={l.code} value={l.code}>{l.name}</option>
                  ))}
                </select>
              </div>

              {/* Drag and Drop Zone */}
              <div
                onDragOver={(e) => e.preventDefault()}
                onDrop={handleDrop}
                className={`border-2 border-dashed rounded-xl p-8 text-center transition-all cursor-pointer ${
                  file ? 'border-indigo-400 bg-indigo-50/10' : 'border-slate-300 hover:border-slate-400 bg-slate-50/50'
                }`}
              >
                {previewUrl ? (
                  <div className="space-y-4">
                    <img
                      src={previewUrl}
                      alt="Invoice Preview"
                      className="max-h-56 mx-auto rounded-lg shadow-sm border border-slate-200"
                    />
                    <div className="flex items-center justify-center space-x-2">
                      <span className="text-xs font-semibold text-slate-500 max-w-xs truncate">{file.name}</span>
                      <button
                        type="button"
                        onClick={() => { setFile(null); setPreviewUrl(null); setResult(null); }}
                        className="text-red-500 hover:text-red-600 font-bold text-xs uppercase ml-2"
                      >
                        Clear
                      </button>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    <div className="text-slate-400 mx-auto w-12 h-12 flex items-center justify-center">
                      <svg className="w-10 h-10" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <p className="text-sm font-semibold text-slate-700">Drag invoice image file here</p>
                    <p className="text-xs text-slate-400">JPEG, PNG or BMP format limits (Max 10MB)</p>
                    <div className="pt-2">
                      <label className="inline-flex items-center px-4 py-2 bg-white border border-slate-200 rounded-lg shadow-sm text-xs font-bold text-slate-700 hover:bg-slate-50 cursor-pointer">
                        Select Local File
                        <input type="file" className="hidden" accept="image/*,application/pdf" onChange={handleFileChange} />
                      </label>
                    </div>
                  </div>
                )}
              </div>

              {errorMsg && (
                <div className="p-3 bg-red-50 border-l-4 border-red-500 text-xs text-red-700 rounded-md">
                  {errorMsg}
                </div>
              )}

              <button
                type="submit"
                disabled={!file || loading}
                className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 text-white rounded-xl text-sm font-bold shadow-lg shadow-indigo-600/15 transition-all disabled:opacity-45"
              >
                {loading ? 'Processing Document...' : 'Execute Analysis Pipeline'}
              </button>
            </form>
          </div>

          {/* Loader Stage Information Overlay */}
          {loading && (
            <div className="bg-slate-900 p-6 rounded-2xl text-white shadow-xl space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-400 uppercase tracking-widest">Active Worker Pipeline</span>
                <svg className="animate-spin h-5 w-5 text-indigo-400" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                </svg>
              </div>
              <p className="text-sm font-medium leading-relaxed">{progressMsg}</p>
              <div className="w-full bg-slate-800 rounded-full h-1.5 overflow-hidden">
                <div className="bg-gradient-to-r from-blue-500 to-indigo-500 h-1.5 rounded-full animate-pulse" style={{ width: '65%' }}></div>
              </div>
            </div>
          )}
        </div>

        {/* Right Output Area (Parsed Results Display) */}
        <div className="lg:col-span-7">
          {result ? (
            <div className="space-y-6">
              
              {/* Core Output Metrics Grid */}
              <div className="bg-white p-6 rounded-2xl border border-slate-200/80 shadow-sm space-y-6">
                <div className="flex flex-wrap items-center justify-between gap-4">
                  <div>
                    <span className="text-xs font-bold text-indigo-500 uppercase tracking-wide block">Extraction Status</span>
                    <h3 className="text-xl font-extrabold text-slate-800">Success</h3>
                  </div>
                  <div className="flex space-x-2">
                    <span className="inline-flex items-center px-3 py-1 bg-indigo-50 text-indigo-700 text-xs font-bold rounded-lg border border-indigo-100">
                      Lang: {result.language_detected ? result.language_detected.toUpperCase() : 'UNKNOWN'}
                    </span>
                    <span className={`inline-flex items-center px-3 py-1 text-xs font-bold rounded-lg border ${
                      result.confidence_score >= 0.85 ? 'bg-emerald-50 text-emerald-700 border-emerald-100' :
                      result.confidence_score >= 0.70 ? 'bg-amber-50 text-amber-700 border-amber-100' : 'bg-red-50 text-red-700 border-red-100'
                    }`}>
                      Confidence: {((result.confidence_score || 0) * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 border-t border-b border-slate-100 py-4">
                  <div>
                    <span className="text-xs text-slate-400 block font-medium">Invoice Number</span>
                    <span className="text-base font-bold text-slate-800">{result.invoice_no || 'Not Found'}</span>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400 block font-medium">Grand Total (Validated)</span>
                    <span className="text-lg font-black text-emerald-600">
                      ₹{(result.grand_total || 0).toLocaleString('en-IN')}
                    </span>
                  </div>
                </div>

                {/* Warnings Section */}
                {result.warnings && result.warnings.length > 0 && (
                  <div className="bg-amber-50 border-l-4 border-amber-500 p-4 rounded-xl">
                    <h4 className="text-xs font-bold text-amber-800 uppercase tracking-wider mb-2 flex items-center space-x-1.5">
                      <svg className="w-4.5 h-4.5 text-amber-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      <span>Pipeline System Warnings</span>
                    </h4>
                    <ul className="list-disc pl-5 text-xs text-amber-700 space-y-1 font-medium">
                      {result.warnings.map((w, idx) => (
                        <li key={idx}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Parsed Products Table */}
              <div className="bg-white rounded-2xl border border-slate-200/80 shadow-sm overflow-hidden">
                <div className="p-4 border-b border-slate-100">
                  <h4 className="text-sm font-extrabold text-slate-800">Extracted Line Items</h4>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-100 text-xs font-semibold text-slate-500 uppercase tracking-wider">
                        <th className="py-3 px-4">Item Name</th>
                        <th className="py-3 px-4 text-center">Qty</th>
                        <th className="py-3 px-4 text-right">Unit Price</th>
                        <th className="py-3 px-4 text-right">Total</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-xs text-slate-600">
                      {result.products && result.products.length > 0 ? (
                        result.products.map((p, idx) => (
                          <tr key={idx} className="hover:bg-slate-50/50">
                            <td className="py-3 px-4 font-bold text-slate-800">{p.name}</td>
                            <td className="py-3 px-4 text-center font-medium">{p.qty}</td>
                            <td className="py-3 px-4 text-right font-medium">₹{p.price.toLocaleString('en-IN')}</td>
                            <td className="py-3 px-4 text-right font-bold text-indigo-600">₹{p.total.toLocaleString('en-IN')}</td>
                          </tr>
                        ))
                      ) : (
                        <tr>
                          <td colSpan="4" className="py-6 text-center text-slate-400 font-medium">
                            No structured records resolved from document parsing.
                          </td>
                        </tr>
                      )}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Raw OCR Text Panel */}
              <div className="bg-slate-900 rounded-2xl text-slate-300 shadow-sm overflow-hidden">
                <button
                  type="button"
                  onClick={() => setShowRawText(!showRawText)}
                  className="w-full flex items-center justify-between p-4 text-sm font-bold border-b border-slate-800"
                >
                  <span className="text-indigo-400">View Raw Engine OCR Dump</span>
                  <span>{showRawText ? 'Collapse' : 'Expand'}</span>
                </button>
                {showRawText && (
                  <pre className="p-4 overflow-auto text-xs font-mono max-h-56 leading-relaxed bg-slate-950/80 text-emerald-400/90 whitespace-pre-wrap">
                    {result.raw_text || 'No raw string buffers collected from system.'}
                  </pre>
                )}
              </div>

            </div>
          ) : (
            <div className="bg-slate-100 border-2 border-dashed border-slate-300 rounded-2xl h-96 flex flex-col items-center justify-center text-slate-400 p-6 text-center">
              <svg className="w-12 h-12 mb-4 text-slate-300" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <h3 className="text-sm font-bold text-slate-500 mb-1">Awaiting Engine Submission</h3>
              <p className="text-xs max-w-sm">
                Acquire an image, set configuration hints, and submit to trigger OCR, preprocessing, and database storage.
              </p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}