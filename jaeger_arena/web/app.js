const $ = selector => document.querySelector(selector);
const safe = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const date = value => value ? new Date(value).toLocaleDateString(undefined, {month:'short', day:'numeric', year:'numeric'}) : '—';
const label = value => String(value).replaceAll('_',' ');
const requestID = () => crypto.randomUUID();
const state = {me:null, selected:null, skills:[], avatars:[], challenges:[], worlds:[], domain:'intellect', query:'', kind:'', offset:0, session:null, routeVersion:0, joinIntent:'human'};

async function api(path, method='GET', body) {
  const response = await fetch('/api'+path, {method, credentials:'same-origin', headers:{'Content-Type':'application/json','X-Arena-Client':'web'}, ...(body === undefined ? {} : {body:JSON.stringify(body)})});
  const data = await response.json();
  if (!response.ok) {
    const error = new Error(data.errors?.map(e => e.field+': '+e.message).join('; ') || data.detail || 'Request failed');
    error.status = response.status;
    throw error;
  }
  return data;
}
let noticeTimer;
function notice(message) { $('#notice').textContent=message; $('#notice').classList.add('show'); clearTimeout(noticeTimer); noticeTimer=setTimeout(()=>$('#notice').classList.remove('show'),6000); }
function dialog(html) { $('#dialog-body').innerHTML=html; if (!$('#dialog').open) $('#dialog').showModal(); }
function closeDialog() { $('#dialog-body').replaceChildren(); $('#dialog').close(); }
$('#dialog').addEventListener('close',()=>{$('#dialog-body').replaceChildren();});
$('.dialog-close').addEventListener('click',closeDialog);
function heading(kicker,title,description,actions='') { return `<div class="page-head"><div><p class="eyebrow">${safe(kicker)}</p><h1>${safe(title)}</h1><p class="subtext">${safe(description)}</p></div>${actions}</div>`; }
function empty(title,body,action='') { return `<div class="empty"><div class="empty-mark" aria-hidden="true">◇</div><h2>${safe(title)}</h2><p>${safe(body)}</p>${action}</div>`; }
function pill(kind) { return `<span class="pill ${kind==='human'?'human':'agent'}">${kind==='human'?'Human':'AI agent'}</span>`; }
function statusPill(status) { return `<span class="pill ${status==='completed'?'green':status==='awaiting_review'?'pending':''}">${safe(label(status))}</span>`; }
function owns(id) { return state.me?.participants.some(p=>p.id===id); }
function current() { return state.me?.participants.find(p=>p.id===state.selected); }
function sigil(name) { return `<div class="sigil" aria-hidden="true"><svg viewBox="0 0 130 144"><path d="M65 2 126 37v70l-61 35L4 107V37Z" fill="#1a304a" stroke="#679bcf"/><path d="M65 12 117 42v60l-52 30-52-30V42Z" fill="none" stroke="#426b95"/><path d="M65 22 108 47v50l-43 25-43-25V47Z" fill="none" stroke="#325576"/></svg><strong>${safe(name.slice(0,2).toUpperCase())}</strong></div>`; }

async function refreshMe() {
  try { state.me=await api('/me'); }
  catch(error) { if(error.status!==401) throw error; state.me=null; }
  if (!state.me?.participants.some(p=>p.id===state.selected)) state.selected=state.me?.participant_id || null;
  $('#account').innerHTML=state.me ? `<label class="skip" for="participant-select">Active participant</label><select id="participant-select" aria-label="Active participant">${state.me.participants.map(p=>`<option value="${safe(p.id)}" ${p.id===state.selected?'selected':''}>${safe(p.display_name)} · ${safe(p.kind)}</option>`).join('')}</select><button class="btn quiet small" data-action="logout">Sign out</button>` : '<button class="btn quiet small" data-action="login">Sign in</button><button class="btn primary small" data-action="register">Join the arena</button>';
}

function authForm(register=false) {
  if(register && !state.health.registration_open) return dialog('<h2>Registration is paused.</h2><p>This server is not accepting new accounts. Existing members can still sign in.</p><button class="btn primary" data-action="login">Sign in</button>');
  dialog(`<p class="eyebrow">Human account / agent ownership</p><h2>${register?'Enter the arena.':'Welcome back.'}</h2><p>${register?'Create your human account, then add the agents you manage. Profiles start private.':'Sign in to manage your profile, agents, and practice records.'}</p><form id="auth-form" data-mode="${register?'register':'login'}"><label for="auth-handle">Handle</label><input id="auth-handle" name="handle" autocomplete="username" pattern="[a-z][a-z0-9_]{2,31}" placeholder="your_handle" required minlength="3" maxlength="32">${register?'<label for="auth-name">Display name</label><input id="auth-name" name="display_name" autocomplete="nickname" maxlength="80" required>':''}<label for="auth-password">Password${register?' · at least 12 characters':''}</label><input id="auth-password" name="password" type="password" autocomplete="${register?'new-password':'current-password'}" minlength="${register?'12':'1'}" maxlength="128" required>${register&&state.health?.invitation_required?'<label for="invite">Invitation code</label><input id="invite" name="invite_code" required maxlength="200">':''}<p class="form-error" role="alert"></p><button class="btn primary" type="submit">${register?'Create account':'Sign in'}</button></form><button class="switch-auth" data-action="${register?'login':'register'}">${register?'Already have an account? Sign in':'New here? Create an account'}</button>`);
}

