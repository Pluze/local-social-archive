const pending = new Map();
let sequence = 0;
window.__bridgeResolve = (id, value) => {
  const request = pending.get(id);
  if (request) { pending.delete(id); request.resolve(value); }
};
window.__bridgeResolveBase64 = (id, encoded) => {
  const bytes = Uint8Array.from(atob(encoded), character => character.charCodeAt(0));
  window.__bridgeResolve(id, JSON.parse(new TextDecoder().decode(bytes)));
};
function api(action, payload = {}) {
  return new Promise(resolve => {
    const id = `r${++sequence}`;
    pending.set(id, { resolve });
    window.webkit.messageHandlers.bridge.postMessage({ id, action, payload });
  });
}

const state = { data: null, view: 'chats', filter: 'all', query: '', active: null, selected: new Set(), offset: 0, windowStart: 0, windowEnd: 0, total: 0, loadingPage: false, content: '', momentStats: null, sourceStatus: null, sourceRefreshBusy: false, liveTasks: {}, taskEpoch: 0 };
const $ = selector => document.querySelector(selector);
const $$ = selector => [...document.querySelectorAll(selector)];
const fmt = number => new Intl.NumberFormat('en-US').format(Number(number || 0));
const esc = value => String(value ?? '').replace(/[&<>"']/g, character => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[character]);
const defaultSourceProfile = {
  sourceName: 'Source', sourceApplicationName: 'source application',
  conversationName: 'Conversation', conversationPlural: 'Conversations',
  timelineName: 'Timeline', ownTimelineName: 'My Timeline',
  timelineMediaName: 'Timeline media',
  timelineNavigationHint: 'Open your own timeline in the source application, view the required items, then return and rescan.'
};
const sourceProfile = () => ({ ...defaultSourceProfile, ...(state.data?.sourceProfile || {}) });

function applySourceProfile() {
  const profile = sourceProfile();
  const conversations = $('.nav[data-view="chats"]'), timeline = $('.nav[data-view="moments"]');
  conversations.title = profile.conversationPlural;
  conversations.querySelector('span').textContent = profile.conversationPlural;
  timeline.title = profile.timelineName;
  timeline.querySelector('span').textContent = profile.timelineName;
}

function toast(message) {
  const element = $('#toast');
  element.textContent = message;
  element.classList.remove('hidden');
  setTimeout(() => element.classList.add('hidden'), 3600);
}

function chooseExportOptions(kind) {
  return new Promise(resolve => {
    const moments = kind === 'moments';
    $('#exportDialogTitle').textContent = moments ? `Export ${sourceProfile().timelineName} archive` : 'Export selected conversations';
    $('#textOption').classList.toggle('hidden', moments);
    $('#voiceOption').classList.toggle('hidden', moments);
    $('#fileOption').classList.toggle('hidden', moments);
    const applyLevel = () => {
      const level = $('#exportLevel').value;
      $$('.media-kind').forEach(item => { item.checked = level === 'complete' || (level === 'standard' && ['image', 'video', 'file'].includes(item.value)); });
    };
    $('#exportLevel').onchange = applyLevel;
    applyLevel();
    $('#exportDialog').classList.remove('hidden');
    const finish = value => { $('#exportDialog').classList.add('hidden'); resolve(value); };
    $('#cancelExport').onclick = () => finish(null);
    $('#confirmExport').onclick = () => {
      if (!$('#optSQLite').checked && !$('#optJSON').checked) return toast('Choose at least one structured format.');
      finish({
        includeSQLite: $('#optSQLite').checked,
        includeJSON: $('#optJSON').checked,
        includeText: !moments && $('#optText').checked,
        mediaKinds: $$('.media-kind:checked').filter(item => !item.closest('.hidden')).map(item => item.value)
      });
    };
  });
}

async function exportArchive(kind) {
  if (kind === 'chats' && !state.selected.size) return toast('Select at least one conversation.');
  const options = await chooseExportOptions(kind);
  if (!options) return;
  const result = kind === 'moments' ? await api('exportMoments', { options }) : await api('exportSelected', { sessionIds: [...state.selected], options });
  if (result.ok) toast(`Exported ${fmt(result.count)} items and ${fmt(result.resourceCount)} media files to ${result.path || 'Exports'}.`);
  else if (!result.cancelled) toast(result.error || 'Export failed.');
}

async function boot() {
  state.data = await api('bootstrap');
  applySourceProfile();
  renderList();
  renderHome();
}

function filtered() {
  let conversations = state.data?.conversations || [];
  if (state.filter === 'group') conversations = conversations.filter(item => item.is_group);
  if (state.filter === 'private') conversations = conversations.filter(item => !item.is_group);
  const query = state.query.toLowerCase();
  if (query) conversations = conversations.filter(item => String(item.display_name).toLowerCase().includes(query) || String(item.session_id).toLowerCase().includes(query));
  return conversations;
}

function renderList() {
  const data = state.data;
  if (!data) return;
  $('#listMeta').textContent = `${fmt(data.chat.conversationCount)} conversations · ${fmt(data.chat.messageCount)} messages`;
  const list = $('#conversationList');
  list.innerHTML = filtered().map(item => `<div class="conversation ${state.active === item.session_id ? 'active' : ''}" data-id="${esc(item.session_id)}"><div class="avatar">${esc(String(item.display_name || '?').slice(0, 1))}</div><div><h4>${esc(item.display_name)}</h4><p>${item.is_group ? 'Group' : 'Direct'} · ${fmt(item.message_count)} messages</p></div><input type="checkbox" ${state.selected.has(item.session_id) ? 'checked' : ''}></div>`).join('');
  list.querySelectorAll('.conversation').forEach(element => {
    element.onclick = event => {
      const id = element.dataset.id;
      if (event.target.tagName === 'INPUT') { event.stopPropagation(); toggleSelect(id, event.target.checked); }
      else openConversation(id);
    };
  });
}

function renderHome() {
  const data = state.data;
  if (!data) return;
  $('#contentTitle').textContent = 'Local archive overview';
  $('#contentMeta').textContent = data.archiveMode ? 'Browsing a structured archive; Keychain access occurs only during sync and media decoding' : 'Browsing a compatible text backup';
  const media = data.archiveMode ? `<div class="stat"><b>${fmt(data.chat.availableResourceCount)}</b><span>Local media / ${fmt(data.chat.resourceCount)}</span></div>` : '';
  const profile = sourceProfile();
  $('#viewer').innerHTML = `<div class="stats ${data.archiveMode ? 'four' : ''}"><div class="stat"><b>${fmt(data.chat.conversationCount)}</b><span>${esc(profile.conversationPlural)}</span></div><div class="stat"><b>${fmt(data.chat.messageCount)}</b><span>Messages</span></div>${media}<div class="stat"><b>${fmt(data.moments.postCount)}</b><span>${esc(profile.ownTimelineName)}</span></div></div><div class="empty" style="height:60%"><div class="empty-icon">✓</div><h3>${data.archiveMode ? 'Structured archive ready' : 'Text backup ready'}</h3><p>Choose a conversation or use Sources to sync current data.</p></div>`;
}

function activateNav(view) {
  $$('.nav[data-view]').forEach(item => item.classList.toggle('active', item.dataset.view === view));
}

function configureHeader(view) {
  const select = $('#selectCurrent'), refresh = $('#refreshButton');
  select.classList.toggle('hidden', view === 'tasks');
  select.textContent = view === 'moments' ? `Export ${sourceProfile().timelineName}` : 'Select';
  refresh.textContent = view === 'tasks' ? 'Refresh status' : 'Sources';
}

function bestResource(resources, kind) {
  const list = (resources || []).filter(item => item.kind === kind && item.available);
  if (kind === 'image') return list.find(item => item.variant === 'normal') || list.find(item => item.variant === 'thumbnail') || list.find(item => item.variant === 'high') || list[0];
  return list.find(item => item.variant === 'video' || item.variant === 'file') || list.find(item => item.variant === 'cover') || list[0];
}

function formatBytes(value) {
  const size = Number(value || 0);
  if (size < 1024) return `${size} B`;
  if (size < 1048576) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / 1048576).toFixed(1)} MB`;
}

function resourceBlock(message) {
  const image = bestResource(message.resources, 'image');
  const video = bestResource(message.resources, 'video');
  const voice = bestResource(message.resources, 'voice');
  const file = bestResource(message.resources, 'file');
  if (image) return `<div class="media image-media" data-resource="${image.id}"><div class="media-placeholder">Preparing image...</div></div>`;
  if (video) return `<div class="media video-media"><button class="media-open" data-resource="${video.id}">Play video</button><small>${formatBytes(video.size)}</small></div>`;
  if (voice) return `<div class="media voice-media"><button class="media-open" data-resource="${voice.id}">Open voice source</button><small>SILK · ${formatBytes(voice.size)}</small></div>`;
  if (file) return `<div class="media file-media"><button class="media-open" data-resource="${file.id}">${esc(file.original_name || 'Open file')}</button><small>${formatBytes(file.size)}</small></div>`;
  if ([3, 34, 43, 47].includes(Number(message.base_type))) return `<div class="media missing-media">${esc(message.content)}<small>Media is not local or its key index is unavailable.</small></div>`;
  return '';
}

function renderMessage(message) {
  const body = resourceBlock(message) || `<div class="bubble-text">${esc(message.content)}</div>`;
  return `<article class="message ${message.is_self ? 'mine' : 'theirs'}" data-message-id="${Number(message.id || 0)}"><div class="message-head"><b>${esc(message.sender_name)}</b><time>${esc(message.formatted_time)}</time><span>${esc(message.label)}</span></div><div class="bubble">${body}</div></article>`;
}

async function hydrateImage(element) {
  if (element.dataset.loaded) return;
  element.dataset.loaded = '1';
  try {
    const result = await api('readMedia', { resourceId: Number(element.dataset.resource) });
    if (result.ok && result.dataUrl) {
      element.innerHTML = `<img src="${result.dataUrl}" alt="Chat image"><button class="media-open overlay" data-resource="${element.dataset.resource}">Open original</button>`;
      bindMediaButtons(element);
    } else if (result.ok && result.tooLarge) {
      element.innerHTML = `<button class="media-placeholder media-open" data-resource="${element.dataset.resource}">Image is too large to preview. Open original.</button>`;
      bindMediaButtons(element);
    } else {
      element.innerHTML = `<div class="media-placeholder media-error">${esc(result.error || 'Image preview is unavailable.')}</div>`;
    }
  } catch (error) { element.innerHTML = `<div class="media-placeholder">${esc(error.message || 'Image unavailable')}</div>`; }
}

function bindMediaButtons(root = document) {
  root.querySelectorAll('.media-open').forEach(button => button.onclick = event => {
    event.stopPropagation();
    api('openResource', { resourceId: Number(button.dataset.resource) }).then(result => { if (!result.ok) toast(result.error || 'Unable to open media.'); });
  });
  root.querySelectorAll('.image-media:not([data-observed])').forEach(element => { element.dataset.observed = '1'; mediaObserver.observe(element); });
}
const mediaObserver = new IntersectionObserver(entries => entries.filter(entry => entry.isIntersecting).forEach(entry => { mediaObserver.unobserve(entry.target); hydrateImage(entry.target); }), { root: $('#viewer'), rootMargin: '400px' });

function conversationTools() {
  return `<div class="conversation-tools"><button class="ghost" id="jumpLatest">Latest</button><label>Jump to date <input type="date" id="jumpDate"></label><button class="ghost" id="jumpDateButton">Go</button><div class="conversation-find"><input id="conversationQuery" placeholder="Find messages in this chat"><button class="ghost" id="findConversation">Find</button></div></div>`;
}

function bindConversationTools(id) {
  $('#jumpLatest').onclick = () => openConversation(id, { offset: 0 });
  const jumpDate = async () => {
    const value = $('#jumpDate').value;
    if (!value) return toast('Choose a date first.');
    const end = new Date(`${value}T00:00:00`); end.setDate(end.getDate() + 1);
    const location = await api('conversationLocation', { sessionId: id, mode: 'date', value: Math.floor(end.getTime() / 1000), limit: 100 });
    if (location.ok) openConversation(id, { offset: location.offset }); else toast(location.error || 'Unable to locate that date.');
  };
  $('#jumpDateButton').onclick = jumpDate;
  const find = () => searchConversation(id, $('#conversationQuery').value.trim());
  $('#findConversation').onclick = find;
  $('#conversationQuery').onkeydown = event => { if (event.key === 'Enter') find(); };
}

async function jumpToMessage(sessionId, messageId) {
  const location = await api('conversationLocation', { sessionId, mode: 'message', value: Number(messageId), limit: 100 });
  if (!location.ok) return toast(location.error || 'Unable to locate that message.');
  await openConversation(sessionId, { offset: location.offset, anchorId: location.anchorId });
}

function showMessageSearchResults(results, title) {
  const overlay = document.createElement('div');
  overlay.className = 'modal';
  overlay.innerHTML = `<div class="modal-card search-modal"><h3>${esc(title)}</h3><div class="modal-results">${results.map(item => `<button class="search-result" data-session="${esc(item.session_id)}" data-message="${Number(item.message_id)}"><b>${esc(item.display_name)}</b><small>${new Date(Number(item.timestamp || 0) * 1000).toLocaleString()}</small><p>${esc(item.sender_name ? `${item.sender_name}: ` : '')}${esc(item.snippet)}</p></button>`).join('') || '<p>No results</p>'}</div><div class="modal-actions"><button class="ghost close-search">Close</button></div></div>`;
  document.body.appendChild(overlay);
  overlay.querySelector('.close-search').onclick = () => overlay.remove();
  overlay.querySelectorAll('.search-result').forEach(button => button.onclick = async () => { const session = button.dataset.session, message = button.dataset.message; overlay.remove(); await jumpToMessage(session, message); });
}

async function searchConversation(id, query) {
  if (query.length < 2) return toast('Enter at least two characters.');
  const result = await api('search', { query, sessionId: id });
  if (!result.ok) return toast(result.error || 'Search failed.');
  showMessageSearchResults(result.results || [], `Results in this chat: ${query}`);
}

async function loadConversationPage(direction) {
  if (state.loadingPage || !state.active) return;
  const older = direction === 'older';
  if (older && state.windowEnd >= state.total) return;
  if (!older && state.windowStart <= 0) return;
  state.loadingPage = true;
  const viewer = $('#viewer'), stream = $('.message-stream');
  const oldHeight = viewer.scrollHeight;
  const offset = older ? state.windowEnd : Math.max(0, state.windowStart - 100);
  const limit = older ? 100 : state.windowStart - offset;
  const result = await api('readConversation', { sessionId: state.active, offset, limit });
  if (result.ok && result.messages) {
    const html = result.messages.map(renderMessage).join('');
    if (older) { stream.insertAdjacentHTML('afterbegin', html); state.windowEnd = result.nextOffset; }
    else { stream.insertAdjacentHTML('beforeend', html); state.windowStart = offset; }
    bindMediaButtons(stream);
    if (older) viewer.scrollTop += viewer.scrollHeight - oldHeight;
  }
  state.loadingPage = false;
}

async function openConversation(id, options = {}) {
  state.active = id;
  renderList();
  const item = state.data.conversations.find(candidate => candidate.session_id === id);
  state.offset = Number(options.offset || 0); state.content = '';
  $('#viewer').innerHTML = '<div class="empty"><p>Loading...</p></div>';
  const result = await api('readConversation', { sessionId: id, offset: state.offset, limit: state.data.archiveMode ? 100 : 120000 });
  if (!result.ok) return toast(result.error || 'Unable to read this conversation.');
  $('#contentTitle').textContent = item.display_name;
  if (result.messages) {
    const html = result.messages.map(renderMessage).join('');
    $('#viewer').innerHTML = conversationTools() + '<div class="message-stream"></div>';
    const stream = $('.message-stream');
    stream.innerHTML = html;
    state.windowStart = state.offset; state.windowEnd = result.nextOffset; state.total = result.total;
    $('#contentMeta').textContent = `${fmt(item.message_count)} messages · ${item.is_group ? 'Group' : 'Direct'} · Structured archive`;
    bindConversationTools(id);
    bindMediaButtons();
    const viewer = $('#viewer');
    viewer.onscroll = () => {
      if (viewer.scrollTop < 140) loadConversationPage('older');
      else if (viewer.scrollTop + viewer.clientHeight > viewer.scrollHeight - 140) loadConversationPage('newer');
    };
    requestAnimationFrame(() => {
      const anchor = options.anchorId ? stream.querySelector(`[data-message-id="${Number(options.anchorId)}"]`) : null;
      if (anchor) { anchor.classList.add('jump-highlight'); anchor.scrollIntoView({ block: 'center' }); }
      else viewer.scrollTop = viewer.scrollHeight;
    });
    return;
  }
  state.content += result.content;
  $('#contentMeta').textContent = `${fmt(item.message_count)} messages · ${item.is_group ? 'Group' : 'Direct'} · ${(result.totalBytes / 1024 / 1024).toFixed(1)} MB`;
  $('#viewer').innerHTML = `<div class="transcript"><pre>${esc(state.content)}</pre>${result.hasMore ? '<button class="ghost load-more">Load more</button>' : ''}</div>`;
  $('.load-more')?.addEventListener('click', () => openConversation(id, true));
}

function toggleSelect(id, selected) {
  if (selected) state.selected.add(id); else state.selected.delete(id);
  $('#selectionCount').textContent = state.selected.size;
  $('#selectionBar').classList.toggle('hidden', !state.selected.size);
}

async function showMoments() {
  let count = state.data?.moments?.postCount || 0;
  const profile = sourceProfile();
  state.view = 'moments';
  activateNav('moments');
  configureHeader('moments');
  $('#listTitle').textContent = profile.timelineName;
  $('#listMeta').textContent = `${fmt(count)} posts published by me`;
  $('#conversationList').innerHTML = '';
  $('.tabs').classList.add('hidden');
  $('.search').classList.add('hidden');
  $('#contentTitle').textContent = profile.ownTimelineName;
  $('#contentMeta').textContent = `${fmt(count)} posts published by me`;
  if (!state.data?.moments?.ready) {
    $('#viewer').innerHTML = `<div class="empty"><h3>${esc(profile.timelineName)} has not been synced</h3><p>Open Sources and sync ${esc(profile.ownTimelineName)}. Local images will load here after the archive is created.</p><button id="goMomentsTasks" class="primary">Open Sources</button></div>`;
    $('#goMomentsTasks').onclick = showTasks;
    return;
  }
  $('#viewer').innerHTML = `<div class="empty"><p>Loading ${esc(profile.timelineName)}...</p></div>`;
  const result = await api('momentsPage', { offset: 0, limit: 40 });
  if (!result.ok) { $('#viewer').innerHTML = `<div class="empty"><h3>Unable to read ${esc(profile.timelineName)}</h3><p>${esc(result.error)}</p></div>`; return; }
  state.momentStats = result;
  count = result.total || count;
  $('#listMeta').textContent = `${fmt(count)} posts published by me`;
  $('#contentMeta').textContent = `${fmt(count)} posts published by me`;
  renderMoments(result.posts || [], result.hasMore, result.nextOffset);
}

function momentMedia(items) {
  return (items || []).map((media, index) => media.localPath ? `<div class="moment-media available" role="button" tabindex="0" data-path="${esc(media.localPath)}"><span>Local media ${index + 1}</span></div>` : '<div class="moment-media missing"><span>Not cached locally</span></div>').join('');
}

function bindMomentMedia() {
  document.querySelectorAll('.moment-media.available').forEach(async element => {
    const result = await api('readMomentMedia', { path: element.dataset.path });
    if (result.ok && result.dataUrl) {
      if (String(result.mime || '').startsWith('video/')) element.innerHTML = `<video controls preload="metadata" src="${result.dataUrl}"></video>`;
      else if (String(result.mime || '').startsWith('image/')) element.innerHTML = `<img src="${result.dataUrl}" alt="${esc(sourceProfile().timelineMediaName)}">`;
      else element.innerHTML = '<span>Open local media</span>';
    } else if (!result.ok) element.innerHTML = `<span>${esc(result.error || 'Local media is unavailable')}</span>`;
    element.onclick = event => { if (event.target.tagName !== 'VIDEO') api('openMomentMedia', { path: element.dataset.path }); };
    element.onkeydown = event => { if (event.key === 'Enter' || event.key === ' ') api('openMomentMedia', { path: element.dataset.path }); };
  });
}

function renderMoments(posts, hasMore, nextOffset) {
  const stats = state.momentStats || {};
  const profile = sourceProfile();
  const recovery = Number(stats.mediaTotal || 0) > Number(stats.localMediaCount || 0) ? `<div class="modal-actions"><button id="openMomentsSource" class="ghost">Open ${esc(profile.sourceApplicationName)}</button><button id="rescanMomentsMedia" class="primary">Rescan local media</button></div>` : '';
  const banner = `<section class="moment-recovery"><div><b>${fmt(stats.localMediaCount)} / ${fmt(stats.mediaTotal)} ${esc(profile.timelineMediaName)} files are local</b><p>The app first verifies the local cache, then asks the installed provider to resolve missing items. If an item is still unavailable, ${esc(profile.timelineNavigationHint)}</p><div id="momentRecoverStatus" class="status-line"></div></div>${recovery}</section>`;
  $('#viewer').innerHTML = banner + posts.map(post => `<article class="moment"><time>${esc(post.createTimeISO || post.tid)}</time><div class="text">${esc(post.contentDesc || '')}</div>${post.linkTitle ? `<div class="meta">Link: ${esc(post.linkTitle)}</div>` : ''}${post.media?.length ? `<div class="moment-media-grid">${momentMedia(post.media)}</div>` : ''}<div class="meta">${fmt(post.likesCount)} likes · ${fmt(post.commentsCount)} comments · ${fmt(post.mediaCount)} media</div></article>`).join('') + (hasMore ? '<button id="moreMoments" class="ghost load-more">Load more</button>' : '');
  bindMomentMedia();
  $('#openMomentsSource')?.addEventListener('click', openMomentsSource);
  $('#rescanMomentsMedia')?.addEventListener('click', rescanMomentsMedia);
  if (hasMore) $('#moreMoments').onclick = async () => { const result = await api('momentsPage', { offset: nextOffset, limit: 40 }); state.momentStats = result; renderMoments(posts.concat(result.posts || []), result.hasMore, result.nextOffset); };
}

async function openMomentsSource() {
  const status = $('#momentRecoverStatus');
  const result = await api('openMomentsSource');
  status.textContent = result.message || result.error || sourceProfile().timelineNavigationHint;
}

async function rescanMomentsMedia() {
  const button = $('#rescanMomentsMedia');
  const status = $('#momentRecoverStatus');
  button.disabled = true;
  status.textContent = `Scanning files cached locally by ${sourceProfile().sourceApplicationName}...`;
  const result = await api('rescanMomentsMedia');
  if (!result.ok) { button.disabled = false; status.textContent = result.error || 'Unable to start recovery.'; return; }
  pollTask(result.taskId, status, async () => { state.data = await api('bootstrap'); await showMoments(); });
}

function pathRow(label, path, kind) {
  return `<div class="path-row"><div><b>${esc(label)}</b><code>${esc(path || 'Not created yet')}</code></div><button class="ghost open-path" data-kind="${kind}">Open</button></div>`;
}

const sourceStepLabels = () => ({ capture: 'Source access', media: 'Protected media', chats: `${sourceProfile().conversationName} archive`, moments: sourceProfile().ownTimelineName });
const sourceStateLabels = { complete: 'Complete', partial: 'Partial', not_started: 'Not started', running: 'Running', action: 'Action needed', error: 'Failed' };

function applySourceStep(id, step = {}, task = null) {
  const active = task && (task.active || ['running', 'action'].includes(task.state));
  const failed = task?.state === 'error';
  const shownState = active ? task.state : (failed ? 'error' : (step.state || 'not_started'));
  const shownMessage = active
    ? (task.message || 'Working...')
    : (failed ? `${task.message || 'The last attempt failed.'} Previous usable result: ${step.message || 'none'}` : (step.message || 'Checking current state...'));
  const line = $(`#${id}Status`), badge = $(`#${id}Badge`), button = $(`#${id}Button`);
  if (line) { line.textContent = shownMessage; line.className = `status-line state-${shownState}`; }
  if (badge) { badge.textContent = sourceStateLabels[shownState] || shownState; badge.className = `state-badge state-${shownState}`; }
  if (button) button.disabled = Boolean(active);
  const updated = $(`#${id}Updated`);
  if (updated) updated.textContent = step.updatedAt ? `Last successful output: ${new Date(step.updatedAt).toLocaleString()}` : '';
}

