import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { apiGet, apiDelete } from "../lib/api";

const BASE_URL = "http://localhost:8000";
const DEVICE_COLORS = { mobile: "#1a6bff", desktop: "#00C853", bot: "#FF4040", unknown: "#888" };

function QrModal({ shortCode, fullUrl, onClose }) {
  const qrSrc = `https://api.qrserver.com/v1/create-qr-code/?size=300x300&data=${encodeURIComponent(fullUrl)}&bgcolor=FFFEF0&color=0a0a0a&format=svg`;
  async function downloadPng() {
    const pngUrl = `https://api.qrserver.com/v1/create-qr-code/?size=600x600&data=${encodeURIComponent(fullUrl)}&bgcolor=FFFEF0&color=0a0a0a&format=png`;
    const res = await fetch(pngUrl); const blob = await res.blob();
    const a = document.createElement("a"); a.href = URL.createObjectURL(blob);
    a.download = `snip-ly-${shortCode}.png`; a.click();
  }
  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative z-10 p-6 text-center w-72" style={{ background: "#FFFEF0", border: "2.5px solid #0a0a0a", boxShadow: "8px 8px 0 #0a0a0a" }}>
        <button onClick={onClose} className="absolute top-3 right-3 font-black text-lg">✕</button>
        <p className="text-xs font-black uppercase tracking-widest mb-3">QR — snip.ly/{shortCode}</p>
        <div className="w-44 h-44 mx-auto mb-4 flex items-center justify-center" style={{ background: "#FFFEF0", border: "2.5px solid #0a0a0a", boxShadow: "4px 4px 0 #0a0a0a" }}>
          <img src={qrSrc} alt="QR" className="w-40 h-40 object-contain" />
        </div>
        <button onClick={downloadPng} className="w-full py-2.5 text-sm font-black uppercase btn-brutal" style={{ background: "#FFE500", border: "2.5px solid #0a0a0a", boxShadow: "4px 4px 0 #0a0a0a" }}>Download PNG</button>
      </div>
    </div>
  );
}