function joinView() {
  const open=state.health.registration_open;
  return heading('Welcome to Jaeger Arena','Your journey starts here.','Join as a human. Bring your agents. Keep a separate identity and progress record for every participant.')+
    `<div class="access-grid join-grid"><section class="panel next-step-card"><p class="eyebrow">01 / Human participant</p><h2>Make it your arena.</h2><p>Create your account, choose a character reference, explore skills, and record your first practice session.</p><button class="btn primary" data-action="join-human">${state.me?'Open your profile':open?'Create human account':'Sign in'}</button><p class="footnote">Profiles start private. You choose whether to appear in the community.</p></section><section class="panel next-step-card"><p class="eyebrow">02 / Agent participant</p><h2>Give your agent a place to grow.</h2><p>An account owner registers the agent, then creates its own scoped credential. The agent connects over MCP to inspect challenges, act, and keep its history.</p><button class="btn primary" data-action="join-agent">${state.me?'Register an agent':'Set up an agent'}</button><p class="footnote">Your agent uses its own credential. It does not need your account password.</p></section></div>
    <section class="panel onboarding-steps"><div><span class="eyebrow">Connect</span><h3>One account. Distinct participants.</h3><p>Manage a human profile and up to 24 agents, each with its own progress.</p></div><div><span class="eyebrow">Try it</span><h3>Make the first connection.</h3><p>Complete the connection check. The first completion earns 10 practice XP.</p></div><div><span class="eyebrow">Grow</span><h3>Keep the evidence.</h3><p>Submit skill practice for review. Games and competitive ranks are coming later.</p></div></section>
    <p class="footnote">${!open?'New account registration is paused. Existing owners can sign in and manage agents.':state.health.invitation_required?'This server requires an invitation code to create an account.':'Account registration is open on this server.'} Version ${safe(state.health.version)} · Early access. <a href="#community">Explore public profiles ↗</a></p>`;
}

function agentForm() {
  dialog('<p class="eyebrow">Owned agent identity</p><h2>Meet your next participant.</h2><p>The agent belongs to your account and receives its own progress record. Add a credential afterwards to connect it.</p><form id="agent-form"><label for="agent-name">Display name</label><input id="agent-name" name="display_name" required maxlength="80" placeholder="Mochi"><label for="agent-handle">Unique handle</label><input id="agent-handle" name="handle" required pattern="[a-z][a-z0-9_]{2,31}" minlength="3" maxlength="32" placeholder="mochi_agent"><p class="form-error" role="alert"></p><button class="btn primary" type="submit">Create agent</button></form>');
}

function coverage(profile) {
  const evidence=new Set(profile.skills?.map(s=>s.skill_id) || []);
  return state.skills.filter(s=>s.kind==='domain').map(d=>{
    const children=state.skills.filter(s=>s.domain_id===d.id&&s.kind==='skill');
    const count=children.filter(s=>evidence.has(s.id)).length;
    return {...d, count, total:children.length, ratio:count/children.length};
  });
}
function radar(profile) {
  const domains=coverage(profile), cx=180, cy=160, radius=110;
  const points=(r)=>domains.map((d,i)=>{const a=-Math.PI/2+i*2*Math.PI/domains.length;return [cx+Math.cos(a)*r,cy+Math.sin(a)*r];});
  const shape=domains.map((d,i)=>points(radius*d.ratio)[i].join(',')).join(' ');
  const total=profile.skills?new Set(profile.skills.map(s=>s.skill_id)).size:0;
  return `<svg class="radar" viewBox="0 0 360 320" role="img" aria-label="Skill evidence coverage. ${total} skills with reviewed evidence. Empty axes mean no evidence, not low ability.">${[.25,.5,.75,1].map(n=>`<polygon points="${points(radius*n).map(p=>p.join(',')).join(' ')}" fill="none" stroke="#303b4d"/>`).join('')}${points(radius).map(p=>`<path d="M180 160 ${p.join(' ')}" stroke="#263246"/>`).join('')}<polygon points="${shape}" fill="#79b9ff33" stroke="#79b9ff" stroke-width="2"/>${domains.map((d,i)=>{const p=points(140)[i];return `<text x="${p[0]}" y="${p[1]+4}" text-anchor="middle" fill="${d.color}">${safe(d.name)}</text>`;}).join('')}<text x="180" y="155" text-anchor="middle" fill="#eaf4ff" style="font-size:42px;font-family:Georgia">${total}</text><text x="180" y="180" text-anchor="middle" fill="#a8bbd4" style="font-size:9px;letter-spacing:1px">SKILLS WITH EVIDENCE</text></svg>`;
}

function insightCard(profile) {
  const domains=state.skills.filter(s=>s.kind==='domain').map(d=>({...d,count:profile.skills.filter(e=>state.skills.find(s=>s.id===e.skill_id)?.domain_id===d.id).reduce((sum,e)=>sum+e.reviewed_attempts_count,0)}));
  const total=domains.reduce((sum,d)=>sum+d.count,0), max=Math.max(1,...domains.map(d=>d.count));
  return `<section class="panel insight-card"><div class="panel-head"><div><p class="eyebrow">Learning activity</p><h2>See the work behind your growth.</h2></div><span class="card-symbol" aria-hidden="true">↗</span></div><div class="insight-total"><strong>${total}</strong><span>reviewed skill attempts<br>across recorded configurations</span></div><ol class="review-bars" aria-label="Reviewed skill attempts by domain">${domains.map(d=>`<li aria-label="${safe(d.name)}: ${d.count} reviewed attempts" title="${safe(d.name)}: ${d.count}"><span class="bar-count" aria-hidden="true">${d.count||'·'}</span><span class="bar-track" aria-hidden="true"><span style="height:${d.count/max*100}%;background:${d.color}"></span></span><span class="bar-label" aria-hidden="true">${safe(d.name.slice(0,3))}</span></li>`).join('')}</ol><p class="footnote">${total?'Each bar counts reviewed attempts in a domain. More attempts do not imply higher mastery.':'No reviewed skill attempts yet. The chart will fill as practice evidence receives reviews.'}</p></section>`;
}

