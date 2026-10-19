import React, { useState } from 'react';
import { Service } from '../types';
import { External } from '../icons';

/** One card per container; every discovered web port gets its own clickable tag. */
export default function Card({ svc, index }: { svc: Service; index: number }) {
  const [broken, setBroken] = useState(false);
  const primary = svc.links[0] ?? { port: svc.port, scheme: svc.scheme, href: svc.href, online: svc.online };

  return (
    <div className="card" style={{ ['--i' as any]: index }} title={svc.image}>
      <a className="ico" href={primary.href} target="_blank" rel="noreferrer" tabIndex={-1} aria-hidden="true">
        {broken
          ? <span className="letter">{svc.name[0].toUpperCase()}</span>
          : <img src={svc.icon} alt="" loading="lazy" onError={() => setBroken(true)} />}
      </a>
      <div className="body">
        <div className="line">
          <span className={`dot${svc.online ? ' up' : ''}`}
                title={svc.online ? '探测到 HTTP 响应' : '未响应，端口按容器端口推断'} />
          <a className="name" href={primary.href} target="_blank" rel="noreferrer" title={primary.href}>
            {svc.name}
          </a>
        </div>
        <div className="tags">
          {svc.links.map((l) => (
            <a className={`tag${l.online ? '' : ' guess'}`} href={l.href} target="_blank" rel="noreferrer"
               key={l.port} title={l.online ? l.href : `${l.href}（未响应，按容器端口推断）`}>
              {l.scheme}:{l.port}
            </a>
          ))}
        </div>
      </div>
      <a className="go" href={primary.href} target="_blank" rel="noreferrer" aria-label={`打开 ${svc.name}`}>
        <External />
      </a>
    </div>
  );
}