function AnalyticsModal({ shortCode, token, onClose }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [err, setErr] = useState("");
  useEffect(() => {
    apiGet(`/analytics/${shortCode}`, token).then(setData).catch(e => setErr(e.message)).finally(() => setLoading(false));
  }, [shortCode, token]);

  return (
    <div className="fixed inset-0 z-[200] flex items-center justify-center px-4">
      <div className="absolute inset-0 bg-black/60" onClick={onClose} />
      <div className="relative z-10 w-full max-w-lg overflow-hidden" style={{ background: "#FFFEF0", border: "2.5px solid #0a0a0a", boxShadow: "8px 8px 0 #0a0a0a", maxHeight: "88vh" }}>
        <div className="flex items-center justify-between px-6 py-4" style={{ background: "#0a0a0a", borderBottom: "2.5px solid #0a0a0a" }}>
          <div>
            <p className="text-xs font-black uppercase tracking-widest" style={{ color: "#FFE500" }}>Analytics — Admin View</p>
            <p className="font-mono font-bold text-sm text-white">snip.ly/{shortCode}</p>
          </div>
          <button onClick={onClose} className="font-black text-lg text-white">✕</button>
        </div>
        <div className="overflow-y-auto" style={{ maxHeight: "calc(88vh - 64px)" }}>
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <svg className="animate-spin w-8 h-8" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
              </svg>
            </div>
          ) : err ? (
            <div className="px-6 py-8 text-center font-bold" style={{ color: "#FF4040" }}>{err}</div>
          ) : (
            <div className="p-6 space-y-6">
              <div className="text-center py-6" style={{ background: "#FFE500", border: "2.5px solid #0a0a0a", boxShadow: "4px 4px 0 #0a0a0a" }}>
                <div className="text-6xl font-black" style={{ fontFamily: "'Space Grotesk',sans-serif" }}>{data.total_clicks.toLocaleString()}</div>
                <div className="text-xs font-black uppercase tracking-widest mt-1">Total Clicks</div>
              </div>
              <div className="grid grid-cols-3 gap-3 text-xs">
                {[
                  { label: "Created", value: new Date(data.created_at).toLocaleDateString() },
                  { label: "Expires", value: data.expires_at ? new Date(data.expires_at).toLocaleDateString() : "Never" },
                  { label: "Type", value: data.is_custom ? "Custom" : "Auto" },
                ].map(m => (
                  <div key={m.label} className="text-center py-3 px-2" style={{ border: "2px solid #0a0a0a", boxShadow: "3px 3px 0 #0a0a0a" }}>
                    <p className="font-black uppercase tracking-widest text-[10px] mb-1" style={{ color: "#888" }}>{m.label}</p>
                    <p className="font-black">{m.value}</p>
                  </div>
                ))}
              </div>
              {Object.keys(data.device_breakdown).length > 0 && (
                <div>
                  <p className="text-xs font-black uppercase tracking-widest mb-3">Device Breakdown</p>
                  <div className="space-y-2">
                    {Object.entries(data.device_breakdown).map(([dev, cnt]) => {
                      const total = Object.values(data.device_breakdown).reduce((a, b) => a + b, 0);
                      const pct = Math.round((cnt / total) * 100);
                      const color = DEVICE_COLORS[dev] || "#888";
                      return (
                        <div key={dev} className="flex items-center gap-3">
                          <span className="text-[10px] font-black uppercase px-2 py-0.5 w-16 text-center" style={{ background: color, color: "#fff", border: "1.5px solid #0a0a0a" }}>{dev}</span>
                          <div className="flex-1 h-3" style={{ background: "#e5e0cc", border: "1.5px solid #0a0a0a" }}>
                            <div className="h-full" style={{ width: `${pct}%`, background: color }} />
                          </div>
                          <span className="text-xs font-bold w-16 text-right">{cnt} ({pct}%)</span>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              {data.top_referrers.length > 0 && (
                <div>
                  <p className="text-xs font-black uppercase tracking-widest mb-3">Top Referrers</p>
                  <div className="space-y-2">
                    {data.top_referrers.slice(0, 8).map(r => (
                      <div key={r.referrer} className="flex items-center justify-between px-3 py-2" style={{ border: "2px solid #0a0a0a", boxShadow: "2px 2px 0 #0a0a0a" }}>
                        <span className="text-xs font-medium truncate max-w-[220px]">{r.referrer}</span>
                        <span className="text-xs font-black ml-4 shrink-0">{r.count} clicks</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
              {data.recent_clicks.length > 0 && (
                <div>
                  <p className="text-xs font-black uppercase tracking-widest mb-3">Recent Activity</p>
                  <div className="space-y-1 max-h-52 overflow-y-auto">
                    {data.recent_clicks.slice(0, 25).map((ev, i) => {
                      const color = DEVICE_COLORS[ev.device_type] || "#888";
                      return (
                        <div key={i} className="flex items-center gap-3 text-xs py-1.5" style={{ borderBottom: "1px dashed #ccc" }}>
                          <span className="shrink-0 font-mono" style={{ color: "#888" }}>{new Date(ev.clicked_at).toLocaleString()}</span>
                          <span className="font-black px-1.5 py-0.5 text-[10px]" style={{ background: color, color: "#fff", border: "1px solid #0a0a0a" }}>{ev.device_type || "unknown"}</span>
                          {ev.referrer && <span className="truncate" style={{ color: "#555" }}>{ev.referrer}</span>}
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
              {data.total_clicks === 0 && <div className="text-center font-bold py-4" style={{ color: "#888" }}>No clicks recorded yet.</div>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function AdminDashboard() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [urls, setUrls] = useState([]);
  const [trending, setTrending] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [search, setSearch] = useState("");
  const [qrModal, setQrModal] = useState(null);
  const [analyticsModal, setAnalyticsModal] = useState(null);
  const [deleting, setDeleting] = useState(null);
  const [activeTab, setActiveTab] = useState("all");

  useEffect(() => {
    if (!user) { navigate("/admin/login"); return; }
    if (!user.is_admin) { navigate("/"); return; }
    async function fetchData() {
      try {
        const [urlsData, trendingData] = await Promise.all([apiGet("/admin/urls", user.token), apiGet("/admin/trending", user.token, { top: 10 })]);
        setUrls(urlsData.urls); setTrending(trendingData.urls);
      } catch (err) { setError(err.message); }
      finally { setLoading(false); }
    }
    fetchData();
  }, [user, navigate]);

  async function handleDelete(shortCode) {
    if (!confirm(`Delete snip.ly/${shortCode}?`)) return;
    setDeleting(shortCode);
    try {
      await apiDelete(`/urls/${shortCode}`, user.token);
      setUrls(prev => prev.filter(u => u.short_code !== shortCode));
      setTrending(prev => prev.filter(u => u.short_code !== shortCode));
    } catch (e) { alert(e.message); }
    finally { setDeleting(null); }
  }

  function isExpired(expiresAt) { return expiresAt && new Date(expiresAt) < new Date(); }

  if (loading) return (
    <div className="min-h-screen flex items-center justify-center" style={{ background: "#FFFEF0" }}>
      <svg className="animate-spin w-8 h-8" fill="none" viewBox="0 0 24 24">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" />
      </svg>
    </div>
  );

  const filtered = urls.filter(u => u.short_code.toLowerCase().includes(search.toLowerCase()) || u.original_url.toLowerCase().includes(search.toLowerCase()));
  const totalClicks = urls.reduce((a, u) => a + u.clicks, 0);
  const customCount = urls.filter(u => u.is_custom).length;
  const expiredCount = urls.filter(u => isExpired(u.expires_at)).length;
  const medals = ["🥇", "🥈", "🥉"];

  return (
    <div className="min-h-screen" style={{ background: "#F5F0DC" }}>
      {qrModal && <QrModal shortCode={qrModal.shortCode} fullUrl={qrModal.fullUrl} onClose={() => setQrModal(null)} />}
      {analyticsModal && <AnalyticsModal shortCode={analyticsModal} token={user.token} onClose={() => setAnalyticsModal(null)} />}

      {/* Nav */}
      <nav style={{ background: "#0a0a0a", borderBottom: "2.5px solid #0a0a0a", position: "sticky", top: 0, zIndex: 50 }}>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <Link to="/admin" className="flex items-center gap-2">
              <div className="w-8 h-8 flex items-center justify-center" style={{ background: "#FFE500", border: "2px solid #FFE500" }}>
                <svg viewBox="0 0 24 24" fill="none" stroke="#0a0a0a" strokeWidth="2.5" className="w-4 h-4">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <span className="font-black text-xl text-white" style={{ fontFamily: "'Space Grotesk',sans-serif" }}>snip<span style={{ color: "#FFE500" }}>.ly</span> <span className="font-medium text-sm" style={{ color: "#888" }}>Admin</span></span>
            </Link>
            <div className="flex items-center gap-3">
              <span className="text-sm font-bold hidden sm:block" style={{ color: "#aaa" }}>Logged in as {user?.username}</span>
              <button onClick={() => { logout(); navigate("/admin/login"); }} className="text-sm font-black px-4 py-2 btn-brutal" style={{ background: "#FFE500", border: "2px solid #FFE500", boxShadow: "2px 2px 0 #FFE500" }}>Sign out</button>
            </div>
          </div>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="mb-8">
          <h1 className="text-3xl font-black mb-1" style={{ fontFamily: "'Space Grotesk',sans-serif" }}>Admin Dashboard</h1>
          <p className="font-medium" style={{ color: "#555" }}>Manage all URLs, view analytics, and monitor trending links.</p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
          {[
            { label: "Total URLs", value: urls.length, bg: "#FFE500" },
            { label: "Total Clicks", value: totalClicks.toLocaleString(), bg: "#0a0a0a", color: "#FFE500" },
            { label: "Custom Aliases", value: customCount, bg: "#1a6bff", color: "#fff" },
            { label: "Expired Links", value: expiredCount, bg: "#FF4040", color: "#fff" },
          ].map(s => (
            <div key={s.label} className="px-5 py-4" style={{ background: s.bg, border: "2.5px solid #0a0a0a", boxShadow: "4px 4px 0 #0a0a0a", color: s.color || "#0a0a0a" }}>
              <div className="text-3xl font-black mb-1" style={{ fontFamily: "'Space Grotesk',sans-serif" }}>{s.value}</div>
              <div className="text-xs font-black uppercase tracking-widest opacity-80">{s.label}</div>
            </div>
          ))}
        </div>

        {error && <div className="mb-6 px-4 py-3 font-bold text-sm" style={{ background: "#FF4040", color: "#fff", border: "2px solid #0a0a0a", boxShadow: "3px 3px 0 #0a0a0a" }}>{error}</div>}

        {/* Tabs */}
        <div className="flex gap-2 mb-5 flex-wrap">
          {["all", "trending"].map(tab => (
            <button key={tab} onClick={() => setActiveTab(tab)}
              className="px-4 py-2 text-sm font-black uppercase tracking-wider btn-brutal"
              style={{ background: activeTab === tab ? "#FFE500" : "#FFFEF0", border: "2.5px solid #0a0a0a", boxShadow: activeTab === tab ? "4px 4px 0 #0a0a0a" : "2px 2px 0 #0a0a0a" }}>
              {tab === "all" ? "All URLs" : "🔥 Trending"}
            </button>
          ))}
          {activeTab === "all" && (
            <input type="text" value={search} onChange={e => setSearch(e.target.value)} placeholder="Search URLs..."
              className="ml-auto text-sm font-medium px-4 py-2 input-brutal" style={{ border: "2.5px solid #0a0a0a", boxShadow: "2px 2px 0 #0a0a0a", width: 220 }} />
          )}
        </div>

        {/* Trending tab */}
        {activeTab === "trending" && (
          <div style={{ border: "2.5px solid #0a0a0a", boxShadow: "5px 5px 0 #0a0a0a", background: "#FFFEF0" }}>
            <div className="px-6 py-4" style={{ background: "#0a0a0a", borderBottom: "2.5px solid #0a0a0a" }}>
              <h2 className="font-black text-white">Top Trending (24h Redis data)</h2>
            </div>
            <div>
              {trending.length === 0 ? (
                <div className="px-6 py-10 text-center font-medium" style={{ color: "#888" }}>No trending data yet.</div>
              ) : trending.map((t, i) => (
                <div key={t.short_code} className="flex items-center gap-4 px-6 py-4" style={{ borderBottom: "2px solid #e5e0cc" }}>
                  <span className="text-2xl w-8 text-center shrink-0">{medals[i] || `${i + 1}.`}</span>
                  <div className="flex-1 min-w-0">
                    <a href={`${BASE_URL}/${t.short_code}`} target="_blank" rel="noreferrer" className="font-mono font-bold hover:underline" style={{ color: "#FF4040" }}>{t.short_code}</a>
                    <p className="text-xs font-medium truncate mt-0.5" style={{ color: "#888" }}>{t.original_url}</p>
                  </div>
                  <div className="text-right">
                    <div className="font-black">{t.clicks.toLocaleString()}</div>
                    <div className="text-xs font-medium" style={{ color: "#888" }}>clicks</div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* All URLs tab */}
        {activeTab === "all" && (
          <div style={{ border: "2.5px solid #0a0a0a", boxShadow: "5px 5px 0 #0a0a0a", background: "#FFFEF0" }}>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm whitespace-nowrap">
                <thead style={{ background: "#0a0a0a", borderBottom: "2.5px solid #0a0a0a" }}>
                  <tr>
                    {["Short Code", "Original URL", "Clicks", "Owner", "Created", "Expires", "Actions"].map(h => (
                      <th key={h} className="px-6 py-4 text-xs font-black uppercase tracking-widest" style={{ color: "#FFE500" }}>{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {filtered.length === 0 ? (
                    <tr><td colSpan="7" className="px-6 py-8 text-center font-medium" style={{ color: "#888" }}>No URLs found.</td></tr>
                  ) : filtered.map((url, idx) => {
                    const expired = isExpired(url.expires_at);
                    return (
                      <tr key={url.short_code} style={{ borderBottom: "2px solid #e5e0cc", opacity: expired ? 0.55 : 1, background: idx % 2 === 0 ? "#FFFEF0" : "#F5F0DC" }}>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2 flex-wrap">
                            <a href={`${BASE_URL}/${url.short_code}`} target="_blank" rel="noreferrer" className="font-mono font-bold hover:underline" style={{ color: "#FF4040" }}>snip.ly/{url.short_code}</a>
                            {url.is_custom && <span className="text-[10px] font-black px-1.5 py-0.5" style={{ background: "#1a6bff", color: "#fff", border: "1.5px solid #0a0a0a" }}>Custom</span>}
                            {expired && <span className="text-[10px] font-black px-1.5 py-0.5" style={{ background: "#FF4040", color: "#fff", border: "1.5px solid #0a0a0a" }}>Expired</span>}
                          </div>
                        </td>
                        <td className="px-6 py-4 max-w-xs truncate font-medium" style={{ color: "#555" }} title={url.original_url}>{url.original_url}</td>
                        <td className="px-6 py-4">
                          <span className="font-black px-2.5 py-1 text-xs" style={{ background: "#FFE500", border: "2px solid #0a0a0a", boxShadow: "2px 2px 0 #0a0a0a" }}>{url.clicks}</span>
                        </td>
                        <td className="px-6 py-4 text-xs font-medium" style={{ color: "#888" }}>{url.owner_id ? `#${url.owner_id}` : "Anonymous"}</td>
                        <td className="px-6 py-4 font-medium" style={{ color: "#888" }}>{new Date(url.created_at).toLocaleDateString()}</td>
                        <td className="px-6 py-4 font-medium">
                          {url.expires_at ? <span style={{ color: expired ? "#FF4040" : "#888" }}>{new Date(url.expires_at).toLocaleDateString()}</span> : <span style={{ color: "#ccc" }}>Never</span>}
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-2">
                            <button onClick={() => setAnalyticsModal(url.short_code)} title="Analytics" className="p-1.5 hover:bg-yellow-100 transition-colors" style={{ border: "2px solid #0a0a0a" }}>
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><path d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" strokeLinecap="round" strokeLinejoin="round" /></svg>
                            </button>
                            <button onClick={() => setQrModal({ shortCode: url.short_code, fullUrl: `${BASE_URL}/${url.short_code}` })} title="QR" className="p-1.5 hover:bg-yellow-100 transition-colors" style={{ border: "2px solid #0a0a0a" }}>
                              <svg className="w-4 h-4" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><path d="M14 14h.01M17 14h.01M20 14h.01M14 17h.01M17 17h.01M20 17h.01M14 20h.01M17 20h.01M20 20h.01" strokeLinecap="round" /></svg>
                            </button>
                            <button onClick={() => handleDelete(url.short_code)} disabled={deleting === url.short_code} title="Delete" className="p-1.5 hover:bg-red-100 transition-colors" style={{ border: "2px solid #0a0a0a" }}>
                              {deleting === url.short_code ? (
                                <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24"><circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" /><path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z" /></svg>
                              ) : (
                                <svg className="w-4 h-4" fill="none" stroke="#FF4040" strokeWidth="2" viewBox="0 0 24 24"><path d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" strokeLinecap="round" strokeLinejoin="round" /></svg>
                              )}
                            </button>
                          </div>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