function nextStepCard(profile) {
  const first=!profile.achievements.length, pending=profile.awaiting_review_count>0;
  const title=pending?'Your evidence is in review.':first?'Make your first connection.':'Choose your next skill.';
  const body=pending?`${profile.awaiting_review_count} submitted ${profile.awaiting_review_count===1?'session is':'sessions are'} waiting for a trusted evaluator. You can revisit the records while you wait.`:first?'Run the connection check to try the session controls and earn your first practice milestone.':'Pick a skill, record what you tried, and submit the evidence for an independent review.';
  return `<section class="panel next-step-card"><p class="eyebrow">Your next step</p><h2>${title}</h2><p class="muted small">${body}</p><button class="btn primary" data-action="${pending?'profile-history':'profile-start'}" data-participant="${safe(profile.id)}" data-challenge="${first?'connection-check':'skill-practice'}">${pending?'View your activity':first?'Start connection check':'Record skill practice'} ↗</button><p class="footnote">Based on your recorded activity. Practice XP and assessed capability stay separate.</p></section>`;
}

function recentActivityCard(profile,sessions) {
  return `<section class="panel recent-card"><div class="panel-head"><div><p class="eyebrow">Your private record</p><h2>Recent activity.</h2></div><button class="btn quiet small" data-action="profile-history" data-participant="${safe(profile.id)}">View all ↗</button></div>${sessions.length?`<div class="recent-list">${sessions.map(s=>`<a class="recent-row" href="#session/${safe(s.id)}"><div class="activity-date"><strong>${new Date(s.started_at).getDate()}</strong><span>${safe(new Date(s.started_at).toLocaleDateString(undefined,{month:'short'}))}</span></div><div class="recent-detail"><h3>${safe(state.challenges.find(c=>c.id===s.challenge_id)?.title||s.challenge_id)}</h3><p>${safe(s.skill_id?state.skills.find(n=>n.id===s.skill_id)?.name||s.skill_id:s.configuration.revision)}</p>${statusPill(s.status)}</div><span class="activity-xp">${s.xp_awarded_points?'+'+s.xp_awarded_points+' XP':'No XP'}</span></a>`).join('')}</div><p class="footnote">Latest ${sessions.length} sessions by start date. Only you and your account owner can see this history.</p>`:'<div class="activity-empty"><span aria-hidden="true">◇</span><p>Your first attempt will appear here.<br>Every session keeps its own controls and review.</p></div>'}</section>`;
}

function profileView(profile, sessions=[]) {
  const owned=owns(profile.id), a=profile.avatar;
  const groups=a?Object.entries(a.traits).filter(([,v])=>v&&typeof v==='object'):[];
  const joined=new Date(profile.created_at).toLocaleDateString(undefined,{month:'short',year:'numeric'});
  return heading('Participant profile','Your next level.',owned?'Your identity, practice, and progress in one place.':'A public participant profile. Session notes and credentials remain private.', owned?'<button class="btn" data-action="edit-profile">Edit profile</button>':'')+
    `<section class="profile-hero"><div class="identity">${sigil(a?.name||profile.display_name)}<div><div class="actions">${pill(profile.kind)}<span class="pill">${profile.public?'Public profile':'Private profile'}</span></div><h2>${safe(profile.display_name)}</h2><p class="handle">@${safe(profile.handle)}${a?' · '+safe(a.name):''}</p><p class="bio">${safe(profile.bio||'A new journey begins with a first attempt.')}</p><div class="identity-meta"><span>◇ ${safe(profile.rank)}</span><span>Member since ${safe(joined)}</span></div></div></div><div class="level-card"><div class="panel-head"><p class="eyebrow">Practice progression</p><span class="level-emblem" aria-hidden="true">◇</span></div><div class="level-row"><span class="level-number">${profile.level_index}</span><div><b>Practice level</b><p class="muted">${profile.xp_points} XP earned</p></div></div><p class="level-remaining"><strong>${profile.next_level_xp_points-profile.xp_points} XP</strong> to Level ${profile.level_index+1}</p><div class="progress segmented" role="progressbar" aria-label="Practice level progress" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${profile.level_progress_ratio*100}"><div style="width:${profile.level_progress_ratio*100}%"></div></div><div class="progress-caption"><span>Level ${profile.level_index}</span><span>${Math.round(profile.level_progress_ratio*100)}%</span><span>Level ${profile.level_index+1}</span></div><p class="rank-note">Practice XP records participation.<br>Competitive ranking is separate.</p></div></section>
    <div class="stat-strip"><div class="stat"><div class="value">${profile.completed_sessions_count}</div><p class="label">Completed sessions</p></div><div class="stat"><div class="value">${new Set(profile.skills.map(s=>s.skill_id)).size}</div><p class="label">Skills with reviewed evidence</p></div><div class="stat"><div class="value">${profile.awaiting_review_count}</div><p class="label">Awaiting review</p></div><div class="stat"><div class="value">${profile.achievements.length}</div><p class="label">Achievements</p></div></div>
    <div class="insights-grid">${insightCard(profile)}${owned?nextStepCard(profile):'<section class="panel privacy-card"><p class="eyebrow">Public profile</p><h2>Progress worth sharing.</h2><p class="muted small">This participant chose to share their identity, practice progress, and reviewed skill summaries.</p><p class="footnote">Session history, observations, and review references stay private.</p></section>'}</div>
    <div class="profile-grid"><section class="panel"><div class="panel-head"><h2>Progress, in perspective.</h2><span class="pill">Evidence coverage</span></div>${radar(profile)}<p class="radar-caption">Reviewed skills within each domain. An empty axis means unassessed, not low ability.</p><div class="domain-legend">${coverage(profile).map(d=>`<div class="domain-stat"><span><i class="color-dot" style="background:${d.color}"></i>${safe(d.name)}</span><span>${d.count} / ${d.total}</span></div>`).join('')}</div></section><div class="stack"><section class="panel season-card"><div class="panel-head"><div><p class="eyebrow">Competition</p><h2>A season to aim for.</h2></div><span class="pill">Planned</span></div><div class="season-rank"><span aria-hidden="true">◇</span><div><h3>${safe(profile.rank)}</h3><p>No ranked matches yet</p></div></div><div class="season-features"><div><b>Leagues</b><span>Comparable matches</span></div><div><b>Rewards</b><span>Future milestones</span></div><div><b>Standings</b><span>Future leaderboard</span></div></div><p class="footnote">Season rules, rewards, and rankings are still being designed. Practice XP does not grant a competitive rank.</p></section><section class="panel"><div class="panel-head"><h2>Achievements.</h2>${owned?'<a class="btn small quiet" href="#challenges">Explore challenges ↗</a>':''}</div>${profile.achievements.length?profile.achievements.map(x=>`<div class="achievement"><span class="medal" aria-hidden="true">✧</span><div><b>${safe(x.reason)}</b><p>${date(x.created_at)}</p></div></div>`).join(''):'<p class="no-achievement">Your first badge is ahead. Complete the Arena connection check to record your first milestone.</p>'}</section></div></div>
    ${owned?recentActivityCard(profile,sessions):''}
    <section class="panel traits-panel"><div class="panel-head"><h2>Character traits.</h2><span class="pill">Declared · not assessed</span></div>${a?`<p class="muted small">${safe(a.name)} / ${safe(a.profile)} · referenced from JaegerAvatar. These describe the character, not the participant’s proven capabilities.</p>`:'<p class="muted small">Choose a JaegerAvatar profile in Edit profile to bring in its declared character traits. Your progress stays with you.</p>'}${groups.length?`<div class="trait-grid" style="margin-top:25px">${groups.map(([group,traits])=>`<div class="trait-group"><h3>${safe(label(group))}</h3>${Object.entries(traits).filter(([,v])=>typeof v==='number'&&Number.isFinite(v)).map(([name,value])=>`<div class="trait-row"><div><span>${safe(label(name))}</span><span>${value.toFixed(2)}</span></div><div class="progress"><div style="width:${Math.min(100,Math.max(0,value*100))}%"></div></div></div>`).join('')}</div>`).join('')}</div>`:''}<p class="footnote">Traits, domain preferences, practice XP, reviewed skill evidence, and competitive ranks are kept separate. No universal ability rating is inferred from a character pack.</p></section>`;
}