function renderSourceStatus() {
  if (state.view !== 'tasks' || !state.sourceStatus) return;
  const steps = state.sourceStatus.steps || {}, tasks = { ...(state.sourceStatus.tasks || {}), ...state.liveTasks };
  applySourceStep('capture', steps.capture, tasks.capture);
  applySourceStep('media', steps.media, tasks.media);
  applySourceStep('chats', steps.chats, tasks.chats);
  applySourceStep('moments', steps.moments, tasks.moments);
  const lifecycle = $('#lifecycleRows');
  if (lifecycle) lifecycle.innerHTML = ['capture', 'media', 'chats', 'moments'].map(id => {
    const step = steps[id] || {}, task = tasks[id];
    const live = task && (task.active || ['running', 'action'].includes(task.state));
    const status = live ? task.state : (task?.state === 'error' ? 'error' : step.state);
    const detail = live ? task.message : (task?.state === 'error' ? task.message : step.message);
    return `<div class="lifecycle-row"><span class="state-dot state-${esc(status || 'not_started')}"></span><b>${esc(sourceStepLabels()[id])}</b><span>${esc(sourceStateLabels[status] || status || 'Not started')}</span><small>${esc(detail || '')}</small></div>`;
  }).join('');
  const checked = $('#sourceCheckedAt');
  if (checked) checked.textContent = `Live status checked ${new Date(state.sourceStatus.checkedAt).toLocaleTimeString()}`;
  const credentials = state.sourceStatus.credentials || {};
  const credentialTarget = $('#credentialStatus');
  if (credentialTarget) credentialTarget.textContent = `${fmt(credentials.databaseRecords)} database, ${fmt(credentials.mediaRecords)} media, ${fmt(credentials.authorizationRecords)} authorization records in Keychain`;
}

