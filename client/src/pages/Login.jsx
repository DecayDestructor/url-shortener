import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiPost } from "../lib/api";

export default function Login() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user) navigate(user.is_admin ? "/admin" : "/");
  }, [user, navigate]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await apiPost("/auth/login", form);
      login(data);
      navigate(data.is_admin ? "/admin" : "/");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12" style={{ background: "#FFFEF0" }}>
      <div className="w-full max-w-md">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 justify-center mb-10">
          <div className="w-10 h-10 flex items-center justify-center" style={{ background: "#FFE500", border: "2.5px solid #0a0a0a", boxShadow: "3px 3px 0px #0a0a0a" }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="#0a0a0a" strokeWidth="2.5" className="w-5 h-5">
              <path d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101" strokeLinecap="round" />
              <path d="M10.172 13.828a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" strokeLinecap="round" />
            </svg>
          </div>
          <span className="font-black text-2xl tracking-tight" style={{ fontFamily: "'Space Grotesk', sans-serif", color: "#0a0a0a" }}>
            snip<span style={{ color: "#FF4040" }}>.ly</span>
          </span>
        </Link>

        {/* Card */}
        <div className="p-8" style={{ background: "#FFFEF0", border: "2.5px solid #0a0a0a", boxShadow: "6px 6px 0px #0a0a0a" }}>
          {/* Header stripe */}
          <div className="-mx-8 -mt-8 px-8 py-4 mb-6" style={{ background: "#FFE500", borderBottom: "2.5px solid #0a0a0a" }}>
            <h1 className="text-2xl font-black" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>Welcome back</h1>
            <p className="text-sm font-medium mt-0.5" style={{ color: "#444" }}>Sign in to your snip.ly account</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-black uppercase tracking-widest mb-1.5">Email</label>
              <input
                id="login-email"
                type="email"
                required
                autoComplete="email"
                value={form.email}
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                placeholder="you@example.com"
                className="w-full px-4 py-3 text-sm font-medium input-brutal"
                style={{ border: "2.5px solid #0a0a0a" }}
              />
            </div>

            <div>
              <label className="block text-xs font-black uppercase tracking-widest mb-1.5">Password</label>
              <input
                id="login-password"
                type="password"
                required
                autoComplete="current-password"
                value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                placeholder="••••••••"
                className="w-full px-4 py-3 text-sm font-medium input-brutal"
                style={{ border: "2.5px solid #0a0a0a" }}
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 px-4 py-3" style={{ background: "#FF4040", border: "2.5px solid #0a0a0a", boxShadow: "3px 3px 0 #0a0a0a" }}>
                <svg className="w-4 h-4 shrink-0 text-white" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                </svg>
                <p className="text-white text-xs font-bold">{error}</p>
              </div>
            )}

            <button
              id="login-submit"
              type="submit"
              disabled={loading}
              className="w-full py-3.5 text-sm font-black uppercase tracking-wider btn-brutal mt-2"
              style={{ background: "#FFE500", border: "2.5px solid #0a0a0a", boxShadow: "4px 4px 0 #0a0a0a" }}
            >
              {loading ? (
                <span className="flex items-center gap-2">
                  <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                  Signing in…
                </span>
              ) : "Sign in →"}
            </button>
          </form>

          <div className="mt-6 pt-6 text-center space-y-3" style={{ borderTop: "2px dashed #ccc" }}>
            <p className="text-sm font-medium">
              No account?{" "}
              <Link to="/register" className="font-black underline" style={{ color: "#FF4040" }}>Create one free</Link>
            </p>
            <Link to="/admin/login" className="block text-xs font-bold uppercase tracking-widest" style={{ color: "#888" }}>
              Admin login →
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}
