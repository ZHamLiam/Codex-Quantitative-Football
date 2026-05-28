const API = '/api';
let currentMatchId = null;
let currentProfileId = null;
let currentProfileItems = [];

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
    } catch(e) { console.error('loadMatches error:', e); }
}

async function selectMatch(matchId) {
    currentMatchId = matchId;
    await loadMatches();
    try {
        const resp = await fetch(API + '/matches/' + matchId);
        const match = await resp.json();
        renderMatchDetail(match);
    } catch(e) { console.error('selectMatch error:', e); }
}

function renderMatchDetail(match) {
    const panel = document.getElementById('main-panel');
    const home = match.home_team ? match.home_team.name : '?';
    const away = match.away_team ? match.away_team.name : '?';
    const dateStr = new Date(match.match_date).toLocaleString('zh-CN');
    panel.innerHTML = ''
        + '<div class="card"><h3>比赛信息</h3>'
        + '<h2 style="text-align:center;margin:10px 0;">' + home + ' vs ' + away + '</h2>'
        + '<p style="text-align:center;color:var(--text-dim);">' + match.league + ' | ' + match.stage + ' | ' + dateStr + '</p>'
        + '<button class="run-btn" onclick="runAnalysis()">开始分析</button></div>'
        + '<div id="result-area"></div><div id="factor-area"></div>';
    loadFactorPanel();
}

async function runAnalysis() {
    if (!currentMatchId) return;
    let url = API + '/matches/' + currentMatchId + '/analyze';
    if (currentProfileId) url += '?profile_id=' + currentProfileId;
    try {
        const resp = await fetch(API + '/matches/' + currentMatchId + '/analyze', { method: 'POST' });
        const data = await resp.json();
        renderResults(data);
    } catch(e) { console.error('runAnalysis error:', e); }
}

function renderResults(data) {
    const sim = data.simulation;
    const adv = data.advice;
    const area = document.getElementById('result-area');
    var scoreHtml = '';
    var dist = sim.score_distribution || {};
    for (var score in dist) {
        scoreHtml += '<div class="score-item"><div class="score">' + score + '</div><div class="pct">' + dist[score] + '%</div></div>';
    }
    var suggText = adv.suggestion === 'buy' ? '✅ 建议买入' : adv.suggestion === 'watch' ? '⚠️ 观望' : '🚫 回避';
    var bestText = adv.best_pick === 'home' ? '主胜' : adv.best_pick === 'draw' ? '平局' : '客胜';
    var evStr = (adv.expected_value > 0 ? '+' : '') + adv.expected_value;
    var kellyStr = adv.kelly_stake ? ' | 建议仓位: ' + adv.kelly_stake + '%' : '';
    area.innerHTML = ''
        + '<div class="card"><h3>模拟结果（' + sim.simulations + ' 次）</h3>'
        + '<div class="result-bar"><div class="home" style="width:' + sim.home_win_pct + '%"></div><div class="draw" style="width:' + sim.draw_pct + '%"></div><div class="away" style="width:' + sim.away_win_pct + '%"></div></div>'
        + '<div class="result-labels"><span>主胜 ' + sim.home_win_pct + '%</span><span>平局 ' + sim.draw_pct + '%</span><span>客胜 ' + sim.away_win_pct + '%</span></div>'
        + '<p style="margin-top:8px;font-size:13px;color:var(--text-dim);">期望总进球: ' + sim.expected_goals + ' | 波动系数: ' + sim.variance + ' | λ主: ' + sim.lambda_home + ' / λ客: ' + sim.lambda_away + '</p></div>'
        + '<div class="card"><h3>比分分布 Top 5</h3><div class="score-dist">' + scoreHtml + '</div></div>'
        + '<div class="card"><h3>买入建议</h3><div class="advice-box ' + adv.suggestion + '">' + suggText + ' | 最佳选择: ' + bestText + ' | 期望值: ' + evStr + kellyStr + '</div>'
        + '<p style="margin-top:8px;font-size:12px;color:var(--text-dim);">风险等级: ' + adv.risk_level + '</p></div>';
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
        currentProfileItems = profileData.items || [];

        document.getElementById('current-profile').textContent = '方案: ' + (profileData.profile ? profileData.profile.name : '默认');

        var cats = { L1: '基本面', L2: '战术风格', L3: '环境因素', L4: '心理/战意', L5: '市场信号' };
        var profileOpts = profiles.map(function(p) {
            return '<option value="' + p.id + '"' + (p.id === currentProfileId ? ' selected' : '') + '>' + p.name + '</option>';
        }).join('');

        var factorHtml = '';
        for (var catKey in cats) {
            factorHtml += '<div style="margin-bottom:10px;"><div style="font-size:12px;color:var(--accent);margin-bottom:4px;">' + cats[catKey] + '</div>';
            var catItems = currentProfileItems.filter(function(i) { return i.factor && i.factor.category === catKey; });
            catItems.forEach(function(i) {
                factorHtml += '<div class="factor-row" data-item-id="' + i.id + '">'
                    + '<input type="checkbox" ' + (i.enabled ? 'checked' : '') + '>'
                    + '<label>' + (i.factor ? i.factor.name : '?') + '</label>'
                    + '<input type="range" min="0" max="30" value="' + i.weight + '" oninput="this.nextElementSibling.textContent=this.value+\'%\'">'
                    + '<span class="weight-val">' + i.weight + '%</span></div>';
            });
            factorHtml += '</div>';
        }

        var area = document.getElementById('factor-area');
        area.innerHTML = ''
            + '<div class="card"><h3>因子配置</h3>'
            + '<div class="profile-selector"><select onchange="switchProfile(this.value)">' + profileOpts + '</select>'
            + '<button onclick="saveProfile()">保存</button><button onclick="createProfile()">新建方案</button></div>'
            + factorHtml + '</div>';
    } catch(e) { console.error('loadFactorPanel error:', e); }
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
        alert('方案已保存');
    } catch(e) { alert('保存失败: ' + e); }
}

async function createProfile() {
    var name = prompt('新方案名称:');
    if (!name) return;
    try {
        var resp = await fetch(API + '/profiles?base_profile_id=' + currentProfileId, {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: name })
        });
        var data = await resp.json();
        currentProfileId = data.id;
        await loadFactorPanel();
    } catch(e) { alert('创建失败: ' + e); }
}

async function switchProfile(id) {
    currentProfileId = parseInt(id);
    await loadFactorPanel();
}

loadMatches();
