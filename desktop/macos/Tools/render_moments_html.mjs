#!/usr/bin/env node
import { readFileSync, writeFileSync } from 'node:fs'
import { dirname, join } from 'node:path'
const input = process.argv[2]
if (!input) throw new Error('usage: render_moments_html.mjs <moments.json>')
const data = JSON.parse(readFileSync(input, 'utf8'))
const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))
const posts = [...(data.posts || [])].sort((left, right) => (Number(right.createTime || 0) - Number(left.createTime || 0)) || String(right.tid || '').localeCompare(String(left.tid || '')))
const cards = posts.map(post => {
  const media = (post.media || []).map(item => item.localPath
    ? (/\.(?:mp4|mov|m4v)$/i.test(item.localPath) || Number(item.type) === 6
      ? `<video controls preload="metadata" src="${esc(item.localPath)}"></video>`
      : `<a href="${esc(item.localPath)}"><img loading="lazy" src="${esc(item.localPath)}" alt="Moment media"></a>`)
	: `<div class="missing">Media was not archived locally</div>`).join('')
  const comments = (post.comments || []).map(c => `<li><b>${esc(c.nickname || c.username)}</b>: ${esc(c.content)}</li>`).join('')
  const likes = (post.likes || []).map(x => x.nickname || x.username).filter(Boolean)
	return `<article><time>${esc(post.createTimeISO || post.tid)}</time><div class="text">${esc(post.contentDesc).replace(/\n/g,'<br>')}</div>${post.linkTitle?`<p>${esc(post.linkTitle)}</p>`:''}<div class="media">${media}</div>${Object.keys(post.location||{}).length?`<p class="meta">Location: ${esc(post.location.poiName||post.location.label||post.location.city||'')}</p>`:''}${likes.length?`<p class="meta">Likes: ${esc(likes.join(', '))}</p>`:''}${comments?`<ul>${comments}</ul>`:''}</article>`
}).join('\n')
const html = `<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width"><title>My Moments Backup</title><style>:root{color-scheme:dark}*{box-sizing:border-box}body{margin:0;background:#0b0d0c;color:#eef2ef;font:15px/1.6 -apple-system,BlinkMacSystemFont,sans-serif}main{max-width:820px;margin:auto;padding:42px 20px 80px}h1{font-size:30px;letter-spacing:-.03em;margin-bottom:4px}.summary,.meta,time{color:#94a099}article{margin:22px 0;padding:24px;border:1px solid #28302c;border-radius:18px;background:#141816;box-shadow:0 14px 45px #0004}.text{font-size:17px;margin:12px 0 18px;white-space:normal}.media{display:grid;grid-template-columns:repeat(3,1fr);gap:7px}.media img,.media video{display:block;width:100%;aspect-ratio:1;object-fit:cover;border-radius:10px;background:#222}.missing{min-height:100px;display:grid;place-items:center;padding:8px;border-radius:10px;background:#202522;color:#9aa39e;text-align:center;text-decoration:none}a{color:#65d696}ul{padding-left:22px}@media(max-width:520px){main{padding:24px 12px}.media{grid-template-columns:repeat(2,1fr)}article{padding:17px}}</style></head><body><main><h1>My Moments Backup</h1><p class="summary">${data.totalPosts} posts · current account only · exported ${esc(data.exportTime)}</p>${cards}</main></body></html>`
writeFileSync(join(dirname(input), 'my-moments.html'), html, { mode: 0o600 })
console.log(JSON.stringify({ posts: posts.length, output: join(dirname(input), 'my-moments.html') }))
