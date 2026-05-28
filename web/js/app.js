const API = '/api';
let currentMatchId = null;
let currentProfileId = null;

async function loadMatches() {
    const league = document.getElementById('league-filter').value;
    const date = document.getElementById('date-filter').value;
    const params = new URLSearchParams();
    if (league) params.set('league', league);
    if (date) params.set('date_from', date);

    try {
        const resp = await fetch(API + '/matches?' + params);
        const matches = await resp.json();
        const list = document.getElementById('match-list');
        list.innerHTML = matches.map(m => {
            const active = m.id === currentMatchId ? ' active' : '';
            const home = m.home_team ? m.home_team.name : '?';
            const away = m.away_team ? m.away_team.name : '?';
            const dateStr = new Date(m.match_date).toLocaleDateString('zh-CN');
            return '<li class="match-item' + active + '" onclick="selectMatch(' + m.id + ')"><div class="teams">' + home + ' vs ' + away + '</div><div class="meta">' + m.league + ' | ' + dateStr + ' | ' + m.stage + '</div></li>';
        }).join('');
    } catch(e) { console.error(e); }
}

async function selectMatch(matchId) {
    currentMatchId = matchId;
    await loadMatches();
    try {
        const resp = await fetch(API + '/matches/' + matchId);
        const match = await resp.json();
        renderMatchDetail(match);
    } catch(e) { console.error(e); }
}

function renderMatchDetail(match) {
    const panel = document.getElementById('main-panel');
    const home = match.home_team ? match.home_team.name : '?';
    const away = match.away_team ? match.away_team.name : '?';
    const dateStr = new Date(match.match_date).toLocaleString('zh-CN');
    panel.innerHTML = ''
        + '<div class="card"><h3>MATCH INFO</h3>'
        + '<h2 style="text-align:center;margin:10px 0;">' + home + ' vs ' + away + '</h2>'
        + '<p style="text-align:center;color:var(--text-dim);">' + match.league + ' | ' + match.stage + ' | ' + dateStr + '</p>'
        + '<button class="run-btn" onclick="runAnalysis()">START ANALYSIS</button></div>'
        + '<div id="result-area"><div class="placeholder" style="margin-top:20px;">Click START ANALYSIS to run the full pipeline</div></div>'
        + '<div id="factor-area"></div>';
    loadFactorPanel();
}

async function runAnalysis() {
    if (!currentMatchId) return;
    const btn = document.querySelector('.run-btn');
    btn.textContent = 'ANALYZING...';
    btn.disabled = true;

    try {
        const resp = await fetch(API + '/matches/' + currentMatchId + '/analyze', { method: 'POST' });
        const data = await resp.json();
        renderResults(data);
    } catch(e) { console.error(e); }
    btn.textContent = 'START ANALYSIS';
    btn.disabled = false;
}

function renderResults(data) {
    const sim = data.simulation;
    const adv = data.advice;
    const factors = data.factors || {};
    const llm = data.llm_summary || '';

    var scoreHtml = '';
    var dist = sim.score_distribution || {};
    var entries = Object.entries(dist).sort(function(a, b) { return b[1] - a[1]; });
    for (var i = 0; i < entries.length; i++) {
        scoreHtml += '<div class="score-item"><div class="score">' + entries[i][0] + '</div><div class="pct">' + entries[i][1] + '%</div></div>';
    }

    var suggClass = adv.suggestion;
    var suggEmoji = adv.suggestion === 'buy' ? 'BUY' : adv.suggestion === 'watch' ? 'WATCH' : 'AVOID';
    var bestText = adv.best_pick === 'home' ? 'HOME WIN' : adv.best_pick === 'draw' ? 'DRAW' : 'AWAY WIN';
    var evStr = (adv.expected_value > 0 ? '+' : '') + adv.expected_value.toFixed(3);
    var kellyStr = adv.kelly_stake ? 'Kelly: ' + adv.kelly_stake + '%' : '';

    // Factor highlights
    var factorRows = '';
    for (var k in factors) {
        var val = factors[k];
        var color = val > 55 ? 'var(--green)' : val < 45 ? 'var(--red)' : 'var(--text-dim)';
        factorRows += '<span style="color:' + color + ';margin-right:12px;font-size:12px;">' + k + ' ' + val.toFixed(0) + '</span>';
    }

    var area = document.getElementById('result-area');
    area.innerHTML = ''
        // Simulation results
        + '<div class="card"><h3>SIMULATION (' + sim.simulations + ' runs)</h3>'
        + '<div class="result-bar"><div class="home" style="width:' + sim.home_win_pct + '%"></div><div class="draw" style="width:' + sim.draw_pct + '%"></div><div class="away" style="width:' + sim.away_win_pct + '%"></div></div>'
        + '<div class="result-labels"><span>HOME ' + sim.home_win_pct + '%</span><span>DRAW ' + sim.draw_pct + '%</span><span>AWAY ' + sim.away_win_pct + '%</span></div>'
        + '<p style="margin-top:8px;font-size:12px;color:var(--text-dim);">Expected Goals: ' + sim.expected_goals + ' | Variance: ' + sim.variance + ' | Home: ' + sim.lambda_home + ' / Away: ' + sim.lambda_away + '</p></div>'

        // Key factors
        + '<div class="card"><h3>KEY FACTORS</h3>'
        + '<div style="line-height:2.2;">' + factorRows + '</div></div>'

        // Score distribution
        + '<div class="card"><h3>SCORE DISTRIBUTION</h3><div class="score-dist">' + scoreHtml + '</div></div>'

        // LLM Summary
        + '<div class="card"><h3>AI ANALYSIS</h3>'
        + '<div style="font-size:14px;line-height:1.8;color:var(--text);padding:8px 0;">' + llm + '</div></div>'

        // Advice
        + '<div class="card"><h3>STRATEGY</h3>'
        + '<div class="advice-box ' + suggClass + '">'
        + '<span style="font-size:18px;font-weight:700;">' + suggEmoji + '</span> '
        + '<span>' + bestText + ' | EV: ' + evStr + ' | ' + kellyStr + '</span></div>'
        + '<p style="margin-top:8px;font-size:12px;color:var(--text-dim);">Risk: ' + adv.risk_level.toUpperCase() + '</p></div>';
}