async function refreshSourceStatus(forceCredentials = false) {
  if (state.sourceRefreshBusy) return;
  state.sourceRefreshBusy = true;
  try {
    const result = await api('sourceStatus', { forceCredentials });
    if (result.ok) { state.sourceStatus = result; renderSourceStatus(); }
  } finally { state.sourceRefreshBusy = false; }
}

function bindPathButtons() {
  $$('.open-path').forEach(button => button.onclick = async () => {
    const result = await api('openBackup', { kind: button.dataset.kind });
    toast(result.ok ? `Opened ${result.path}` : (result.error || 'Unable to open that location.'));
  });
}

function confirmCredentialReset() {
  return new Promise(resolve => {
    const overlay = document.createElement('div');
    overlay.className = 'modal';
    overlay.innerHTML = `<div class="modal-card"><h3>Reset source credentials?</h3><p>This removes all database, media, and administrator credentials from Keychain. It also removes the isolated source client and decrypted source snapshots. Existing archives, backups, and exports are preserved.</p><div class="modal-actions"><button class="ghost" id="keepCredentials">Cancel</button><button class="primary" id="confirmCredentialReset">Reset credentials</button></div></div>`;
    document.body.appendChild(overlay);
    const finish = value => { overlay.remove(); resolve(value); };
    overlay.querySelector('#keepCredentials').onclick = () => finish(false);
    overlay.querySelector('#confirmCredentialReset').onclick = () => finish(true);
  });
}

