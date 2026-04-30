import { useState, useEffect } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiPost, apiGet } from "../lib/api";

const FEATURES = [
  { title: "Base62 Shortening", desc: "Lightning-fast encoding into compact short links.", bg: "#FFE500" },
  { title: "QR Code Generator", desc: "High-res QR codes for every link. Download instantly.", bg: "#FF4040", color: "#fff" },
  { title: "Custom Aliases", desc: "Brand your links with memorable custom slugs.", bg: "#0a0a0a", color: "#FFE500" },
  { title: "Real-Time Analytics", desc: "Live clicks, device breakdown, referrer tracking.", bg: "#1a6bff", color: "#fff" },
  { title: "Link Expiration", desc: "Set time-based expiry. Fully automated.", bg: "#00C853", color: "#fff" },
  { title: "Rate Limiting", desc: "Redis-backed protection against abuse.", bg: "#F5F0DC" },
];

const STATS = [
  { value: "2.4B+", label: "Links Shortened" },
  { value: "180+", label: "Countries Reached" },
  { value: "99.9%", label: "Uptime SLA" },
  { value: "<50ms", label: "Avg Redirect" },
];

const NAV_LINKS = [
  { label: "Features",    href: "#features" },
  { label: "Trending",    href: "#trending" },
  { label: "Get Started", href: "#cta" },
];

function scrollTo(id) {
  const el = document.getElementById(id.replace("#", ""));
  if (el) el.scrollIntoView({ behavior: "smooth", block: "start" });
}

