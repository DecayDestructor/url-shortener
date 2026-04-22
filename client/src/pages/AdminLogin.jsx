import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiPost } from "../lib/api";

export default function AdminLogin() {
  const { login, user } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (user?.is_admin) navigate("/admin");
    else if (user) navigate("/");
  }, [user, navigate]);

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const data = await apiPost("/auth/admin/login", form);
      login(data);
      navigate("/admin");
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center px-4 py-12" style={{ background: "#F5F0DC" }}>
      <div className="w-full max-w-md">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-3 justify-center mb-10">
          <div className="w-10 h-10 flex items-center justify-center" style={{ background: "#0a0a0a", border: "2.5px solid #0a0a0a", boxShadow: "3px 3px 0px #FFE500" }}>
            <svg viewBox="0 0 24 24" fill="none" stroke="#FFE500" strokeWidth="2.5" className="w-5 h-5">
              <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <span className="font-black text-2xl tracking-tight" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>
            snip<span style={{ color: "#FF4040" }}>.ly</span>
            <span className="text-xs font-black ml-2 px-2 py-0.5 align-middle" style={{ background: "#FFE500", border: "2px solid #0a0a0a", boxShadow: "2px 2px 0 #0a0a0a" }}>ADMIN</span>
          </span>
        </Link>

        <div className="p-8" style={{ background: "#FFFEF0", border: "2.5px solid #0a0a0a", boxShadow: "6px 6px 0px #0a0a0a" }}>
          {/* Header */}
          <div className="-mx-8 -mt-8 px-8 py-5 mb-6 text-center" style={{ background: "#0a0a0a", borderBottom: "2.5px solid #0a0a0a" }}>
            <div className="w-12 h-12 mx-auto mb-3 flex items-center justify-center" style={{ background: "#FFE500", border: "2px solid #FFE500" }}>
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="#0a0a0a" strokeWidth="2.5">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <h1 className="text-2xl font-black text-white" style={{ fontFamily: "'Space Grotesk', sans-serif" }}>Admin Portal</h1>
            <p className="text-xs font-bold uppercase tracking-widest mt-1" style={{ color: "#FFE500" }}>Restricted Access</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-black uppercase tracking-widest mb-1.5">Admin Email</label>
              <input
                id="admin-email"
                type="email"
                required
                autoComplete="email"
                placeholder="admin@snip.ly"
                value={form.email}
                onChange={e => setForm(f => ({ ...f, email: e.target.value }))}
                className="w-full px-4 py-3 text-sm font-medium input-brutal"
                style={{ border: "2.5px solid #0a0a0a" }}
              />
            </div>

            <div>
              <label className="block text-xs font-black uppercase tracking-widest mb-1.5">Password</label>
              <input
                id="admin-password"
                type="password"
                required
                autoComplete="current-password"
                placeholder="••••••••"
                value={form.password}
                onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                className="w-full px-4 py-3 text-sm font-medium input-brutal"
                style={{ border: "2.5px solid #0a0a0a" }}
              />
            </div>

            {error && (
              <div className="flex items-center gap-2 px-4 py-3" style={{ background: "#FF4040", border: "2.5px solid #0a0a0a", boxShadow: "3px 3px 0 #0a0a0a" }}>
                <svg className="w-4 h-4 text-white shrink-0" fill="none" stroke="currentColor" strokeWidth="2.5" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v2m0 4h.01M10.29 3.86L1.82 18a2 2 0 001.71 3h16.94a2 2 0 001.71-3L13.71 3.86a2 2 0 00-3.42 0z" />
                </svg>
                <p className="text-white text-xs font-bold">{error}</p>
              </div>
            )}

            <button
              id="admin-submit"
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
                  Verifying…
                </span>
              ) : "Access Dashboard →"}
            </button>
          </form>

          <p className="text-center mt-6 text-xs font-medium" style={{ color: "#888" }}>
            Regular user?{" "}
            <Link to="/login" className="font-black underline">Sign in here</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
