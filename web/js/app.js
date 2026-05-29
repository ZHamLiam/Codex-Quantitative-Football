const API = '/api';
let currentMatchId = null;
let currentProfileId = null;
let currentMode = 'upcoming';

async function switchMode(mode) {
    currentMode = mode;
    document.querySelectorAll('.tab-btn').forEach(function(btn) { btn.classList.remove('active'); });
    document.querySelectorAll('.tab-btn').forEach(function(btn) {
        if ((mode === 'upcoming' && btn.textContent === '即将开始') || (mode === 'history' && btn.textContent === '历史比赛')) {
            btn.classList.add('active');
        }
    });
    await loadMatches();
}

async function loadMatches() {
    var league = document.getElementById('league-filter').value;
    var search = document.getElementById('search-input').value;
    var params = new URLSearchParams();
    if (league) params.set('league', league);
    if (search) params.set('search', search);
    params.set('mode', currentMode);

    try {
        var resp = await fetch(API + '/matches?' + params);
        var matches = await resp.json();
        var list = document.getElementById('match-list');
        if (matches.length === 0) {
            list.innerHTML = '<li style="color:var(--text-dim);padding:20px;text-align:center;">' + (currentMode === 'upcoming' ? '暂无即将开始的比赛' : '暂无历史比赛') + '</li>';
            return;
        }
        list.innerHTML = matches.map(function(m) {
            var active = m.id === currentMatchId ? ' active' : '';
            var home = m.home_team.name_zh || m.home_team.name || '?';
            var away = m.away_team.name_zh || m.away_team.name || '?';
            var date = new Date(m.match_date);
            var dateStr = date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' });
            var timeStr = date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' });
            var scoreStr = (m.home_score !== null && m.away_score !== null) ? m.home_score + '-' + m.away_score : dateStr + ' ' + timeStr;
            return '<li class="match-item' + active + '" onclick="selectMatch(' + m.id + ')"><div class="teams">' + home + ' vs ' + away + '</div><div class="meta">' + m.league + ' | ' + scoreStr + ' | ' + m.stage + '</div></li>';
        }).join('');
    } catch(e) { console.error(e); }
}

async function selectMatch(matchId) {
    currentMatchId = matchId;
    await loadMatches();
    try {
        var resp = await fetch(API + '/matches/' + matchId);
        var match = await resp.json();
        renderMatchDetail(match);
    } catch(e) { console.error(e); }
}

function renderMatchDetail(match) {
    var panel = document.getElementById('main-panel');
    var home = match.home_team.name_zh || match.home_team.name || '?';
    var away = match.away_team.name_zh || match.away_team.name || '?';
    var date = new Date(match.match_date);
    var dateStr = date.toLocaleString('zh-CN', { month: 'long', day: 'numeric', weekday: 'short', hour: '2-digit', minute: '2-digit' });
    var stageMap = { group_md1: '小组赛MD1', group_md2: '小组赛MD2', group_md3: '小组赛MD3', r16: '1/8决赛', qf: '1/4决赛', sf: '半决赛', final: '决赛', league: '联赛' };
    var stageZh = stageMap[match.stage] || match.stage;

    panel.innerHTML = ''
        + '<div class="card"><h3>比赛信息</h3>'
        + '<h2 style="text-align:center;margin:10px 0;">' + home + ' vs ' + away + '</h2>'
        + '<p style="text-align:center;color:var(--text-dim);">' + match.league + ' | ' + stageZh + ' | ' + dateStr + '</p>'
        + '<button class="run-btn" onclick="runAnalysis()">开始分析</button></div>'
        + '<div id="result-area"><div class="placeholder" style="margin-top:20px;">点击"开始分析"运行完整分析管线</div></div>'
        + '<div id="factor-area"></div>';
    loadFactorPanel();
}

async function runAnalysis() {
    if (!currentMatchId) return;
    var btn = document.querySelector('.run-btn');
    btn.textContent = '分析中...';
    btn.disabled = true;
    try {
        var resp = await fetch(API + '/matches/' + currentMatchId + '/analyze', { method: 'POST' });
        var data = await resp.json();
        renderResults(data);
    } catch(e) { console.error(e); }
    btn.textContent = '开始分析';
    btn.disabled = false;
}