function Navbar() {
  const [open, setOpen] = useState(false);
  const { user, logout } = useAuth();
  return (
    <nav style={{ background: "#FFFEF0", borderBottom: "2.5px solid #0a0a0a", position: "sticky", top: 0, zIndex: 50 }}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <button onClick={() => scrollTo("#hero")} className="flex items-center gap-2 bg-transparent border-0 cursor-pointer p-0">
            <div className="w-8 h-8 flex items-center justify-center" style={{ background: "#FFE500", border: "2.5px solid #0a0a0a", boxShadow: "2px 2px 0 #0a0a0a" }}>
              <svg viewBox="0 0 24 24" fill="none" stroke="#0a0a0a" strokeWidth="2.5" className="w-4 h-4">
                <path d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101" strokeLinecap="round" />
                <path d="M10.172 13.828a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" strokeLinecap="round" />
              </svg>
            </div>
            <span className="font-black text-xl" style={{ fontFamily: "'Space Grotesk',sans-serif" }}>snip<span style={{ color: "#FF4040" }}>.ly</span></span>
          </button>

          {/* Desktop section links */}
          <div className="hidden md:flex items-center gap-6">
            {NAV_LINKS.map(l => (
              <a key={l.label} href={l.href}
                onClick={e => { e.preventDefault(); scrollTo(l.href); }}
                className="text-sm font-semibold hover:underline" style={{ color: "#0a0a0a" }}>
                {l.label}
              </a>
            ))}
          </div>

          {/* Desktop auth */}
          <div className="hidden md:flex items-center gap-2">
            {user ? (
              <>
                <span className="text-sm font-bold mr-1">Hi, {user.username}</span>
                {!user.is_admin && <Link to="/dashboard" className="text-sm font-black px-3 py-1.5" style={{ border: "2px solid #0a0a0a", boxShadow: "2px 2px 0 #0a0a0a" }}>Dashboard</Link>}
                {user.is_admin && <Link to="/admin" className="text-sm font-black px-3 py-1.5" style={{ background: "#FFE500", border: "2px solid #0a0a0a", boxShadow: "2px 2px 0 #0a0a0a" }}>Admin Portal</Link>}
                <button onClick={logout} className="text-sm font-semibold px-3 py-1.5 hover:underline">Sign out</button>
              </>
            ) : (
              <>
                <Link to="/login" className="text-sm font-bold px-3 py-1.5" style={{ border: "2px solid #0a0a0a", boxShadow: "2px 2px 0 #0a0a0a" }}>Sign in</Link>
                <Link to="/register" className="text-sm font-black px-4 py-1.5" style={{ background: "#FFE500", border: "2.5px solid #0a0a0a", boxShadow: "3px 3px 0 #0a0a0a" }}>Get started →</Link>
              </>
            )}
          </div>

          {/* Hamburger */}
          <button className="md:hidden font-black text-xl" onClick={() => setOpen(!open)}>{open ? "✕" : "☰"}</button>
        </div>

        {/* Mobile menu */}
        {open && (
          <div className="md:hidden pb-4" style={{ borderTop: "2px solid #0a0a0a" }}>
            {/* Section links */}
            <div className="pt-3 space-y-1">
              {NAV_LINKS.map(l => (
                <a key={l.label} href={l.href}
                  onClick={e => { e.preventDefault(); scrollTo(l.href); setOpen(false); }}
                  className="block px-4 py-2.5 text-sm font-semibold hover:underline">{l.label}</a>
              ))}
            </div>
            {/* Auth section */}
            <div className="mt-3 pt-3 space-y-2 px-4" style={{ borderTop: "2px dashed #ccc" }}>
              {user ? (
                <>
                  <p className="text-sm font-bold py-1">Hi, {user.username}</p>
                  {!user.is_admin && <Link to="/dashboard" onClick={() => setOpen(false)} className="block text-center py-2.5 text-sm font-black" style={{ border: "2px solid #0a0a0a", boxShadow: "2px 2px 0 #0a0a0a" }}>Dashboard</Link>}
                  {user.is_admin && <Link to="/admin" onClick={() => setOpen(false)} className="block text-center py-2.5 text-sm font-black" style={{ background: "#FFE500", border: "2px solid #0a0a0a", boxShadow: "2px 2px 0 #0a0a0a" }}>Admin Portal</Link>}
                  <button onClick={() => { logout(); setOpen(false); }} className="w-full text-center py-2.5 text-sm font-semibold hover:underline">Sign out</button>
                </>
              ) : (
                <>
                  <Link to="/login" onClick={() => setOpen(false)} className="block text-center py-2.5 text-sm font-bold" style={{ border: "2px solid #0a0a0a", boxShadow: "2px 2px 0 #0a0a0a" }}>Sign in</Link>
                  <Link to="/register" onClick={() => setOpen(false)} className="block text-center py-2.5 text-sm font-black" style={{ background: "#FFE500", border: "2.5px solid #0a0a0a", boxShadow: "3px 3px 0 #0a0a0a" }}>Get started →</Link>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </nav>
  );
}

function AuthModal({ onClose }) {
  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative z-10 w-full max-w-sm p-8" style={{ background: "#FFFEF0", border: "2.5px solid #0a0a0a", boxShadow: "8px 8px 0 #0a0a0a" }}>
        <button onClick={onClose} className="absolute top-4 right-4 font-black text-lg">✕</button>
        <div className="w-12 h-12 flex items-center justify-center mb-4 mx-auto" style={{ background: "#FFE500", border: "2.5px solid #0a0a0a", boxShadow: "3px 3px 0 #0a0a0a" }}>
          <svg className="w-6 h-6" viewBox="0 0 24 24" fill="none" stroke="#0a0a0a" strokeWidth="2.5">
            <path d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
        <h3 className="text-xl font-black text-center mb-1" style={{ fontFamily: "'Space Grotesk',sans-serif" }}>Sign in to shorten</h3>
        <p className="text-sm text-center mb-6" style={{ color: "#555" }}>Free account required to shorten URLs and track analytics.</p>
        <div className="flex flex-col gap-3">
          <Link to="/register" className="w-full text-center font-black py-3 text-sm btn-brutal" style={{ background: "#FFE500", border: "2.5px solid #0a0a0a", boxShadow: "4px 4px 0 #0a0a0a" }}>Create free account →</Link>
          <Link to="/login" className="w-full text-center font-bold py-3 text-sm btn-brutal" style={{ border: "2.5px solid #0a0a0a", boxShadow: "4px 4px 0 #0a0a0a" }}>Sign in</Link>
        </div>
      </div>
    </div>
  );
}

function HeroSection() {
  const [url, setUrl] = useState("");
  const [alias, setAlias] = useState("");
  const [expiryHours, setExpiryHours] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState("");
  const [showAuthModal, setShowAuthModal] = useState(false);
  const { user } = useAuth();
  const isLoggedIn = !!user;

  function isValidUrl(str) { try { new URL(str); return true; } catch { return false; } }

  async function handleShorten() {
    if (!url.trim()) { setError("Please enter a URL."); return; }
    if (!isValidUrl(url)) { setError("Enter a valid URL (include https://)."); return; }
    setError("");
    if (!isLoggedIn) { setShowAuthModal(true); return; }
    setLoading(true);
    try {
      const body = { original_url: url };
      if (alias.trim()) body.custom_alias = alias.trim();
      if (expiryHours) body.expires_in_hours = parseInt(expiryHours);
      const data = await apiPost("/shorten", body, user.token);
      const urlObj = new URL(data.short_url);
      setResult({ shortened: urlObj.host + urlObj.pathname, fullUrl: data.short_url, qrSrc: data.qr_url, isCustom: data.is_custom, expiresAt: data.expires_at, shortCode: data.short_code });
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }

  function handleCopy() {
    if (!result) return;
    navigator.clipboard.writeText(result.fullUrl);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  async function handleDownloadQR() {
    if (!result) return;
    const pngUrl = result.qrSrc.replace("format=svg", "format=png").replace("size=300x300", "size=600x600");
    const res = await fetch(pngUrl);
    const blob = await res.blob();
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = `snip-ly-${result.shortCode}.png`;
    a.click();
  }

  return (
    <>
      {showAuthModal && <AuthModal onClose={() => setShowAuthModal(false)} />}
      <section className="px-4 pt-16 pb-20" style={{ background: "#FFFEF0" }}>
        <div className="max-w-4xl mx-auto text-center">
          <div className="inline-block px-4 py-1.5 mb-6 text-xs font-black uppercase tracking-widest" style={{ background: "#FFE500", border: "2px solid #0a0a0a", boxShadow: "3px 3px 0 #0a0a0a" }}>
            🔗 URL Shortener &amp; Analytics
          </div>
          <h1 className="text-5xl sm:text-6xl md:text-7xl font-black leading-tight mb-6" style={{ fontFamily: "'Space Grotesk',sans-serif" }}>
            BITLY<br />
            <span style={{ WebkitTextStroke: "3px #0a0a0a", color: "#FFE500" }}>Big impact.</span>
          </h1>
          <p className="text-lg font-medium max-w-xl mx-auto mb-10" style={{ color: "#444" }}>
            Transform any URL into a powerful, tracable,short link with QR codes, custom aliases, and real-time analytics.
          </p>

          {!isLoggedIn && (
            <div className="inline-flex items-center gap-2 mb-6 px-4 py-2 text-sm font-bold" style={{ background: "#F5F0DC", border: "2px solid #0a0a0a", boxShadow: "3px 3px 0 #0a0a0a" }}>
              🔒 <Link to="/login" className="font-black underline">Sign in</Link> or <Link to="/register" className="font-black underline">create a free account</Link> to shorten URLs
            </div>
          )}

          {/* Input box */}
          <div className="max-w-2xl mx-auto p-3" style={{ background: "#FFFEF0", border: "2.5px solid #0a0a0a", boxShadow: "6px 6px 0 #0a0a0a" }}>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                id="url-input"
                type="url"
                value={url}
                onChange={e => { setUrl(e.target.value); setError(""); setResult(null); }}
                onKeyDown={e => e.key === "Enter" && handleShorten()}
                placeholder="Paste your long URL here..."
                className="flex-1 px-4 py-3 text-sm font-medium input-brutal"
                style={{ border: "2.5px solid #0a0a0a" }}
              />
              <button
                id="shorten-btn"
                onClick={handleShorten}
                disabled={loading}
                className="px-6 py-3 text-sm font-black uppercase tracking-wider btn-brutal whitespace-nowrap"
                style={{ background: "#FFE500", border: "2.5px solid #0a0a0a", boxShadow: "4px 4px 0 #0a0a0a" }}
              >
                {loading ? (
                  <svg className="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
                  </svg>
                ) : "Shorten →"}
              </button>
            </div>

            {isLoggedIn && (
              <div className="mt-2 px-1">
                <button onClick={() => setShowAdvanced(!showAdvanced)} className="text-xs font-bold uppercase tracking-wider flex items-center gap-1" style={{ color: "#888" }}>
                  <span className={`inline-block transition-transform ${showAdvanced ? "rotate-90" : ""}`}>▶</span>
                  Advanced options
                </button>
                {showAdvanced && (
                  <div className="mt-3 grid grid-cols-1 sm:grid-cols-2 gap-2">
                    <div>
                      <label className="text-xs font-black uppercase tracking-widest mb-1 block">Custom alias</label>
                      <input id="alias-input" type="text" value={alias} onChange={e => setAlias(e.target.value)} placeholder="e.g. my-brand"
                        className="w-full px-3 py-2 text-xs input-brutal" style={{ border: "2px solid #0a0a0a" }} />
                      <p className="text-[10px] mt-1" style={{ color: "#888" }}>3–30 chars: letters, digits, _ or -</p>
                    </div>
                    <div>
                      <label className="text-xs font-black uppercase tracking-widest mb-1 block">Expires in</label>
                      <select id="expiry-select" value={expiryHours} onChange={e => setExpiryHours(e.target.value)}
                        className="w-full px-3 py-2 text-xs input-brutal" style={{ border: "2px solid #0a0a0a" }}>
                        <option value="">Never</option>
                        <option value="1">1 hour</option>
                        <option value="6">6 hours</option>
                        <option value="24">24 hours</option>
                        <option value="72">3 days</option>
                        <option value="168">7 days</option>
                        <option value="720">30 days</option>
                      </select>
                    </div>
                  </div>
                )}
              </div>
            )}

            {error && <p className="text-xs font-bold mt-2 px-1" style={{ color: "#FF4040" }}>⚠ {error}</p>}

            {result && (
              <div className="mt-3 grid grid-cols-1 sm:grid-cols-[1fr_auto] gap-3">
                <div className="p-4 flex flex-col gap-3" style={{ background: "#F5F0DC", border: "2px solid #0a0a0a", boxShadow: "3px 3px 0 #0a0a0a" }}>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs font-black uppercase">Your short link</span>
                    {result.isCustom && <span className="tag-brutal text-[10px]" style={{ background: "#1a6bff", color: "#fff", borderColor: "#0a0a0a" }}>Custom</span>}
                    {result.expiresAt && <span className="tag-brutal text-[10px]" style={{ background: "#FFE500" }}>Expires {new Date(result.expiresAt).toLocaleDateString()}</span>}
                  </div>
                  <a href={result.fullUrl} target="_blank" rel="noopener noreferrer" className="font-mono font-bold text-sm hover:underline" style={{ color: "#FF4040" }}>{result.shortened}</a>
                  <button onClick={handleCopy} className="self-start text-xs font-black uppercase px-3 py-1.5 btn-brutal"
                    style={{ background: copied ? "#00C853" : "#FFE500", border: "2px solid #0a0a0a", boxShadow: "2px 2px 0 #0a0a0a", color: copied ? "#fff" : "#0a0a0a" }}>
                    {copied ? "✓ Copied!" : "Copy link"}
                  </button>
                </div>
                <div className="p-4 flex flex-col items-center gap-2" style={{ background: "#F5F0DC", border: "2px solid #0a0a0a", boxShadow: "3px 3px 0 #0a0a0a" }}>
                  <span className="text-xs font-black uppercase">QR code</span>
                  <div className="w-28 h-28 flex items-center justify-center" style={{ background: "#0a0a0f", border: "2px solid #0a0a0a" }}>
                    <img src={result.qrSrc} alt="QR Code" className="w-24 h-24 object-contain" />
                  </div>
                  <button onClick={handleDownloadQR} className="text-xs font-black uppercase px-3 py-1 btn-brutal" style={{ border: "2px solid #0a0a0a", boxShadow: "2px 2px 0 #0a0a0a" }}>
                    Download PNG
                  </button>
                </div>
              </div>
            )}
          </div>
          <p className="text-xs font-medium mt-4" style={{ color: "#888" }}>
            {!isLoggedIn ? "Sign in required. Free forever for personal use." : "Ready to shorten! Manage your links in the dashboard."}
          </p>
        </div>
      </section>
    </>
  );
}

function StatsSection() {
  return (
    <section id="stats" style={{ background: "#0a0a0a", borderTop: "2.5px solid #0a0a0a", borderBottom: "2.5px solid #0a0a0a" }} className="py-12 px-4">
      <div className="max-w-5xl mx-auto grid grid-cols-2 md:grid-cols-4 gap-0">
        {STATS.map((s, i) => (
          <div key={s.label} className="text-center py-6 px-4" style={{ borderRight: i < 3 ? "2px solid #333" : "none" }}>
            <div className="text-4xl font-black mb-1" style={{ fontFamily: "'Space Grotesk',sans-serif", color: "#FFE500" }}>{s.value}</div>
            <div className="text-xs font-bold uppercase tracking-widest" style={{ color: "#888" }}>{s.label}</div>
          </div>
        ))}
      </div>
    </section>
  );
}

function FeaturesSection() {
  return (
    <section id="features" className="py-24 px-4" style={{ background: "#FFFEF0", borderBottom: "2.5px solid #0a0a0a" }}>
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-16">
          <span className="text-xs font-black uppercase tracking-widest px-3 py-1" style={{ background: "#FFE500", border: "2px solid #0a0a0a", boxShadow: "3px 3px 0 #0a0a0a" }}>Everything you need</span>
          <h2 className="text-4xl sm:text-5xl font-black mt-6 mb-3" style={{ fontFamily: "'Space Grotesk',sans-serif" }}>Built for builders</h2>
          <p className="font-medium max-w-xl mx-auto" style={{ color: "#555" }}>From one-click shortening to enterprise link management — all in one place.</p>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {FEATURES.map(f => (
            <div key={f.title} className="p-6 transition-transform hover:-translate-y-1 cursor-pointer" style={{ background: f.bg || "#FFFEF0", border: "2.5px solid #0a0a0a", boxShadow: "5px 5px 0 #0a0a0a", color: f.color || "#0a0a0a" }}>
              <h3 className="font-black text-lg mb-2" style={{ fontFamily: "'Space Grotesk',sans-serif" }}>{f.title}</h3>
              <p className="text-sm font-medium" style={{ opacity: 0.8 }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function TrendingSection() {
  const [trending, setTrending] = useState([]);
  const medals = ["🥇", "🥈", "🥉"];
  useEffect(() => {
    apiGet("/trending/public").then(d => setTrending(d.trending || [])).catch(() => {});
  }, []);

  return (
    <section id="trending" className="py-24 px-4" style={{ background: "#F5F0DC", borderBottom: "2.5px solid #0a0a0a" }}>
      <div className="max-w-3xl mx-auto">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-10 gap-4">
          <div>
            <span className="text-xs font-black uppercase tracking-widest px-3 py-1" style={{ background: "#FF4040", color: "#fff", border: "2px solid #0a0a0a", boxShadow: "3px 3px 0 #0a0a0a" }}>Live Leaderboard</span>
            <h2 className="text-4xl font-black mt-4" style={{ fontFamily: "'Space Grotesk',sans-serif" }}>Trending right now</h2>
          </div>
          <Link to="/dashboard" className="text-sm font-black uppercase underline">View dashboard →</Link>
        </div>
        <div className="space-y-3">
          {trending.length === 0 ? (
            <div className="text-center py-12 font-medium" style={{ color: "#888" }}>No trending data yet — start shortening!</div>
          ) : trending.map((t, i) => (
            <div key={t.short_code} className="flex items-center gap-4 px-5 py-4" style={{ background: "#FFFEF0", border: "2.5px solid #0a0a0a", boxShadow: "4px 4px 0 #0a0a0a" }}>
              <span className="text-2xl w-8 text-center shrink-0">{medals[i] || `${i + 1}.`}</span>
              <div className="flex-1 min-w-0">
                <div className="font-mono font-bold text-sm truncate">snip.ly/{t.short_code}</div>
              </div>
              <div className="text-right shrink-0">
                <div className="font-black text-sm">{t.clicks.toLocaleString()}</div>
                <div className="text-xs font-medium" style={{ color: "#888" }}>clicks</div>
              </div>
              <div className="w-24 h-3 hidden sm:block" style={{ background: "#e5e0cc", border: "1.5px solid #0a0a0a" }}>
                <div className="h-full" style={{ width: `${(t.clicks / (trending[0]?.clicks || 1)) * 100}%`, background: "#FFE500", borderRight: "1.5px solid #0a0a0a" }} />
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

function CTASection() {
  return (
    <section id="cta" className="py-24 px-4" style={{ background: "#0a0a0a" }}>
      <div className="max-w-2xl mx-auto text-center">
        <h2 className="text-4xl sm:text-5xl font-black mb-4" style={{ fontFamily: "'Space Grotesk',sans-serif", color: "#FFE500" }}>Start shortening today</h2>
        <p className="font-medium mb-10" style={{ color: "#aaa" }}>Free forever for personal use. No credit card needed.</p>
        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link to="/register" className="font-black text-sm px-8 py-4 btn-brutal uppercase tracking-wider" style={{ background: "#FFE500", border: "2.5px solid #FFE500", boxShadow: "5px 5px 0 #FFE500", color: "#0a0a0a" }}>
            Create free account →
          </Link>
          <Link to="/login" className="font-black text-sm px-8 py-4 btn-brutal uppercase tracking-wider" style={{ background: "transparent", border: "2.5px solid #555", boxShadow: "5px 5px 0 #333", color: "#fff" }}>
            Sign in
          </Link>
        </div>
      </div>
    </section>
  );
}

function Footer() {
  return (
    <footer className="py-10 px-4" style={{ background: "#FFFEF0", borderTop: "2.5px solid #0a0a0a" }}>
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        <span className="font-black text-lg" style={{ fontFamily: "'Space Grotesk',sans-serif" }}>snip<span style={{ color: "#FF4040" }}>.ly</span></span>
        <div className="flex gap-6">
          {NAV_LINKS.map(l => (
            <a key={l.label} href={l.href}
              onClick={e => { e.preventDefault(); scrollTo(l.href); }}
              className="text-xs font-bold uppercase tracking-wider hover:underline" style={{ color: "#888" }}>
              {l.label}
            </a>
          ))}
        </div>
        <p className="text-xs font-medium" style={{ color: "#aaa" }}>© 2026 snip.ly</p>
      </div>
    </footer>
  );
}

export default function Home() {
  return (
    <div className="overflow-x-hidden" style={{ background: "#FFFEF0" }}>
      <Navbar />
      <HeroSection />
      <StatsSection />
      <FeaturesSection />
      <TrendingSection />
      <CTASection />
      <Footer />
    </div>
  );
}