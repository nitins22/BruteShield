/**
 * BruteShield SOC Dashboard Controller
 * Handles SPA navigation, real-time polling, interactive charts, and modals.
 */

document.addEventListener('DOMContentLoaded', () => {
    'use strict';

    // State
    const state = {
        activeSection: 'overview',
        pollIntervalMs: 10000,
        pollTimer: null,
        liveFeedPage: 1,
        liveFeedFilter: 'all',
        liveFeedSearch: '',
        honeypotPage: 1,
        honeypotSearch: '',
        charts: {}
    };

    // DOM Elements
    const elements = {
        navItems: document.querySelectorAll('.soc-nav-item'),
        sections: document.querySelectorAll('.soc-section'),
        pollSelect: document.getElementById('poll-interval-select'),
        btnRefresh: document.getElementById('btn-manual-refresh'),
        sidebar: document.querySelector('.soc-sidebar'),
        mobileToggle: document.querySelector('.soc-mobile-toggle'),
        pageTitle: document.getElementById('soc-current-page-title'),
        statusBadge: document.getElementById('soc-status-badge'),
        investigateModal: document.getElementById('modal-investigate'),
        unblockModal: document.getElementById('modal-unblock'),
        activeAlertsBadge: document.getElementById('nav-alerts-badge')
    };

    // Initialize Navigation
    function initNavigation() {
        elements.navItems.forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const target = item.getAttribute('data-section');
                if (target) {
                    navigateTo(target);
                }
            });
        });

        // Mobile toggle
        if (elements.mobileToggle) {
            elements.mobileToggle.addEventListener('click', () => {
                elements.sidebar.classList.toggle('open');
            });
        }

        // Close sidebar on link click on mobile
        document.addEventListener('click', (e) => {
            if (window.innerWidth <= 768 && !elements.sidebar.contains(e.target) && !elements.mobileToggle.contains(e.target)) {
                elements.sidebar.classList.remove('open');
            }
        });

        // Listen for hash change
        window.addEventListener('hashchange', () => {
            const hash = window.location.hash.replace('#', '');
            if (hash) navigateTo(hash, false);
        });

        // Initial route
        const initialHash = window.location.hash.replace('#', '') || 'overview';
        navigateTo(initialHash, false);
    }

    function navigateTo(sectionId, updateHash = true) {
        state.activeSection = sectionId;

        elements.sections.forEach(sec => {
            sec.classList.remove('active');
            if (sec.id === `section-${sectionId}`) {
                sec.classList.add('active');
            }
        });

        elements.navItems.forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('data-section') === sectionId) {
                item.classList.add('active');
            }
        });

        const titles = {
            overview: 'Security Operations Center — Overview',
            live: 'Live Authentication Stream & Telemetry',
            threats: 'Threat Detection & Anomaly Investigation',
            analytics: 'Security Analytics & Research Benchmarks',
            honeypot: 'Honeypot Decoy Monitoring (/admin-login)',
            system: 'System Administration & Security Policies'
        };

        if (elements.pageTitle) {
            elements.pageTitle.textContent = titles[sectionId] || 'SOC Dashboard';
        }

        if (updateHash) {
            window.location.hash = sectionId;
        }

        // Trigger section-specific load
        loadCurrentSectionData();
    }

    // Polling Controller
    function initPolling() {
        if (elements.pollSelect) {
            elements.pollSelect.addEventListener('change', () => {
                const val = parseInt(elements.pollSelect.value, 10);
                state.pollIntervalMs = val;
                resetPolling();
            });
        }

        if (elements.btnRefresh) {
            elements.btnRefresh.addEventListener('click', () => {
                loadCurrentSectionData(true);
            });
        }

        resetPolling();
    }

    function resetPolling() {
        if (state.pollTimer) {
            clearInterval(state.pollTimer);
            state.pollTimer = null;
        }
        if (state.pollIntervalMs > 0) {
            state.pollTimer = setInterval(() => {
                loadCurrentSectionData(false);
            }, state.pollIntervalMs);
        }
    }

    function loadCurrentSectionData(forceSpinner = false) {
        switch (state.activeSection) {
            case 'overview':
                fetchOverviewData();
                break;
            case 'live':
                fetchLiveFeedData();
                break;
            case 'threats':
                fetchThreatsData();
                break;
            case 'analytics':
                fetchAnalyticsData();
                fetchBenchmarksData();
                break;
            case 'honeypot':
                fetchHoneypotData();
                break;
            case 'system':
                fetchSystemData();
                break;
        }
    }

    // -------------------------------------------------------------
    // SECTION A: Overview Data
    // -------------------------------------------------------------
    async function fetchOverviewData() {
        try {
            const res = await fetch('/dashboard/api/overview');
            if (!res.ok) return;
            const data = await res.json();
            if (!data.success) return;

            const m = data.metrics;
            document.getElementById('kpi-total-attempts').textContent = m.total_attempts.toLocaleString();
            document.getElementById('kpi-failed-attempts').textContent = m.failed_attempts.toLocaleString();
            document.getElementById('kpi-failure-rate').textContent = `${m.failure_rate}%`;
            document.getElementById('kpi-active-blocks').textContent = m.active_blocks;
            document.getElementById('kpi-honeypot-hits').textContent = m.honeypot_triggers;
            document.getElementById('kpi-active-alerts').textContent = m.unacknowledged_alerts;

            // Nav alert badge
            if (elements.activeAlertsBadge) {
                if (m.unacknowledged_alerts > 0) {
                    elements.activeAlertsBadge.textContent = m.unacknowledged_alerts;
                    elements.activeAlertsBadge.style.display = 'inline-block';
                } else {
                    elements.activeAlertsBadge.style.display = 'none';
                }
            }

            // System Status Badge
            if (elements.statusBadge) {
                elements.statusBadge.className = 'soc-status-badge';
                if (m.system_status === 'NORMAL_SECURE') {
                    elements.statusBadge.classList.add('status-healthy');
                    elements.statusBadge.innerHTML = '<span class="soc-status-dot"></span> System Normal';
                } else if (m.system_status === 'GUARDED') {
                    elements.statusBadge.classList.add('status-guarded');
                    elements.statusBadge.innerHTML = '<span class="soc-status-dot"></span> Guarded Activity';
                } else {
                    elements.statusBadge.classList.add('status-attack');
                    elements.statusBadge.innerHTML = '<span class="soc-status-dot"></span> Under Attack';
                }
            }

            // Overview Timeline Chart
            if (data.timeline && window.SocCharts) {
                if (!state.charts.overviewLine) {
                    state.charts.overviewLine = new SocCharts.LineChart('canvas-overview-trend', {
                        padding: { top: 20, right: 20, bottom: 30, left: 40 }
                    });
                }
                state.charts.overviewLine.setData(data.timeline.labels, [
                    { label: 'Successful', data: data.timeline.success, color: '#10b981', fillColor: 'rgba(16, 185, 129, 0.12)' },
                    { label: 'Failed / Anomaly', data: data.timeline.failures, color: '#f43f5e', fillColor: 'rgba(244, 63, 94, 0.15)' }
                ]);

                // Donut Chart for auth ratio
                if (!state.charts.overviewDonut) {
                    state.charts.overviewDonut = new SocCharts.DonutChart('canvas-overview-donut', {
                        centerText: `${m.total_attempts}`,
                        centerSub: 'Total Logins'
                    });
                }
                state.charts.overviewDonut.setData([
                    { label: 'Authorized', value: m.success_attempts, color: '#10b981' },
                    { label: 'Rejected', value: m.failed_attempts, color: '#f43f5e' }
                ], `${m.total_attempts}`, 'Total Events');
            }

            // Recent Events Table
            const tbody = document.getElementById('tbody-overview-recent');
            if (tbody) {
                if (!data.recent_activity.length) {
                    tbody.innerHTML = '<tr><td colspan="4" class="soc-empty-state"><p>No operational events recorded yet.</p></td></tr>';
                } else {
                    tbody.innerHTML = data.recent_activity.map(ev => `
                        <tr>
                            <td><span class="badge ${ev.type === 'HONEYPOT_HIT' ? 'badge-danger' : 'badge-info'}">${ev.type}</span></td>
                            <td><span class="soc-code-pill cursor-pointer" onclick="window.investigateIp('${ev.source}')">${escapeHtml(ev.source)}</span></td>
                            <td>${escapeHtml(ev.detail)}</td>
                            <td><span class="soc-code-pill">${ev.time}</span></td>
                        </tr>
                    `).join('');
                }
            }

        } catch (err) {
            console.error('Error fetching overview data:', err);
        }
    }

    // -------------------------------------------------------------
    // SECTION B: Live Monitoring Data
    // -------------------------------------------------------------
    async function fetchLiveFeedData() {
        try {
            const url = `/dashboard/api/live-feed?page=${state.liveFeedPage}&filter=${state.liveFeedFilter}&search=${encodeURIComponent(state.liveFeedSearch)}&limit=15`;
            const res = await fetch(url);
            if (!res.ok) return;
            const data = await res.json();
            if (!data.success) return;

            const tbody = document.getElementById('tbody-live-feed');
            if (!tbody) return;

            if (!data.items.length) {
                tbody.innerHTML = '<tr><td colspan="6" class="soc-empty-state"><p>No authentication events match the current filter.</p></td></tr>';
            } else {
                tbody.innerHTML = data.items.map(item => `
                    <tr>
                        <td><span class="soc-code-pill">${item.time_formatted}</span></td>
                        <td>
                            <a href="#" class="soc-code-pill" style="text-decoration:none; color:#38bdf8;" onclick="window.investigateIp('${item.ip}'); return false;">
                                ${escapeHtml(item.ip)}
                            </a>
                        </td>
                        <td><strong>${escapeHtml(item.username)}</strong></td>
                        <td>
                            <span class="badge ${item.success ? 'badge-success' : 'badge-danger'}">
                                ${item.success ? '✓ Authorized' : '✗ Failed'}
                            </span>
                        </td>
                        <td>
                            ${item.is_blocked 
                                ? '<span class="badge badge-danger">BLOCKED</span>' 
                                : '<span class="badge badge-success">ACTIVE</span>'}
                        </td>
                        <td>
                            <button class="btn btn-secondary btn-sm" onclick="window.investigateIp('${item.ip}')">Investigate</button>
                        </td>
                    </tr>
                `).join('');
            }

            // Pagination Controls
            const pageInfo = document.getElementById('live-feed-page-info');
            if (pageInfo) {
                pageInfo.textContent = `Page ${data.pagination.page} of ${data.pagination.total_pages} (${data.pagination.total} events)`;
            }

            const btnPrev = document.getElementById('live-feed-prev');
            const btnNext = document.getElementById('live-feed-next');
            if (btnPrev) btnPrev.disabled = (data.pagination.page <= 1);
            if (btnNext) btnNext.disabled = (data.pagination.page >= data.pagination.total_pages);

        } catch (err) {
            console.error('Error fetching live feed:', err);
        }
    }

    // -------------------------------------------------------------
    // SECTION C: Threats & Anomalies
    // -------------------------------------------------------------
    async function fetchThreatsData() {
        try {
            const res = await fetch('/dashboard/api/threats');
            if (!res.ok) return;
            const data = await res.json();
            if (!data.success) return;

            // Blocked IPs
            const tbodyBlocks = document.getElementById('tbody-active-blocks');
            if (tbodyBlocks) {
                if (!data.active_blocks.length) {
                    tbodyBlocks.innerHTML = '<tr><td colspan="5" class="soc-empty-state"><p>No IP addresses currently under quarantine block.</p></td></tr>';
                } else {
                    tbodyBlocks.innerHTML = data.active_blocks.map(b => `
                        <tr>
                            <td>
                                <a href="#" class="soc-code-pill" style="text-decoration:none; color:#f43f5e;" onclick="window.investigateIp('${b.ip}'); return false;">
                                    ${escapeHtml(b.ip)}
                                </a>
                            </td>
                            <td><span class="badge badge-danger">${b.remaining_formatted}</span></td>
                            <td>${b.block_count} time(s)</td>
                            <td><span class="soc-code-pill">${b.features.decision} (score: ${b.features.raw_score !== null ? b.features.raw_score : 'N/A'})</span></td>
                            <td>
                                <button class="btn btn-danger btn-sm" onclick="window.promptUnblock('${b.ip}')">Unblock</button>
                                <button class="btn btn-secondary btn-sm" onclick="window.investigateIp('${b.ip}')">Deep Dive</button>
                            </td>
                        </tr>
                    `).join('');
                }
            }

            // Alerts Table
            const tbodyAlerts = document.getElementById('tbody-alerts-full');
            if (tbodyAlerts) {
                if (!data.alerts.length) {
                    tbodyAlerts.innerHTML = '<tr><td colspan="5" class="soc-empty-state"><p>Zero security alerts recorded.</p></td></tr>';
                } else {
                    tbodyAlerts.innerHTML = data.alerts.map(a => `
                        <tr style="${a.is_acknowledged ? 'opacity: 0.6;' : ''}">
                            <td><span class="soc-code-pill">${a.time_formatted}</span></td>
                            <td>
                                <span class="badge ${a.level === 'HIGH' ? 'badge-danger' : (a.level === 'MEDIUM' ? 'badge-warning' : 'badge-info')}">
                                    ${a.level}
                                </span>
                            </td>
                            <td>${escapeHtml(a.message)}</td>
                            <td>
                                ${a.is_acknowledged 
                                    ? `<span class="badge badge-success">✓ Acknowledged by ${escapeHtml(a.acknowledged_by)}</span>` 
                                    : '<span class="badge badge-warning">Pending Review</span>'}
                            </td>
                            <td>
                                ${!a.is_acknowledged 
                                    ? `<button class="btn btn-primary btn-sm" onclick="window.acknowledgeAlert(${a.id})">Acknowledge</button>` 
                                    : '<span style="color:#64748b; font-size:11px;">Resolved</span>'}
                            </td>
                        </tr>
                    `).join('');
                }
            }

        } catch (err) {
            console.error('Error fetching threats data:', err);
        }
    }

    // -------------------------------------------------------------
    // SECTION D: Analytics & Benchmarks
    // -------------------------------------------------------------
    async function fetchAnalyticsData() {
        try {
            const res = await fetch('/dashboard/api/analytics');
            if (!res.ok) return;
            const data = await res.json();
            if (!data.success) return;

            // Daily chart
            if (data.daily_trend && window.SocCharts) {
                if (!state.charts.dailyBar) {
                    state.charts.dailyBar = new SocCharts.BarChart('canvas-daily-trend', {
                        padding: { top: 20, right: 20, bottom: 35, left: 40 },
                        color: '#0284c7'
                    });
                }
                state.charts.dailyBar.setData(data.daily_trend.labels, data.daily_trend.failures);
            }

            // Top Targeted Users
            const tbodyUsers = document.getElementById('tbody-top-targets');
            if (tbodyUsers) {
                if (!data.targeted_users.length) {
                    tbodyUsers.innerHTML = '<tr><td colspan="4" class="soc-empty-state"><p>No account authentication data recorded.</p></td></tr>';
                } else {
                    tbodyUsers.innerHTML = data.targeted_users.map(u => `
                        <tr>
                            <td><strong>${escapeHtml(u.username)}</strong></td>
                            <td>${u.total}</td>
                            <td><span style="color:#f43f5e; font-weight:600;">${u.failures}</span></td>
                            <td><span class="badge ${u.fail_rate > 50 ? 'badge-danger' : 'badge-warning'}">${u.fail_rate}%</span></td>
                        </tr>
                    `).join('');
                }
            }

            // Top Offending IPs
            const tbodyIps = document.getElementById('tbody-top-ips');
            if (tbodyIps) {
                if (!data.source_ips.length) {
                    tbodyIps.innerHTML = '<tr><td colspan="5" class="soc-empty-state"><p>No source IP telemetry recorded.</p></td></tr>';
                } else {
                    tbodyIps.innerHTML = data.source_ips.map(ip => `
                        <tr>
                            <td>
                                <a href="#" class="soc-code-pill" style="text-decoration:none; color:#38bdf8;" onclick="window.investigateIp('${ip.ip}'); return false;">
                                    ${escapeHtml(ip.ip)}
                                </a>
                            </td>
                            <td>${ip.total}</td>
                            <td><span style="color:#f43f5e; font-weight:600;">${ip.failures}</span></td>
                            <td>${ip.distinct_users} user(s)</td>
                            <td>
                                <button class="btn btn-secondary btn-sm" onclick="window.investigateIp('${ip.ip}')">Inspect</button>
                            </td>
                        </tr>
                    `).join('');
                }
            }

        } catch (err) {
            console.error('Error fetching analytics:', err);
        }
    }

    async function fetchBenchmarksData() {
        try {
            const res = await fetch('/dashboard/api/benchmarks');
            if (!res.ok) return;
            const data = await res.json();
            if (!data.success) return;

            const bench = data.data;

            // Render Synthetic Benchmark Table
            const tbodySynth = document.getElementById('tbody-synth-bench');
            if (tbodySynth && bench.synthetic) {
                const s = bench.synthetic;
                const m = s.metrics_comparison;
                tbodySynth.innerHTML = `
                    <tr>
                        <td><strong>Accuracy</strong></td>
                        <td><span class="soc-code-pill" style="color:#10b981;">${(m.accuracy.ml * 100).toFixed(1)}%</span></td>
                        <td><span class="soc-code-pill">${(m.accuracy.rule * 100).toFixed(1)}%</span></td>
                        <td><span class="badge badge-success">+13.0%</span></td>
                    </tr>
                    <tr>
                        <td><strong>Precision</strong></td>
                        <td><span class="soc-code-pill" style="color:#10b981;">${(m.precision.ml * 100).toFixed(1)}%</span></td>
                        <td><span class="soc-code-pill">${(m.precision.rule * 100).toFixed(1)}%</span></td>
                        <td><span class="badge badge-warning">-4.3%</span></td>
                    </tr>
                    <tr>
                        <td><strong>Recall (Detection Rate)</strong></td>
                        <td><span class="soc-code-pill" style="color:#10b981;">${(m.recall.ml * 100).toFixed(1)}%</span></td>
                        <td><span class="soc-code-pill">${(m.recall.rule * 100).toFixed(1)}%</span></td>
                        <td><span class="badge badge-success">+38.4%</span></td>
                    </tr>
                    <tr>
                        <td><strong>F1-Score</strong></td>
                        <td><span class="soc-code-pill" style="color:#10b981;">${m.f1_score.ml.toFixed(3)}</span></td>
                        <td><span class="soc-code-pill">${m.f1_score.rule.toFixed(3)}</span></td>
                        <td><span class="badge badge-success">+0.225</span></td>
                    </tr>
                    <tr>
                        <td><strong>Avg Attempts Until Block</strong></td>
                        <td><span class="soc-code-pill" style="color:#10b981;">${m.avg_block_attempt.ml} tries</span></td>
                        <td><span class="soc-code-pill">${m.avg_block_attempt.rule} tries</span></td>
                        <td><span class="badge badge-success">Faster (-1.4 attempts)</span></td>
                    </tr>
                `;
            }

            // Render LANL Benchmark Table
            const tbodyLanlExpA = document.getElementById('tbody-lanl-expA');
            if (tbodyLanlExpA && bench.lanl && bench.lanl.experiment_a) {
                tbodyLanlExpA.innerHTML = bench.lanl.experiment_a.models.map(m => `
                    <tr>
                        <td><strong>${escapeHtml(m.model)}</strong></td>
                        <td>${m.tp}</td>
                        <td>${m.fp}</td>
                        <td>${m.fn}</td>
                        <td>${m.tn}</td>
                        <td><span class="soc-code-pill">${m.precision}</span></td>
                        <td><span class="soc-code-pill" style="color:#10b981;">${m.recall}</span></td>
                        <td><span class="soc-code-pill">${m.fpr}</span></td>
                        <td><span class="soc-code-pill" style="color:#38bdf8; font-weight:bold;">${m.roc_auc}</span></td>
                    </tr>
                `).join('');
            }

            const tbodyLanlExpB = document.getElementById('tbody-lanl-expB');
            if (tbodyLanlExpB && bench.lanl && bench.lanl.experiment_b) {
                tbodyLanlExpB.innerHTML = bench.lanl.experiment_b.models.map(m => `
                    <tr>
                        <td><strong>${escapeHtml(m.model)}</strong></td>
                        <td>${m.fp}</td>
                        <td>${m.tn}</td>
                        <td><span class="soc-code-pill">${m.fpr}</span></td>
                        <td><span class="badge badge-muted">N/A (Single-Class)</span></td>
                        <td><small style="color:#94a3b8;">${escapeHtml(m.notes)}</small></td>
                    </tr>
                `).join('');
            }

        } catch (err) {
            console.error('Error fetching benchmarks:', err);
        }
    }

    // -------------------------------------------------------------
    // SECTION E: Honeypot Monitoring
    // -------------------------------------------------------------
    async function fetchHoneypotData() {
        try {
            const url = `/dashboard/api/honeypot?page=${state.honeypotPage}&search=${encodeURIComponent(state.honeypotSearch)}&limit=15`;
            const res = await fetch(url);
            if (!res.ok) return;
            const data = await res.json();
            if (!data.success) return;

            const tbody = document.getElementById('tbody-honeypot');
            if (!tbody) return;

            if (!data.items.length) {
                tbody.innerHTML = '<tr><td colspan="6" class="soc-empty-state"><p>No unauthorized interactions detected by decoy trap.</p></td></tr>';
            } else {
                tbody.innerHTML = data.items.map(h => `
                    <tr>
                        <td><span class="soc-code-pill">${h.time_formatted}</span></td>
                        <td>
                            <a href="#" class="soc-code-pill" style="text-decoration:none; color:#f43f5e;" onclick="window.investigateIp('${h.ip}'); return false;">
                                ${escapeHtml(h.ip)}
                            </a>
                        </td>
                        <td><strong>${escapeHtml(h.username_tried)}</strong></td>
                        <td><span class="soc-code-pill" style="color:#f59e0b;">${escapeHtml(h.password_masked)}</span></td>
                        <td>
                            ${h.is_blocked 
                                ? '<span class="badge badge-danger">Quarantined</span>' 
                                : '<span class="badge badge-warning">Logged</span>'}
                        </td>
                        <td>
                            <button class="btn btn-secondary btn-sm" onclick="window.investigateIp('${h.ip}')">Investigate</button>
                        </td>
                    </tr>
                `).join('');
            }

            const pageInfo = document.getElementById('honeypot-page-info');
            if (pageInfo) {
                pageInfo.textContent = `Page ${data.pagination.page} of ${data.pagination.total_pages} (${data.pagination.total} trap events)`;
            }

            const btnPrev = document.getElementById('honeypot-prev');
            const btnNext = document.getElementById('honeypot-next');
            if (btnPrev) btnPrev.disabled = (data.pagination.page <= 1);
            if (btnNext) btnNext.disabled = (data.pagination.page >= data.pagination.total_pages);

        } catch (err) {
            console.error('Error fetching honeypot logs:', err);
        }
    }

    // -------------------------------------------------------------
    // SECTION F: System Administration
    // -------------------------------------------------------------
    async function fetchSystemData() {
        try {
            const res = await fetch('/dashboard/api/system');
            if (!res.ok) return;
            const data = await res.json();
            if (!data.success) return;

            // Users Table
            const tbodyUsers = document.getElementById('tbody-system-users');
            if (tbodyUsers) {
                tbodyUsers.innerHTML = data.users.map(u => `
                    <tr>
                        <td>#${u.id}</td>
                        <td><strong>${escapeHtml(u.username)}</strong></td>
                        <td>
                            <span class="badge ${u.role === 'admin' ? 'badge-danger' : 'badge-info'}">
                                ${u.role}
                            </span>
                        </td>
                        <td><span class="soc-code-pill">${u.created_formatted}</span></td>
                    </tr>
                `).join('');
            }

            // Database info
            document.getElementById('sys-db-path').textContent = data.database.path;
            document.getElementById('sys-db-size').textContent = `${data.database.size_kb} KB (WAL: ${data.database.wal_size_kb} KB)`;
            document.getElementById('sys-db-journal').textContent = data.database.journal_mode;
            document.getElementById('sys-db-rows').textContent = 
                `Logins: ${data.database.tables.login_attempts} | Alerts: ${data.database.tables.alerts} | Vault: ${data.database.tables.vault_items}`;

            // Model info
            document.getElementById('sys-model-status').innerHTML = data.model.loaded 
                ? '<span class="badge badge-success">Active & Operational</span>' 
                : '<span class="badge badge-danger">Not Loaded</span>';
            document.getElementById('sys-model-type').textContent = data.model.model_type;
            document.getElementById('sys-model-sha256').textContent = data.model.sha256 || 'N/A';
            document.getElementById('sys-model-features').textContent = `${data.model.feature_count} features: ${data.model.features.join(', ')}`;

            // Policies
            document.getElementById('sys-policy-threshold').textContent = `${data.policies.max_failed_attempts} failures in ${data.policies.time_window_seconds}s`;
            document.getElementById('sys-policy-durations').textContent = data.policies.block_durations_seconds.map(d => `${d}s`).join(' → ');
            document.getElementById('sys-policy-captcha').textContent = `Decision score < ${data.policies.captcha_score_limit}`;
            document.getElementById('sys-policy-window').textContent = `${data.policies.sliding_window_seconds} seconds (15 min)`;

        } catch (err) {
            console.error('Error fetching system data:', err);
        }
    }

    // -------------------------------------------------------------
    // MODALS: IP Investigation & Unblocking
    // -------------------------------------------------------------
    window.investigateIp = async function(ip) {
        if (!elements.investigateModal) return;
        elements.investigateModal.classList.add('active');
        document.getElementById('modal-investigate-ip').textContent = ip;
        document.getElementById('modal-investigate-content').innerHTML = '<div class="soc-empty-state"><p>Extracting 6-dimensional behavioral feature vector...</p></div>';

        try {
            const res = await fetch(`/dashboard/api/investigate/${encodeURIComponent(ip)}`);
            if (!res.ok) throw new Error('API query failed');
            const data = await res.json();
            if (!data.success) throw new Error(data.error || 'Unknown error');

            const a = data.analysis;
            const f = a.features;

            document.getElementById('modal-investigate-content').innerHTML = `
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                    <div>
                        <span class="badge ${data.is_blocked ? 'badge-danger' : 'badge-success'}" style="font-size:13px; padding:4px 10px;">
                            ${data.is_blocked ? `BLOCKED (${data.remaining_seconds}s remaining)` : 'ACTIVE / NOT BLOCKED'}
                        </span>
                        <span style="font-size:12px; color:#94a3b8; margin-left:8px;">Historical blocks: ${data.historical_block_count}</span>
                    </div>
                    <div>
                        ${data.is_blocked ? `<button class="btn btn-danger btn-sm" onclick="window.promptUnblock('${data.ip}'); window.closeModals();">Unblock IP</button>` : ''}
                    </div>
                </div>

                <div class="soc-card" style="padding:16px; margin-bottom:16px; background:#0f172a;">
                    <div style="font-size:12px; font-weight:700; color:#38bdf8; text-transform:uppercase; margin-bottom:8px;">
                        ML Behavioral Anomaly Analysis
                    </div>
                    <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; font-size:13px;">
                        <div>ML Decision: <strong>${a.decision}</strong></div>
                        <div>Continuous Score: <strong class="soc-code-pill">${a.raw_score !== null ? a.raw_score : 'N/A'}</strong></div>
                        <div>Anomaly Flag: <span class="badge ${a.is_anomaly ? 'badge-danger' : 'badge-success'}">${a.is_anomaly ? 'YES (Anomaly)' : 'NO (Normal)'}</span></div>
                        <div>Total Records: <strong>${data.total_recorded_attempts}</strong></div>
                    </div>
                </div>

                <div style="font-size:12px; font-weight:700; color:#94a3b8; text-transform:uppercase; margin-bottom:8px;">
                    6 Behavioral Feature Dimensions
                </div>
                <div style="display:grid; grid-template-columns:repeat(3, 1fr); gap:8px; margin-bottom:16px;">
                    <div class="soc-card" style="padding:10px; margin-bottom:0; background:#0f172a;">
                        <div style="font-size:10px; color:#94a3b8;">Total Attempts</div>
                        <div style="font-size:16px; font-weight:bold; color:#f8fafc;">${f.total_attempts}</div>
                    </div>
                    <div class="soc-card" style="padding:10px; margin-bottom:0; background:#0f172a;">
                        <div style="font-size:10px; color:#94a3b8;">Failed Attempts</div>
                        <div style="font-size:16px; font-weight:bold; color:#f43f5e;">${f.failed_attempts}</div>
                    </div>
                    <div class="soc-card" style="padding:10px; margin-bottom:0; background:#0f172a;">
                        <div style="font-size:10px; color:#94a3b8;">Distinct Users</div>
                        <div style="font-size:16px; font-weight:bold; color:#38bdf8;">${f.distinct_usernames}</div>
                    </div>
                    <div class="soc-card" style="padding:10px; margin-bottom:0; background:#0f172a;">
                        <div style="font-size:10px; color:#94a3b8;">Average Gap</div>
                        <div style="font-size:16px; font-weight:bold; color:#f8fafc;">${f.avg_gap}s</div>
                    </div>
                    <div class="soc-card" style="padding:10px; margin-bottom:0; background:#0f172a;">
                        <div style="font-size:10px; color:#94a3b8;">Minimum Gap</div>
                        <div style="font-size:16px; font-weight:bold; color:#f8fafc;">${f.min_gap}s</div>
                    </div>
                    <div class="soc-card" style="padding:10px; margin-bottom:0; background:#0f172a;">
                        <div style="font-size:10px; color:#94a3b8;">Failure Ratio</div>
                        <div style="font-size:16px; font-weight:bold; color:${f.failure_ratio > 0.5 ? '#f43f5e' : '#10b981'};">
                            ${(f.failure_ratio * 100).toFixed(1)}%
                        </div>
                    </div>
                </div>

                <div style="font-size:12px; font-weight:700; color:#94a3b8; text-transform:uppercase; margin-bottom:8px;">
                    Recent Authentication History
                </div>
                <div class="soc-table-wrapper" style="max-height:180px;">
                    <table class="soc-table">
                        <thead>
                            <tr>
                                <th>Timestamp</th>
                                <th>Username Attempted</th>
                                <th>Outcome</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${data.attempt_history.length ? data.attempt_history.slice(0, 10).map(h => `
                                <tr>
                                    <td><span class="soc-code-pill">${h.time_formatted}</span></td>
                                    <td>${escapeHtml(h.username)}</td>
                                    <td><span class="badge ${h.success ? 'badge-success' : 'badge-danger'}">${h.success ? 'Success' : 'Failed'}</span></td>
                                </tr>
                            `).join('') : '<tr><td colspan="3" class="soc-empty-state"><p>No authentication events recorded for this IP.</p></td></tr>'}
                        </tbody>
                    </table>
                </div>
            `;
        } catch (err) {
            document.getElementById('modal-investigate-content').innerHTML = `
                <div class="soc-notice soc-notice-danger">
                    Failed to inspect IP ${escapeHtml(ip)}: ${escapeHtml(err.message)}
                </div>
            `;
        }
    };

    window.promptUnblock = function(ip) {
        if (!elements.unblockModal) return;
        elements.unblockModal.classList.add('active');
        document.getElementById('unblock-target-ip').textContent = ip;
        document.getElementById('unblock-confirm-btn').onclick = async () => {
            try {
                const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
                const res = await fetch('/dashboard/api/unblock-ip', {
                    method: 'POST',
                    headers: { 
                        'Content-Type': 'application/json',
                        'X-CSRF-Token': csrfToken
                    },
                    body: JSON.stringify({ ip, csrf_token: csrfToken })
                });
                const data = await res.json();
                if (data.success) {
                    window.closeModals();
                    loadCurrentSectionData(true);
                } else {
                    alert('Unblock failed: ' + (data.error || 'Unknown error'));
                }
            } catch (err) {
                alert('Request failed: ' + err);
            }
        };
    };

    window.acknowledgeAlert = async function(alertId) {
        try {
            const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content') || '';
            const res = await fetch(`/dashboard/api/threats/acknowledge/${alertId}`, {
                method: 'POST',
                headers: {
                    'X-CSRF-Token': csrfToken
                }
            });
            const data = await res.json();
            if (data.success) {
                fetchThreatsData();
                fetchOverviewData();
            }
        } catch (err) {
            console.error('Failed to acknowledge alert:', err);
        }
    };

    window.closeModals = function() {
        document.querySelectorAll('.soc-modal-backdrop').forEach(m => m.classList.remove('active'));
    };

    // Filter and Pagination Event Listeners
    const searchLive = document.getElementById('search-live-feed');
    if (searchLive) {
        searchLive.addEventListener('input', debounce((e) => {
            state.liveFeedSearch = e.target.value;
            state.liveFeedPage = 1;
            fetchLiveFeedData();
        }, 300));
    }

    const filterLive = document.getElementById('filter-live-status');
    if (filterLive) {
        filterLive.addEventListener('change', (e) => {
            state.liveFeedFilter = e.target.value;
            state.liveFeedPage = 1;
            fetchLiveFeedData();
        });
    }

    const btnLivePrev = document.getElementById('live-feed-prev');
    if (btnLivePrev) {
        btnLivePrev.addEventListener('click', () => {
            if (state.liveFeedPage > 1) {
                state.liveFeedPage--;
                fetchLiveFeedData();
            }
        });
    }

    const btnLiveNext = document.getElementById('live-feed-next');
    if (btnLiveNext) {
        btnLiveNext.addEventListener('click', () => {
            state.liveFeedPage++;
            fetchLiveFeedData();
        });
    }

    const searchHoney = document.getElementById('search-honeypot');
    if (searchHoney) {
        searchHoney.addEventListener('input', debounce((e) => {
            state.honeypotSearch = e.target.value;
            state.honeypotPage = 1;
            fetchHoneypotData();
        }, 300));
    }

    const btnHoneyPrev = document.getElementById('honeypot-prev');
    if (btnHoneyPrev) {
        btnHoneyPrev.addEventListener('click', () => {
            if (state.honeypotPage > 1) {
                state.honeypotPage--;
                fetchHoneypotData();
            }
        });
    }

    const btnHoneyNext = document.getElementById('honeypot-next');
    if (btnHoneyNext) {
        btnHoneyNext.addEventListener('click', () => {
            state.honeypotPage++;
            fetchHoneypotData();
        });
    }

    // Benchmark Tab Switching
    document.querySelectorAll('.soc-tab-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const parent = btn.closest('.soc-card') || document;
            parent.querySelectorAll('.soc-tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');

            const tabId = btn.getAttribute('data-tab');
            parent.querySelectorAll('.soc-tab-pane').forEach(p => {
                p.style.display = (p.id === tabId) ? 'block' : 'none';
            });
        });
    });

    // Helper functions
    function debounce(func, wait) {
        let timeout;
        return function(...args) {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }

    // Start App
    initNavigation();
    initPolling();
});