function renderResults(data) {
    var sim = data.simulation;
    var adv = data.advice;
    var factors = data.factors || {};
    var llm = data.llm_summary || '';

    var scoreHtml = '';
    var dist = sim.score_distribution || {};
    var entries = Object.entries(dist).sort(function(a, b) { return b[1] - a[1]; });
    for (var i = 0; i < entries.length; i++) {
        scoreHtml += '<div class="score-item"><div class="score">' + entries[i][0] + '</div><div class="pct">' + entries[i][1] + '%</div></div>';
    }

    var suggClass = adv.suggestion;
    var suggLabel = adv.suggestion === 'buy' ? '✅ 建议买入' : adv.suggestion === 'watch' ? '⚠️ 观望' : '🚫 回避';
    var bestLabel = adv.best_pick === 'home' ? '主胜' : adv.best_pick === 'draw' ? '平局' : '客胜';
    var evStr = (adv.expected_value > 0 ? '+' : '') + adv.expected_value.toFixed(3);
    var kellyStr = adv.kelly_stake ? '凯利仓位: ' + adv.kelly_stake + '%' : '';

    var area = document.getElementById('result-area');
    area.innerHTML = ''
        + '<div class="card"><h3>模拟结果 (' + sim.simulations + ' 次)</h3>'
        + '<div class="result-bar"><div class="home" style="width:' + sim.home_win_pct + '%"></div><div class="draw" style="width:' + sim.draw_pct + '%"></div><div class="away" style="width:' + sim.away_win_pct + '%"></div></div>'
        + '<div class="result-labels"><span>主胜 ' + sim.home_win_pct + '%</span><span>平局 ' + sim.draw_pct + '%</span><span>客胜 ' + sim.away_win_pct + '%</span></div>'
        + '<p style="margin-top:8px;font-size:12px;color:var(--text-dim);">期望总进球: ' + sim.expected_goals + ' | 波动系数: ' + sim.variance + ' | λ主: ' + sim.lambda_home + ' / λ客: ' + sim.lambda_away + '</p></div>'

        + '<div class="card"><h3>关键因子</h3>' + _renderFactorBars(factors) + '</div>'

        + _renderUpsetCard(data.upset_analysis)

        + '<div class="card"><h3>AI 分析</h3><div style="font-size:14px;line-height:1.8;color:var(--text);padding:8px 0;">' + llm + '</div></div>'

        + '<div class="card"><h3>买入策略</h3>'
        + '<div class="advice-box ' + suggClass + '"><span style="font-size:16px;font-weight:700;">' + suggLabel + '</span> | ' + bestLabel + ' | EV: ' + evStr + ' | ' + kellyStr + '</div>'
        + '<p style="margin-top:8px;font-size:12px;color:var(--text-dim);">风险等级: ' + adv.risk_level.toUpperCase() + '</p></div>';
}

function _renderUpsetCard(ua) {
    if (!ua) return '<div class="card"><h3>爆冷 & 大比分</h3><p style="color:var(--text-dim);">暂无数据</p></div>';
    var upsetLabel = ua.upset_risk === 'HIGH' ? '🔴 高风险' : '🟢 低风险';
    var upsetColor = ua.upset_risk === 'HIGH' ? 'var(--red)' : 'var(--green)';
    var goalsLabel = ua.big_score_risk === 'HIGH' ? '🟡 可能' : '⚪ 不太可能';
    var goalsColor = ua.big_score_risk === 'HIGH' ? 'var(--yellow)' : 'var(--text-dim)';

    return '<div class="card"><h3>爆冷 & 大比分分析</h3>'
        + '<div class="upset-card">'
        + '<div class="upset-item" style="border-left-color:' + upsetColor + ';">'
        + '<div class="label">爆冷风险</div><div class="value" style="color:' + upsetColor + ';">' + upsetLabel + '</div>'
        + '<div class="detail">' + ua.underdog + ' 胜率: ' + ua.underdog_win_pct + '%</div>'
        + '<div class="detail" style="font-size:10px;">热门: ' + ua.favorite + ' | 阈值: ' + ua.upset_threshold + '%</div></div>'
        + '<div class="upset-item" style="border-left-color:' + goalsColor + ';">'
        + '<div class="label">大比分</div><div class="value" style="color:' + goalsColor + ';">' + goalsLabel + '</div>'
        + '<div class="detail">期望总进球: ' + ua.expected_goals + '</div>'
        + '<div class="detail" style="font-size:10px;">阈值: ' + ua.goals_threshold + ' 球</div></div>'
        + '</div></div>';
}