async function loadCredentialStatus() {
  const status = await api('credentialStatus');
  const target = $('#credentialStatus');
  if (!target) return;
  target.textContent = status.ok
    ? `${fmt(status.databaseRecords)} database, ${fmt(status.mediaRecords)} media, ${fmt(status.authorizationRecords)} authorization records in Keychain`
    : (status.error || 'Credential status is unavailable.');
}

async function resetCredentials() {
  if (!await confirmCredentialReset()) return;
	state.taskEpoch += 1;
	state.liveTasks = {};
	renderSourceStatus();
  const result = await api('resetCredentials');
  toast(result.ok ? result.message : (result.error || 'Credential reset failed.'));
  await loadCredentialStatus();
  await refreshSourceStatus();
}

function showTasks() {
  const paths = state.data?.storage || {};
  const profile = sourceProfile();
  state.view = 'tasks';
  activateNav('tasks');
  configureHeader('tasks');
  $('#listTitle').textContent = 'Sources';
  $('#listMeta').textContent = 'Credentials, snapshots, archives, and media';
  $('#conversationList').innerHTML = '';
  $('.tabs').classList.add('hidden');
  $('.search').classList.add('hidden');
  $('#contentTitle').textContent = 'Extract and refresh';
  $('#contentMeta').textContent = 'Live state from credentials, snapshots, archives, HTML viewers, and local media';
  $('#viewer').innerHTML = `<div class="task-grid">
    <div class="task-card"><div class="task-heading"><h3>1. Configure authorized source</h3><span id="captureBadge" class="state-badge">Checking</span></div><p>Prepare and validate reusable access for the current account. Re-run only after an account change or compatibility failure.</p><div class="inline-actions"><button class="primary" id="captureButton">Configure / Repair source</button><button class="ghost" id="capturePrivacy">Full Disk Access</button></div><div class="status-line" id="captureStatus">Checking current state...</div><small id="captureUpdated" class="updated-at"></small></div>
    <div class="task-card"><div class="task-heading"><h3>2. Enable protected media</h3><span id="mediaBadge" class="state-badge">Checking</span></div><p>Validate the current account's image credential. Successful validation makes existing indexed chat images previewable immediately.</p><button class="primary" id="mediaButton">Enable / Revalidate media</button><div class="status-line" id="mediaStatus">Checking current state...</div><small id="mediaUpdated" class="updated-at"></small></div>
    <div class="task-card"><div class="task-heading"><h3>3. Sync ${esc(profile.conversationName)} archive</h3><span id="chatsBadge" class="state-badge">Checking</span></div><p>Refresh one current snapshot, searchable archive, text files, and directly openable HTML viewer. Unchanged sources are reused.</p><button class="primary" id="chatsButton">Sync ${esc(profile.conversationPlural)}</button><div class="status-line" id="chatsStatus">Checking current state...</div><small id="chatsUpdated" class="updated-at"></small></div>
    <div class="task-card"><div class="task-heading"><h3>4. Sync ${esc(profile.ownTimelineName)}</h3><span id="momentsBadge" class="state-badge">Checking</span></div><p>Refresh posts published by the current account, reuse verified archive files, scan local cache, and ask the installed provider to resolve remaining media.</p><button class="primary" id="momentsButton">Sync ${esc(profile.ownTimelineName)}</button><div class="status-line" id="momentsStatus">Checking current state...</div><small id="momentsUpdated" class="updated-at"></small></div>
    <div class="task-card full lifecycle-card"><div class="task-heading"><h3>Current lifecycle</h3><small id="sourceCheckedAt">Checking live status...</small></div><div id="lifecycleRows" class="lifecycle-rows"></div></div>
    <div class="task-card full permission-card"><div><h3>Credential lifecycle</h3><p>Reset before switching accounts or removing the app. Keychain credentials and decrypted source snapshots are cleared; archives and exports stay available.</p><div class="status-line" id="credentialStatus">Reading Keychain status...</div></div><button class="ghost" id="resetCredentials">Switch account / Reset credentials</button></div>
    <div class="task-card full"><h3>Local data locations</h3><p>All durable files created by this app stay under the application data root. Exports are saved automatically in its Exports folder.</p>${pathRow('Application data', paths.root, 'root')}${pathRow('Exports', paths.exports, 'exports')}${pathRow(`${profile.conversationName} snapshots`, paths.chatDatabase, 'chat-db')}${pathRow(`${profile.timelineName} snapshot`, paths.momentsDatabase, 'moments-db')}${pathRow('Structured archive', paths.archive, 'archive')}</div>
    <div class="task-card full permission-card"><div><h3>macOS data permission</h3><p>Grant Full Disk Access only to /Applications/Local Social Archive.app. After replacing or updating the app, remove its old entry, add the current app again, then quit and reopen it once.</p></div><button class="ghost" id="privacy">Open Full Disk Access</button></div>
  </div>`;
  $('#captureButton').onclick = () => startTask('startCapture', '#captureStatus');
  $('#capturePrivacy').onclick = () => api('openPrivacy');
  $('#mediaButton').onclick = () => startTask('refreshImageKey', '#mediaStatus');
  $('#chatsButton').onclick = () => startTask('refreshChats', '#chatsStatus');
  $('#momentsButton').onclick = () => startTask('refreshMoments', '#momentsStatus');
  $('#resetCredentials').onclick = resetCredentials;
  $('#privacy').onclick = () => api('openPrivacy');
  bindPathButtons();
  refreshSourceStatus();
}