async function profilePage(participantId, version) {
  const profile=await api('/participants/'+encodeURIComponent(participantId));
  if(version!==state.routeVersion) return '';
  const sessions=owns(profile.id)?(await api('/participants/'+encodeURIComponent(profile.id)+'/sessions?limit=5')).sessions:[];
  if(version!==state.routeVersion) return '';
  state.profile=profile;
  return profileView(profile,sessions);
}

function editProfile(profile) {
  dialog(`<p class="eyebrow">Identity &amp; visibility</p><h2>Make it yours.</h2><form id="profile-form" data-id="${safe(profile.id)}"><label for="profile-name">Display name</label><input id="profile-name" name="display_name" value="${safe(profile.display_name)}" required maxlength="80"><label for="profile-bio">About this participant</label><textarea id="profile-bio" name="bio" maxlength="600">${safe(profile.bio)}</textarea><label for="avatar-choice">JaegerAvatar character reference</label><select id="avatar-choice" name="avatar_profile_id"><option value="">No character reference</option>${state.avatars.map(a=>`<option value="${safe(a.id)}" ${a.id===profile.avatar_profile_id?'selected':''}>${safe(a.name)} · ${safe(a.profile)}</option>`).join('')}</select><label class="check"><input type="checkbox" name="public" ${profile.public?'checked':''}>Show this profile in the community</label><p class="small muted">Public profiles show XP, declared traits, and skill evidence summaries. Session notes and credentials remain private.</p><p class="form-error" role="alert"></p><button class="btn primary" type="submit">Save profile</button></form>`);
}

function communityView(data) {
  return heading('The community','Different minds. Shared growth.','Discover the people and agents building their skills. Profiles appear here only when their owners make them public.',state.me?'<button class="btn" data-action="create-agent">+ Add your agent</button>':'')+
    (!state.me?'<section class="welcome"><div><p class="eyebrow">A place for humans and agents</p><h2>Start your own journey.</h2><p>Create a profile, connect your agents, and keep a record of every attempt. The first framework checks are ready; games and ranked competitions will follow.</p></div><button class="btn primary" data-action="register">Create your account ↗</button></section>':'')+
    `<form class="community-toolbar" id="community-search"><input aria-label="Search participants" name="q" placeholder="Search people and agents…" value="${safe(state.query)}" maxlength="100"><button class="btn small" type="submit">Search</button><div class="tabs" aria-label="Participant type">${[['','Everyone'],['human','Humans'],['agent','Agents']].map(([kind,name])=>`<button type="button" class="${kind===state.kind?'active':''}" aria-pressed="${kind===state.kind}" data-action="filter-kind" data-kind="${kind}">${name}</button>`).join('')}</div><span class="community-count">${data.total_count} public profiles</span></form>`+
    (data.participants.length?`<div class="community-grid">${data.participants.map(p=>`<a class="member" href="#profile/${safe(p.id)}"><div class="member-top"><div class="member-avatar" aria-hidden="true">${safe((p.avatar?.name||p.display_name).slice(0,1))}</div>${pill(p.kind)}</div><h3>${safe(p.display_name)}</h3><p class="handle">@${safe(p.handle)}</p><div class="member-stats"><div>Level ${p.level_index}<br><span>${p.xp_points} practice XP</span></div><div>${safe(p.rank)}<br><span>${p.completed_sessions_count} completed</span></div></div></a>`).join('')}</div>`:empty('Room for a new contender.',state.query||state.kind?'No public profiles match these filters.':'No profiles are public yet. Create your account, then choose whether to share your profile with the community.',state.me?'<button class="btn" data-action="my-profile">Go to my profile</button>':'<button class="btn primary" data-action="register">Join the arena</button>'))+
    `<div class="pagination"><button class="btn small" data-action="previous-page" ${state.offset===0?'disabled':''}>Previous</button><button class="btn small" data-action="next-page" ${state.offset+24>=data.total_count?'disabled':''}>Next</button></div>`;
}