async function loadFactorPanel() {
    try {
        var profilesResp = await fetch(API + '/profiles');
        var profiles = await profilesResp.json();
        if (!currentProfileId) {
            var def = profiles.find(function(p) { return p.is_default; });
            currentProfileId = def ? def.id : (profiles[0] ? profiles[0].id : null);
        }
        var profileResp = await fetch(API + '/profiles/' + currentProfileId);
        var profileData = await profileResp.json();
        document.getElementById('current-profile').textContent = 'Profile: ' + (profileData.profile ? profileData.profile.name : 'Default');

        var cats = { L1: 'Fundamentals', L2: 'Tactics', L3: 'Environment', L4: 'Psychology', L5: 'Market' };
        var profileOpts = profiles.map(function(p) {
            return '<option value="' + p.id + '"' + (p.id === currentProfileId ? ' selected' : '') + '>' + p.name + '</option>';
        }).join('');

        var factorHtml = '';
        for (var catKey in cats) {
            factorHtml += '<div style="margin-bottom:8px;"><div style="font-size:11px;color:var(--accent);margin-bottom:3px;">' + cats[catKey] + '</div>';
            var catItems = profileData.items.filter(function(i) { return i.factor && i.factor.category === catKey; });
            catItems.forEach(function(i) {
                factorHtml += '<div class="factor-row" data-item-id="' + i.id + '">'
                    + '<input type="checkbox" ' + (i.enabled ? 'checked' : '') + '>'
                    + '<label>' + (i.factor ? i.factor.name : '?') + '</label>'
                    + '<input type="range" min="0" max="30" value="' + i.weight + '" oninput="this.nextElementSibling.textContent=this.value">'
                    + '<span class="weight-val">' + i.weight + '</span></div>';
            });
            factorHtml += '</div>';
        }

        var area = document.getElementById('factor-area');
        area.innerHTML = ''
            + '<div class="card"><h3>FACTOR CONFIG</h3>'
            + '<div class="profile-selector"><select onchange="switchProfile(this.value)">' + profileOpts + '</select>'
            + '<button onclick="saveProfile()">SAVE</button><button onclick="createProfile()">NEW</button></div>'
            + factorHtml + '</div>';
    } catch(e) { console.error(e); }
}

async function saveProfile() {
    var rows = document.querySelectorAll('.factor-row');
    var items = [];
    rows.forEach(function(row) {
        items.push({
            factor_config_id: parseInt(row.dataset.itemId || 0),
            weight: parseInt(row.querySelector('input[type="range"]').value),
            enabled: row.querySelector('input[type="checkbox"]').checked
        });
    });
    try {
        await fetch(API + '/profiles/' + currentProfileId + '/items', {
            method: 'PUT', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(items)
        });
        alert('Profile saved');
    } catch(e) { alert('Save failed'); }
}

async function createProfile() {
    var name = prompt('New profile name:');
    if (!name) return;
    try {
        var resp = await fetch(API + '/profiles?base_profile_id=' + currentProfileId, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });
        var data = await resp.json();
        currentProfileId = data.id;
        await loadFactorPanel();
    } catch(e) { alert('Create failed'); }
}

async function switchProfile(id) {
    currentProfileId = parseInt(id);
    await loadFactorPanel();
}

loadMatches();