function pollTask(taskId, target, onDone) {
	const epoch = state.taskEpoch;
  const poll = async () => {
    const status = await api('taskStatus', { taskId });
		if (epoch !== state.taskEpoch || status.state === 'cancelled') return;
    const kind = Object.keys(state.liveTasks).find(key => state.liveTasks[key].taskId === taskId);
    if (kind) state.liveTasks[kind] = { ...status, taskId, active: !['done', 'error'].includes(status.state) };
    renderSourceStatus();
    const element = typeof target === 'string' ? $(target) : target;
    if (element) {
      element.textContent = status.message || status.state;
      element.classList.toggle('error', status.state === 'error');
    }
    if (status.state === 'done') { toast(status.message); state.data = await api('bootstrap'); if (kind) delete state.liveTasks[kind]; await refreshSourceStatus(); if (onDone) await onDone(); return; }
    if (status.state === 'error') { toast(status.message || 'Task failed.'); await refreshSourceStatus(); return; }
    setTimeout(poll, 1200);
  };
  poll();
}

async function startTask(action, targetSelector) {
  const result = await api(action);
  if (!result.ok) return toast(result.error || 'Unable to start task.');
  const kind = { startCapture: 'capture', refreshImageKey: 'media', refreshChats: 'chats', refreshMoments: 'moments' }[action];
  if (kind) state.liveTasks[kind] = { taskId: result.taskId, state: 'running', message: 'Starting...', active: true };
  renderSourceStatus();
  pollTask(result.taskId, targetSelector);
}