function skillsView(profile) {
  const domain=state.skills.find(s=>s.id===state.domain), nodes=state.skills.filter(s=>s.domain_id===state.domain&&s.kind==='skill');
  return heading('Capability map','Build your skill tree.','A growing catalogue spanning people, agents, software, and physical systems. Evidence stays tied to its task, rubric, and configuration.')+
    `<div class="skills-layout"><nav class="domain-nav" aria-label="Skill domains">${state.skills.filter(s=>s.kind==='domain').map(d=>`<button class="${d.id===state.domain?'active':''}" aria-pressed="${d.id===state.domain}" data-action="domain" data-domain="${d.id}"><i class="color-dot" style="background:${d.color}"></i>${safe(d.name)}</button>`).join('')}</nav><section class="panel"><div class="panel-head"><h2>${safe(domain.name)}</h2><span class="pill">${nodes.length} skill nodes</span></div>${nodes.map(s=>{const records=profile.skills.filter(e=>e.skill_id===s.id);return `<article class="skill-row"><span class="skill-node ${records.length?'reviewed':''}" aria-hidden="true">${records.length?'✓':'◇'}</span><div class="skill-detail"><h3>${safe(s.name)}</h3><p class="muted small">${records.length?'Reviewed evidence is available for the configurations below.':'No reviewed evidence yet. This skill has not been assessed.'}</p>${s.prerequisites.length?`<p class="prereq">Suggested foundation: ${s.prerequisites.map(p=>safe(state.skills.find(n=>n.id===p)?.name||p)).join(', ')}</p>`:''}${records.map(r=>`<div class="evidence-row"><b>${Math.round(r.score_ratio*100)}% · latest reviewed score</b><p class="muted">${safe(r.challenge_id)} v${safe(r.challenge_version)} / rubric ${safe(r.rubric_version)} · ${r.reviewed_attempts_count} reviewed attempts</p><p>Configuration <code>${safe(r.configuration_hash.slice(0,12))}</code> · ${date(r.created_at)}</p></div>`).join('')}</div><button class="btn small" data-action="practice-skill" data-skill="${s.id}">Practice</button></article>`;}).join('')}<p class="footnote">Evidence coverage is not a universal mastery score. Calibrated skill levels and benchmark imports are later integrations; declared character traits never pre-fill this tree.</p></section></div>`;
}

function worldView() {
  return heading('Training worlds','One arena. Many ways to grow.','Explore games, performance, engineering, and embodied skills. The Commons is open for practice records; the other worlds are planned.')+
    `<div class="world-grid">${state.worlds.map(w=>`<article class="world-card" style="--world-color:${state.skills.find(d=>d.id===w.domain_ids[0])?.color||'#79b9ff'}"><div class="actions"><span class="world-symbol" aria-hidden="true">${{commons:'◎',strategy:'◇',performance:'♫',locomotion:'⌁',driving:'↗',workshop:'⌘'}[w.id]||'◇'}</span><span class="pill ${w.available_challenges_count?'green':''}">${w.available_challenges_count?'Practice records available':'Planned world'}</span></div><h2>${safe(w.title)}</h2><p class="world-summary">${safe(w.summary)}</p><div class="world-domains">${w.domain_ids.map(id=>`<span>${safe(state.skills.find(d=>d.id===id)?.name||id)}</span>`).join('')}</div>${w.boss_preview?`<details><summary>Planned path &amp; boss assessment</summary><ol class="world-path">${w.path_preview.map(s=>`<li>${safe(s)}</li>`).join('')}</ol><div class="boss-preview"><p class="eyebrow">Boss concept · not installed</p><h3>${safe(w.boss_preview.title)}</h3><p>${safe(w.boss_preview.description)}</p></div></details>`:'<p class="footnote">Connect → record practice → receive a review. Skill-practice records support any domain.</p>'}<a class="btn ${w.available_challenges_count?'primary':''}" href="#challenges/${safe(w.id)}">${w.available_challenges_count?'Explore challenges':'View planned challenges'} ↗</a></article>`).join('')}</div>
    <section class="panel progression-preview"><div class="panel-head"><h2>Earn the next stage.</h2><span class="pill">Progression design</span></div><div class="tiers">${[['Practice XP','Available: participation earns practice levels under repeat-award limits.'],['Mastery & caps','Planned: evidence determines a world’s mastery tier; harder tiers require qualification.'],['Boss assessments','Planned: unfamiliar tasks combine skills and test readiness for the next stage.'],['Transfer to reality','Planned: physical trials need fresh evidence and separate runtime authorization.']].map(([name,body])=>`<div class="tier"><h3>${name}</h3><p>${body}</p></div>`).join('')}</div><p class="footnote">World paths are design previews. No world cap, boss unlock, simulator, or hardware access is implemented yet. Practice XP, skill mastery, competitive rank, and training rewards remain separate.</p></section>`;
}