function _renderFactorBars(factors) {
    if (!factors) return '<p>No data</p>';
    var items = Object.keys(factors);
    if (items.length === 0) return '<p style="color:var(--text-dim);">所有因子均为默认值</p>';
    var html = '';
    for (var idx = 0; idx < items.length; idx++) {
        var k = items[idx];
        var item = factors[k];
        var val = 0;
        var source = '';
        if (typeof item === 'object' && item !== null) {
            val = item.value !== undefined ? item.value : 50;
            source = item.source || '';
        } else {
            val = item;
        }
        var pct = Math.max(2, Math.min(98, val));
        var barColor = val > 55 ? '#1a4a2e' : val < 45 ? '#4a1a1a' : '#2a2d3a';
        var textColor = val > 55 ? 'var(--green)' : val < 45 ? 'var(--red)' : 'var(--text-dim)';
        html += '<div style="margin-bottom:14px;">';
        html += '<div style="display:flex;justify-content:space-between;font-size:12px;margin-bottom:4px;">';
        html += '<span style="color:var(--text);font-weight:600;">' + k + '</span>';
        html += '<span style="color:' + textColor + ';font-weight:700;">' + val.toFixed(1) + '</span></div>';
        html += '<div style="height:8px;background:var(--bg);border-radius:4px;overflow:hidden;">';
        html += '<div style="height:100%;width:' + pct + '%;background:' + textColor + ';border-radius:4px;opacity:0.8;"></div></div>';
        if (source) {
            html += '<div style="font-size:10px;color:var(--text-dim);margin-top:2px;">数据来源: ' + source + '</div>';
        }
        html += '</div>';
    }
    return html;
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
        document.getElementById('current-profile').textContent = '方案: ' + (profileData.profile ? profileData.profile.name : '默认');

        var cats = { L1: '基本面', L2: '战术风格', L3: '环境因素', L4: '心理/战意', L5: '市场信号' };
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
                    + '<input type="range" min="0" max="30" value="' + i.weight + '" oninput="updateSlider(this)">'
                    + '<span class="weight-val">' + i.weight + '</span></div>';
            });
            factorHtml += '</div>';
        }

        var area = document.getElementById('factor-area');
        area.innerHTML = ''
            + '<div class="card"><h3>因子配置</h3>'
            + '<div class="profile-selector"><select onchange="switchProfile(this.value)">' + profileOpts + '</select>'
            + '<button onclick="saveProfile()">保存</button><button onclick="createProfile()">新建</button></div>'
            + factorHtml + '</div>';
    } catch(e) { console.error(e); }
}

function updateSlider(el) {
    var next = el.nextElementSibling;
    if (next) next.textContent = el.value;
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
            method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(items)
        });
        alert('方案已保存');
    } catch(e) { alert('保存失败'); }
}

async function createProfile() {
    var name = prompt('新方案名称:');
    if (!name) return;
    try {
        var resp = await fetch(API + '/profiles?base_profile_id=' + currentProfileId, {
            method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name: name })
        });
        var data = await resp.json();
        currentProfileId = data.id;
        await loadFactorPanel();
    } catch(e) { alert('创建失败'); }
}

async function switchProfile(id) {
    currentProfileId = parseInt(id);
    await loadFactorPanel();
}

switchMode('upcoming');