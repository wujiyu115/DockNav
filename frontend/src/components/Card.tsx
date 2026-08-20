import React, { useState } from 'react';
import { Service } from '../types';
import { External } from '../icons';

export default function Card({ svc, index }: { svc: Service; index: number }) {
  const [broken, setBroken] = useState(false);

  return (
    <a className="card" href={svc.href} target="_blank" rel="noreferrer"
       style={{ ['--i' as any]: index }} title={svc.image}>
      <span className="ico">
        {broken
          ? <span className="letter">{svc.name[0].toUpperCase()}</span>
          : <img src={svc.icon} alt="" loading="lazy" onError={() => setBroken(true)} />}
      </span>
      <div className="body">
        <div className="line">
          <span className={`dot${svc.online ? ' up' : ''}`}
                title={svc.online ? '探测到 HTTP 响应' : '未响应，端口按容器端口推断'} />
          <span className="name">{svc.name}</span>
        </div>
        <div className="tags">
          <span className={`tag${svc.online ? '' : ' guess'}`}>{svc.scheme}:{svc.port}</span>
          {svc.ports.length > 1 && <span className="tag">+{svc.ports.length - 1}</span>}
        </div>
      </div>
      <span className="go"><External /></span>
    </a>
  );
}