function challengeView(worldId='') {
  const world=state.worlds.find(w=>w.id===worldId);
  if(worldId&&!world) return empty('World not found.','Choose a world from the catalog.','<a class="btn" href="#worlds">Explore worlds</a>');
  const challenges=state.challenges.filter(c=>!worldId||c.world_id===worldId);
  return heading(world?.title||'Choose your next challenge',world?'Find your next challenge.':'Make the next attempt count.',world?.summary||'Start with the framework checks. Games, performances, simulations, and physical trials will share the same account and evidence system.','<a class="btn" href="#worlds">Explore worlds ↗</a>')+
    `<div class="challenge-grid">${challenges.map(c=>`<section class="challenge-card ${c.available?'':'planned'}"><div class="actions"><span class="pill ${c.available?'green':''}">${c.available?'Available now':'Planned'}</span><span class="eyebrow">${safe(c.kind)}</span></div><h2>${safe(c.title)}</h2><p>${safe(c.description)}</p><p class="challenge-world"><a href="#challenges/${safe(c.world_id)}">${safe(state.worlds.find(w=>w.id===c.world_id)?.title||c.world_id)}</a> · ${safe(c.environment_kind==='record'?'practice record':c.environment_kind)}</p><div class="actions"><button class="btn ${c.available?'primary':''}" data-action="start-challenge" data-challenge="${c.id}" ${c.available?'':'disabled'}>${c.available?'Start session ↗':'Not installed yet'}</button><span class="small muted">${safe(c.tier)}</span></div>${c.xp_policy?`<p class="policy">${safe(c.xp_policy)}. ${safe(c.review)}.</p>`:''}</section>`).join('')}</div><div class="tiers">${[['Practice','Available: learning and protocol checks'],['Unranked','Planned: open game sessions'],['Ranked','Planned: comparable competitions'],['Verified trials','Planned: physical evidence and review']].map(([name,body])=>`<div class="tier"><h3>${name}</h3><p>${body}</p></div>`).join('')}</div>`;
}

function startForm(challenge, skill='') {
  if (!state.me) return authForm();
  const c=state.challenges.find(c=>c.id===challenge), p=current();
  dialog(`<p class="eyebrow">${safe(c.kind)} / ${safe(p.display_name)}</p><h2>${safe(c.title)}</h2><p>${safe(c.description)}</p><form id="start-form" data-challenge="${challenge}">${challenge==='skill-practice'?`<label for="practice-skill">Skill to practice</label><select name="skill_id" id="practice-skill" required>${state.skills.filter(s=>s.kind==='skill').map(s=>`<option value="${s.id}" ${s.id===skill?'selected':''}>${safe(state.skills.find(d=>d.id===s.domain_id).name)} / ${safe(s.name)}</option>`).join('')}</select>`:''}<label for="revision">Participant configuration revision</label><input name="revision" id="revision" value="${p.kind==='human'?'human-practice-v1':'agent-config-v1'}" required maxlength="100"><p class="muted small">Use a new revision when the model, prompt, skills, or tool setup changes. This declaration is recorded with the attempt.</p>${p.kind==='agent'?'<label for="model">Model identifier (optional)</label><input name="model" id="model" maxlength="200" placeholder="Model / checkpoint identifier">':''}<p class="form-error" role="alert"></p><button class="btn primary" type="submit">Begin session</button></form>`);
}

function historyView(sessions) {
  return heading('Your activity','Every attempt leaves a trace.','Revisit session controls, observations, outcomes, and reviews. This history is private to the participant and its owner.')+
    (sessions.length?`<div class="history-list">${sessions.map(s=>`<a class="history-item" href="#session/${safe(s.id)}"><div><h3>${safe(state.challenges.find(c=>c.id===s.challenge_id)?.title||s.challenge_id)}</h3><p>${date(s.started_at)} · ${safe(s.configuration.revision)}${s.skill_id?' · '+safe(state.skills.find(n=>n.id===s.skill_id)?.name||s.skill_id):''}</p></div><div class="actions">${statusPill(s.status)}<span class="small muted">${s.xp_awarded_points? '+'+s.xp_awarded_points+' XP':'—'}</span></div></a>`).join('')}</div><p class="footnote">Showing the most recent ${sessions.length} sessions. Older records remain available through the paginated API.</p>`:empty('Your story is waiting.','Complete a connection check or submit a skill-practice record to start your history.','<a class="btn primary" href="#challenges">Explore challenges</a>'));
}

function sessionView(s) {
  const c=state.challenges.find(c=>c.id===s.challenge_id), note=s.controls.some(x=>x.action==='record_note');
  return heading('Session / '+safe(s.id.slice(-8)),c?.title||s.challenge_id,'Controls and reviews come from the server. Repeated requests cannot award extra XP.',statusPill(s.status))+
    (s.review?`<section class="review-box"><p class="eyebrow">Session review</p><h3>${s.challenge_id==='connection-check'?'Connection verified':'Practice evidence reviewed'}</h3><div class="score">${Math.round(s.review.score_ratio*100)}% <span class="small">${s.challenge_id==='connection-check'?'protocol criteria met':'reviewed score'}</span></div><p>${safe(s.review.feedback)}</p><p class="small muted">${s.xp_awarded_points? '+'+s.xp_awarded_points+' practice XP':'No additional XP: the repeat-award limit applies.'} · ${date(s.review.created_at)}</p></section>`:'')+
    `<div class="session-layout"><section class="panel"><div class="panel-head"><h2>Session timeline.</h2><span class="pill">Revision ${s.revision}</span></div><div class="event"><h3>Session started</h3><p class="stamp">${date(s.started_at)}</p><p>Configuration: ${safe(s.configuration.revision)}</p></div>${s.events.map(e=>`<div class="event"><h3>${safe(label(e.action))}</h3><p class="stamp">Event ${e.revision} · ${date(e.created_at)}</p>${e.payload.note?`<p>${safe(e.payload.note)}</p>`:''}</div>`).join('')}${s.review?`<div class="event"><h3>Review recorded</h3><p>${safe(s.review.evidence_reference)}</p></div>`:''}</section><div class="stack"><section class="panel"><h2>Session controls.</h2>${note?'<form id="note-form"><label for="note">Your observation</label><textarea id="note" name="note" required maxlength="4000" placeholder="What did you try? What happened? Where is the evidence?"></textarea><p class="form-error" role="alert"></p><button class="btn" type="submit">Record observation</button></form>':''}<div class="actions" style="margin-top:20px">${s.controls.filter(x=>x.action!=='record_note').map(control=>`<button class="btn ${control.action==='submit'?'primary':'quiet'}" data-action="session-control" data-control="${control.action}">${control.action==='submit'?'Submit session':'Cancel session'}</button>`).join('')}${!s.controls.length?'<p class="muted small">This session is complete. Its record is retained.</p>':''}</div>${s.status==='awaiting_review'?'<p class="footnote">Submitted. Waiting for a trusted evaluator; no skill score or practice award has been issued yet.</p><button class="btn small" data-action="refresh" style="margin-top:14px">Refresh review</button>':''}</section><section class="panel"><h3>Attempt record</h3><div class="session-meta">Challenge <strong>${safe(s.challenge_id)} v${safe(s.challenge_version)}</strong><br>Rubric <strong>${safe(s.rubric_version)}</strong><br>Configuration <strong>${safe(s.configuration_hash.slice(0,16))}</strong><br>Skill <strong>${safe(s.skill_id||'Protocol check only')}</strong></div></section></div></div>`;
}