async function globalSearch() {
  const query = $('#searchInput').value.trim();
  if (query.length < 2) return toast('Enter at least two characters.');
  $('#contentTitle').textContent = `Full-text search: ${query}`;
  $('#viewer').innerHTML = '<div class="empty"><p>Searching all conversations...</p></div>';
  const result = await api('search', { query });
  if (!result.ok) return toast(result.error || 'Search failed.');
  $('#viewer').innerHTML = `<div class="transcript">${result.results.map(item => { const id = item.sessionId || item.session_id; const name = item.displayName || item.display_name; return `<button class="search-result" data-id="${esc(id)}" data-message="${Number(item.message_id)}"><b>${esc(name)}</b><p>${esc(item.sender_name ? `${item.sender_name}: ` : '')}${esc(item.snippet)}</p></button>`; }).join('') || '<p>No results</p>'}</div>`;
  $$('.search-result').forEach(element => element.onclick = () => jumpToMessage(element.dataset.id, element.dataset.message));
}

$$('.nav[data-view]').forEach(button => button.onclick = () => {
  const view = button.dataset.view;
  activateNav(view);
  configureHeader(view);
  if (view === 'chats') {
    state.view = 'chats';
    state.active = null;
    $('.tabs').classList.remove('hidden');
    $('.search').classList.remove('hidden');
    $('#listTitle').textContent = sourceProfile().conversationPlural;
    renderList();
    renderHome();
  } else if (view === 'moments') showMoments(); else showTasks();
});
$$('.tabs button').forEach(button => button.onclick = () => { $$('.tabs button').forEach(item => item.classList.remove('active')); button.classList.add('active'); state.filter = button.dataset.filter; renderList(); });
$('#searchInput').oninput = event => { state.query = event.target.value; renderList(); };
$('#globalSearch').onclick = globalSearch;
$('#openFolder').onclick = async () => { const result = await api('openBackup', { kind: 'root' }); toast(result.ok ? `Opened ${result.path}` : (result.error || 'Unable to open the data folder.')); };
$('#refreshButton').onclick = () => state.view === 'tasks' ? refreshSourceStatus(true) : showTasks();
$('#selectCurrent').onclick = () => { if (state.view === 'moments') exportArchive('moments'); else if (state.active) { toggleSelect(state.active, true); renderList(); } };
$('#clearSelection').onclick = () => { state.selected.clear(); renderList(); toggleSelect('', false); };
$('#exportSelected').onclick = () => exportArchive('chats');
boot();
