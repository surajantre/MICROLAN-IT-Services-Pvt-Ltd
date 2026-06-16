import React, { useState } from 'react';
import { api } from '../services/api';

export default function Login({ onSuccess }) {
  const [isRegistering, setIsRegistering] = useState(false);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setLoading(true);

    try {
      if (isRegistering) {
        await api.register(username, password);
        setSuccessMsg('Account created successfully. Please sign in.');
        setIsRegistering(false);
        setPassword('');
      } else {
        await api.login(username, password);
        onSuccess();
      }
    } catch (err) {
      setError(err.message || 'Something went wrong.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center relative overflow-hidden bg-slate-950">

      {/* Background Glow */}
      <div className="absolute inset-0">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-indigo-600 rounded-full blur-3xl opacity-30 animate-pulse"></div>
        <div className="absolute top-40 -right-40 w-96 h-96 bg-purple-600 rounded-full blur-3xl opacity-30 animate-pulse"></div>
        <div className="absolute bottom-0 left-1/2 w-96 h-96 bg-cyan-500 rounded-full blur-3xl opacity-20 animate-pulse"></div>
      </div>

      {/* Card */}
      <div className="relative w-full max-w-md mx-4">
        <div className="backdrop-blur-xl bg-white/10 border border-white/20 shadow-2xl rounded-2xl p-8 text-white">

          {/* Header */}
          <div className="text-center mb-6">
            <div className="mx-auto w-14 h-14 rounded-2xl bg-gradient-to-r from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg">
              🔐
            </div>

            <h2 className="text-2xl font-bold mt-4">
              {isRegistering ? 'Create Account' : 'Welcome Back'}
            </h2>

            <p className="text-sm text-white/60 mt-1">
              {isRegistering
                ? 'Sign up to access the system'
                : 'Login to continue your session'}
            </p>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-4 p-3 rounded-lg bg-red-500/20 border border-red-400/30 text-red-200 text-sm">
              {error}
            </div>
          )}

          {/* Success */}
          {successMsg && (
            <div className="mb-4 p-3 rounded-lg bg-green-500/20 border border-green-400/30 text-green-200 text-sm">
              {successMsg}
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-5">

            <div>
              <label className="text-xs text-white/70">Username</label>
              <input
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter username"
                className="w-full mt-1 px-4 py-3 rounded-xl bg-white/10 border border-white/20 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-indigo-400 transition"
                required
              />
            </div>

            <div>
              <label className="text-xs text-white/70">Password</label>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full mt-1 px-4 py-3 rounded-xl bg-white/10 border border-white/20 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-indigo-400 transition"
                required
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 rounded-xl font-semibold transition-all duration-300
              bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500
              hover:scale-[1.02] active:scale-[0.98]
              disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
            >
              {loading ? 'Processing...' : isRegistering ? 'Create Account' : 'Login'}
            </button>
          </form>

          {/* Toggle */}
          <p className="text-center text-xs text-white/60 mt-6">
            {isRegistering ? 'Already have an account?' : "Don't have an account?"}{' '}
            <button
              onClick={() => {
                setIsRegistering(!isRegistering);
                setError('');
                setSuccessMsg('');
              }}
              className="text-indigo-300 hover:text-indigo-200 font-semibold"
            >
              {isRegistering ? 'Sign in' : 'Register'}
            </button>
          </p>
        </div>
      </div>
    </div>
  );
}