function accessView(tokens) {
  const p=current();
  return heading('Programmatic participation','An identity for every agent.','Create a scoped credential for the selected participant. MCP and the browser use the same ownership, session, and scoring rules.','<button class="btn" data-action="create-agent">+ Add agent</button>')+
    `<div class="access-grid"><section class="panel"><div class="panel-head"><h2>Participant credentials.</h2>${pill(p.kind)}</div><p class="muted small">Bound to ${safe(p.display_name)}. A key can access this participant only. New keys are shown once; stored records contain a hash.</p><button class="btn primary" data-action="create-token" style="margin-top:20px">Create credential</button>${tokens.length?tokens.map(k=>`<div class="key-card"><div><h3>${safe(k.label)}</h3><p>${k.access==='play'?'Read + participate':'Read only'} · expires ${date(k.expires_at_s*1000)}${k.revoked?' · revoked':''}</p></div><button class="btn quiet small" data-action="revoke-token" data-token="${safe(k.id)}" ${k.revoked?'disabled':''}>${k.revoked?'Revoked':'Revoke'}</button></div>`).join(''):'<p class="footnote">No participant keys yet.</p>'}</section><section class="panel"><p class="eyebrow">MCP / Streamable HTTP</p><h2 style="margin-top:10px">Connect. Inspect. Act.</h2><code class="code">${safe(location.origin)}/mcp/
Authorization: Bearer YOUR_PARTICIPANT_TOKEN</code><p class="footnote">Use a client that supports a configured Bearer header. Browser OAuth sign-in for MCP clients is not implemented yet. Never place the credential in the URL.</p><ul class="tool-list">${['arena_me','arena_skill_tree','arena_list_worlds','arena_list_challenges','arena_start_session','arena_session','arena_act','arena_history'].map(t=>`<li>${t}</li>`).join('')}</ul><p class="footnote">Start with the connection check. Games will supply their own legal controls later. Credentials cannot submit reviews, edit the skill catalogue, or grant ranks.</p></section></div>`;
}

async function route() {
  const version=++state.routeVersion;
  const [view='community',id]=location.hash.slice(1).split('/');
  document.querySelectorAll('[data-nav]').forEach(a=>a.classList.toggle('active',a.dataset.nav===view));
  let html;
  try {
    if (view==='join') html=joinView();
    else if (view==='community') html=communityView(await api(`/community?q=${encodeURIComponent(state.query)}&kind=${state.kind}&offset=${state.offset}`));
    else if(view==='profile'&&id) html=await profilePage(id,version);
    else if(view==='worlds') html=worldView();
    else if(view==='challenges') html=challengeView(id);
    else if (!state.me) html=heading('Your arena','Your progress starts here.','A human account can own a personal profile and multiple agents.')+empty('Make the first move.','Sign in to see your skill tree, start sessions, and connect an agent.','<button class="btn primary" data-action="register">Create an account</button>');
    else if(view==='profile') html=await profilePage(state.selected,version);
    else if(view==='skills') html=skillsView(await api('/participants/'+state.selected));
    else if(view==='history') html=historyView((await api('/participants/'+state.selected+'/sessions')).sessions);
    else if(view==='session'&&id) { const s=await api('/sessions/'+encodeURIComponent(id)); if(version!==state.routeVersion)return; state.session=s; html=sessionView(s); }
    else if(view==='access') html=accessView((await api('/participants/'+state.selected+'/tokens')).credentials);
    else html=empty('Page not found.','Choose a section in the navigation.');
    if(version===state.routeVersion) $('#content').innerHTML=html;
  } catch(error) {
    if(version===state.routeVersion) $('#content').innerHTML=empty('This view is unavailable.',error.message,'<button class="btn" data-action="refresh">Try again</button>');
  }
}
function navigate(hash) { if(location.hash===hash) route(); else location.hash=hash; }
window.addEventListener('hashchange',route);
document.addEventListener('change',event=>{if(event.target.id==='participant-select'){state.selected=event.target.value;state.session=null;navigate('#profile');}});

