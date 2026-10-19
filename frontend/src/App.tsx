import React, { useEffect, useMemo, useState } from 'react';
import { fetchServices } from './api';
import { Service } from './types';
import Card from './components/Card';
import { Search, Refresh, Grid, List, Sun, Moon, Plug } from './icons';

type View = 'grid' | 'list';
type Theme = 'dark' | 'light';

export default function App() {
  const [svcs, setSvcs] = useState<Service[] | null>(null);
  const [host, setHost] = useState('');
  const [err, setErr] = useState('');
  const [busy, setBusy] = useState(false);
  const [q, setQ] = useState('');
  const [view, setView] = useState<View>(() => (localStorage.getItem('view') as View) || 'grid');
  const [theme, setTheme] = useState<Theme>(() => (localStorage.getItem('theme') as Theme) || 'dark');

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem('theme', theme);
  }, [theme]);
  useEffect(() => localStorage.setItem('view', view), [view]);

  const load = (refresh = false) => {
    setBusy(true);
    fetchServices(refresh)
      .then((d) => { setSvcs(d.services); setHost(d.host); setErr(''); })
      .catch((e) => setErr(e.message))
      .finally(() => setBusy(false));
  };
  useEffect(() => load(), []);

  const shown = useMemo(() => {
    const k = q.trim().toLowerCase();
    if (!k) return svcs ?? [];
    return (svcs ?? []).filter(
      (s) => s.name.toLowerCase().includes(k) || s.image.toLowerCase().includes(k)
        || s.links.some((l) => String(l.port).includes(k)),
    );
  }, [svcs, q]);

  return (
    <div className="wrap">
      <header className="top">
        <div className="brand">
          <h1>DockNav</h1>
          <span className="sub">
            {err ? '连接失败' : svcs === null ? '扫描中…'
              : <><span className="count">{shown.length}</span> 个服务 · {host}</>}
          </span>
        </div>
        <div className="tools">
          <label className="search">
            <Search />
            <input name="q" value={q} onChange={(e) => setQ(e.target.value)} placeholder="搜索服务 / 端口" />
          </label>
          <div className="seg">
            <button className={`seg-btn${view === 'grid' ? ' active' : ''}`} onClick={() => setView('grid')}
                    aria-label="网格视图"><Grid /></button>
            <button className={`seg-btn${view === 'list' ? ' active' : ''}`} onClick={() => setView('list')}
                    aria-label="列表视图"><List /></button>
          </div>
          <button className="btn icon-only" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
                  aria-label="切换主题">{theme === 'dark' ? <Sun /> : <Moon />}</button>
          <button className="btn icon-only" onClick={() => load(true)} disabled={busy} aria-label="重新扫描">
            <span className={busy ? 'spin' : ''} style={{ display: 'grid' }}><Refresh /></span>
          </button>
        </div>
      </header>

      {err ? (
        <div className="note err">
          <div className="ico-big"><Plug /></div>
          <h3>拿不到容器列表</h3>
          <p>{err}<br />挂载 <code>/var/run/docker.sock</code>，并把 <code>HOST_IP</code> 设成宿主机地址。</p>
        </div>
      ) : svcs === null ? (
        <div className="grid">{Array.from({ length: 8 }, (_, i) => <div className="skel" key={i} />)}</div>
      ) : shown.length === 0 ? (
        <div className="note">
          <div className="ico-big"><Plug /></div>
          <h3>{q ? '没有匹配的服务' : '没发现 HTTP 服务'}</h3>
          <p>{q ? '换个关键词试试。' : '只有映射到宿主机且能应答 HTTP 的端口才会出现在这里。'}</p>
        </div>
      ) : (
        <div className={`grid${view === 'list' ? ' list' : ''}`}>
          {shown.map((s, i) => <Card key={s.name} svc={s} index={i} />)}
        </div>
      )}
    </div>
  );
}