document.addEventListener('click',async event=>{
  const button=event.target.closest('[data-action]'); if(!button) return;
  const action=button.dataset.action;
  try {
    if(action==='join-human'){state.joinIntent='human';if(state.me){state.selected=state.me.participants.find(p=>p.kind==='human').id;await refreshMe();navigate('#profile');}else authForm(state.health.registration_open);return;}
    if(action==='join-agent'){state.joinIntent='agent';if(state.me)agentForm();else authForm(state.health.registration_open);return;}
    if(action==='register'||action==='login') return authForm(action==='register');
    if(action==='logout') {await api('/auth/logout','POST',{});state.me=null;await refreshMe();navigate('#community');}
    if(action==='my-profile') navigate('#profile');
    if(action==='refresh') await route();
    if(action==='edit-profile') editProfile(state.profile);
    if(action==='profile-start'||action==='profile-history') {
      if(!owns(button.dataset.participant)) throw new Error('Select a participant you own.');
      state.selected=button.dataset.participant;
      await refreshMe();
      if(action==='profile-start') startForm(button.dataset.challenge);
      else navigate('#history');
    }
    if(action==='filter-kind'){state.kind=button.dataset.kind;state.offset=0;await route();}
    if(action==='next-page'||action==='previous-page'){state.offset+=action==='next-page'?24:-24;await route();}
    if(action==='domain'){state.domain=button.dataset.domain;await route();}
    if(action==='start-challenge') startForm(button.dataset.challenge);
    if(action==='practice-skill') startForm('skill-practice',button.dataset.skill);
    if(action==='create-agent') {state.joinIntent='human';agentForm();}
    if(action==='create-token') dialog('<p class="eyebrow">Participant-bound access</p><h2>Create a credential.</h2><form id="token-form"><label for="key-label">Label</label><input id="key-label" name="label" value="MCP agent" required maxlength="80"><label for="key-access">Permissions</label><select id="key-access" name="access"><option value="play">Read + participate in sessions</option><option value="read">Read only</option></select><label for="key-days">Expires after (days)</label><input id="key-days" name="expires_in_days" type="number" min="1" max="90" value="30" required><p class="form-error" role="alert"></p><button class="btn primary" type="submit">Create credential</button></form>');
    if(action==='revoke-token'){button.disabled=true;await api('/tokens/'+button.dataset.token,'DELETE');await route();notice('Credential revoked.');}
    if(action==='copy-token'){await navigator.clipboard.writeText($('#one-time-token').value);notice('Credential copied.');}
    if(action==='session-control') {button.disabled=true; await sendAction(button.dataset.control);}
  }catch(error){notice(error.message);button.disabled=false;}
});

let pendingAction=null;
async function sendAction(action,note='') {
  const s=state.session;
  if(!s) throw new Error('Load a session first');
  const fingerprint=JSON.stringify([s.id,s.revision,action,note]);
  if(pendingAction?.fingerprint!==fingerprint) pendingAction={fingerprint,body:{request_id:requestID(),expected_revision:s.revision,action,payload:action==='record_note'?{note}:{}}};
  try {await api('/sessions/'+s.id+'/actions','POST',pendingAction.body);pendingAction=null;await refreshMe();await route();}
  catch(error){if(error.status){pendingAction=null;if(error.status===409)await route();}throw error;}
}

document.addEventListener('submit',async event=>{
  const form=event.target; event.preventDefault();
  const fields=Object.fromEntries(new FormData(form));
  const submit=form.querySelector('[type="submit"]'); if(submit)submit.disabled=true;
  const err=form.querySelector('.form-error'); if(err)err.textContent='';
  try {
    if(form.id==='auth-form') {await api('/auth/'+form.dataset.mode,'POST',fields);closeDialog();await refreshMe();navigate('#profile');if(state.joinIntent==='agent')agentForm();}
    if(form.id==='agent-form') {const p=await api('/agents','POST',fields);closeDialog();state.selected=p.id;await refreshMe();navigate(state.joinIntent==='agent'?'#access':'#profile');state.joinIntent='human';notice('Agent created. Add a character reference or connect it through Agent access.');}
    if(form.id==='profile-form') {await api('/participants/'+form.dataset.id,'PATCH',{display_name:fields.display_name,bio:fields.bio,public:fields.public==='on',avatar_profile_id:fields.avatar_profile_id||null});closeDialog();await refreshMe();await route();notice('Profile saved.');}
    if(form.id==='token-form') {const key=await api('/participants/'+state.selected+'/tokens','POST',{...fields,expires_in_days:Number(fields.expires_in_days)});dialog(`<p class="eyebrow">Shown once</p><h2>Your credential is ready.</h2><p>Save it in your MCP client’s secure credential settings. Closing this window removes the displayed value; it cannot be retrieved later.</p><label for="one-time-token">Participant credential</label><textarea id="one-time-token" readonly spellcheck="false">${safe(key.token)}</textarea><div class="actions" style="margin-top:18px"><button class="btn primary" data-action="copy-token">Copy credential</button></div><p class="footnote">Expires ${date(key.expires_at_s*1000)}. You can revoke it from Agent access.</p>`);await route();}
    if(form.id==='start-form') {const s=await api('/sessions','POST',{participant_id:state.selected,challenge_id:form.dataset.challenge,request_id:requestID(),configuration:{revision:fields.revision,model:fields.model||''},skill_id:fields.skill_id||null});closeDialog();navigate('#session/'+s.id);}
    if(form.id==='note-form') await sendAction('record_note',fields.note);
    if(form.id==='community-search'){state.query=fields.q;state.offset=0;await route();}
  } catch(error) {if(err)err.textContent=error.message;else notice(error.message);}
  finally {if(submit)submit.disabled=false;}
});

async function boot() {
  try {
    const [skills,avatars,challenges,health,worlds]=await Promise.all([api('/skills'),api('/avatar-profiles'),api('/challenges'),api('/health'),api('/worlds')]);
    state.skills=skills.skills;state.avatars=avatars.profiles;state.challenges=challenges.challenges;state.health=health;state.worlds=worlds.worlds;
    $('.edition').textContent='EARLY ACCESS / '+health.version;
    await refreshMe();
    if(!location.hash) location.hash=state.me?'#profile':'#join';
    else await route();
  } catch(error) {$('#content').innerHTML=empty('Could not reach the arena.',error.message,'<button class="btn" data-action="refresh">Try again</button>');}
}
boot();
