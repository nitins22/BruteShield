"""
Unit and Integration Tests for LANL Benchmark Pipeline
======================================================
Tests the mathematical invariants, data quality audit, deterministic matching,
boundary embargo logic, episode censoring asymmetry, and custom Fail2ban state machine
as specified in Phase 2A Version 3.6.
"""

import pytest
from collections import deque
from bruteshield.ml.lanl_pipeline import (
    LANLConfig,
    DataQualityAuditor,
    parse_auth_line,
    DeterministicMatcher,
    run_hopcroft_karp_diagnostic,
    EpisodeAuditor,
    CustomFail2banSimulator,
    extract_active_windows
)


def test_data_quality_and_missing_value_handling():
    """
    Verifies that:
    1. LogOff records are audited and excluded.
    2. Missing values ('?') for destination users are audited and excluded from distinct usernames.
    3. Invalid source computers or non-LogOn/TGT/TGS orientations are excluded from E_observed.
    """
    auditor = DataQualityAuditor()

    # Valid LogOn line: tau = 100 - 1 = 99
    line_valid = "100,U1@DOM1,U2@DOM1,C100,C200,NTLM,Network,LogOn,Success"
    res1 = parse_auth_line(line_valid, line_idx=1, auditor=auditor)
    assert res1 is not None
    assert res1["tau"] == 99
    assert res1["dst_user"] == "U2@DOM1"
    assert auditor.retained_e_observed == 1

    # LogOff line: must be audited and rejected
    line_logoff = "101,U1@DOM1,U1@DOM1,C100,C100,?,Network,LogOff,Success"
    res2 = parse_auth_line(line_logoff, line_idx=2, auditor=auditor)
    assert res2 is None
    assert auditor.excluded_logoff == 1

    # Missing source computer ('?'): rejected
    line_no_src = "102,U1@DOM1,U2@DOM1,?,C200,NTLM,Network,LogOn,Success"
    res3 = parse_auth_line(line_no_src, line_idx=3, auditor=auditor)
    assert res3 is None
    assert auditor.missing_source_computer == 1

    # Missing destination user ('?'): retained in E_observed but dst_user is '?'
    line_unknown_dst = "103,U1@DOM1,?,C100,C200,Kerberos,Network,TGS,Success"
    res4 = parse_auth_line(line_unknown_dst, line_idx=4, auditor=auditor)
    assert res4 is not None
    assert res4["dst_user"] == "?"
    assert auditor.missing_dest_user == 1


def test_distinct_usernames_excludes_question_mark():
    """
    Verifies that active window feature calculation excludes '?' from distinct usernames count.
    """
    auth_events = [
        {"line_idx": 1, "tau": 1000, "src_user": "U1@DOM1", "dst_user": "U2@DOM1", "src_comp": "C10", "dst_comp": "C20", "status": "Success"},
        {"line_idx": 2, "tau": 1010, "src_user": "U1@DOM1", "dst_user": "?", "src_comp": "C10", "dst_comp": "C20", "status": "Success"},
        {"line_idx": 3, "tau": 1020, "src_user": "U1@DOM1", "dst_user": "U3@DOM1", "src_comp": "C10", "dst_comp": "C20", "status": "Success"},
    ]
    partitions = {"train": (0, 3542400)}
    windows, _ = extract_active_windows(auth_events, [], [], partitions)
    
    # In window containing these 3 events, valid users should be U2@DOM1 and U3@DOM1, so count = 2
    matching_wins = [w for w in windows if w["w_start"] <= 1000 < w["w_end"]]
    assert len(matching_wins) > 0
    # Features: [total_attempts, failed_attempts, distinct_usernames, avg_gap, min_gap, failure_ratio]
    features = matching_wins[0]["features"]
    assert features[0] == 3       # total attempts
    assert features[1] == 0       # failed attempts
    assert features[2] == 2       # distinct usernames (excluding '?')


def test_deterministic_matcher_tie_breaking():
    """
    Verifies deterministic 1-to-1 matching:
    - Priority 1: Exact matches (Delta tau == 0) over tolerance (0 < |Delta tau| <= 2)
    - Priority 2: dest_user match over src_user match
    - Priority 3: Lowest raw line index
    """
    matcher = DeterministicMatcher()

    redteam_records = [
        {"raw_line_idx": 1, "tau": 500, "user": "U_TARGET@DOM1", "src_comp": "C1", "dst_comp": "C2"}
    ]

    # Two competing auth events at Delta tau = 0:
    # Event A has src_user == target, Event B has dst_user == target
    auth_events = [
        {"line_idx": 10, "tau": 500, "src_user": "U_TARGET@DOM1", "dst_user": "U_OTHER@DOM1", "src_comp": "C1", "dst_comp": "C2", "status": "Success"},
        {"line_idx": 20, "tau": 500, "src_user": "U_OTHER@DOM1", "dst_user": "U_TARGET@DOM1", "src_comp": "C1", "dst_comp": "C2", "status": "Success"},
    ]

    matcher.match(redteam_records, auth_events)
    assert len(matcher.exact_matches) == 1
    # Must pick Event B (line_idx 20) because dest_user takes precedence over src_user
    assert matcher.exact_matches[0]["auth"]["line_idx"] == 20
    assert matcher.ambiguous_candidate_count == 1


def test_hopcroft_karp_diagnostic():
    """
    Verifies that Hopcroft-Karp computes maximum cardinality bipartite matching
    and does not contradict greedy matching size when graph is simple.
    """
    redteam = [
        {"raw_line_idx": 1, "tau": 100, "user": "U1@DOM1", "src_comp": "C1", "dst_comp": "C2"},
        {"raw_line_idx": 2, "tau": 101, "user": "U1@DOM1", "src_comp": "C1", "dst_comp": "C2"}
    ]
    auth = [
        {"line_idx": 1, "tau": 100, "src_user": "U1@DOM1", "dst_user": "U1@DOM1", "src_comp": "C1", "dst_comp": "C2"},
        {"line_idx": 2, "tau": 101, "src_user": "U1@DOM1", "dst_user": "U1@DOM1", "src_comp": "C1", "dst_comp": "C2"}
    ]
    size = run_hopcroft_karp_diagnostic(redteam, auth)
    assert size == 2


def test_boundary_embargo_guard():
    """
    Verifies that scoring windows intersecting G_b = [b - 86400, b + 86400)
    around partition boundaries b in {3542400, 4233600} are purged.
    """
    b = 3542400
    g_start = b - 86400  # 3456000
    g_end = b + 86400    # 3628800

    # Create dummy events
    auth_events = [
        {"line_idx": 1, "tau": 3450000, "src_user": "U1", "dst_user": "U2", "src_comp": "C1", "dst_comp": "C2", "status": "Success"},
        {"line_idx": 2, "tau": 3500000, "src_user": "U1", "dst_user": "U2", "src_comp": "C1", "dst_comp": "C2", "status": "Success"},
    ]
    partitions = {
        "train": (0, 3542400),
        "val": (3542400, 4233600)
    }

    windows, purged_count = extract_active_windows(auth_events, [], [], partitions)
    
    # All scoring windows in train with tau_score > g_start must be purged
    for w in windows:
        assert not (w["w_start"] < g_end and w["w_end"] > g_start), \
            f"Window [{w['w_start']}, {w['w_end']}) overlaps embargo [{g_start}, {g_end})"
    assert purged_count > 0


def test_episode_censoring_asymmetry():
    """
    Verifies mathematical censoring asymmetry for integer seconds:
    Left-censor:  tau_start(e) - tau_a < 3600
    Right-censor: tau_b - tau_end(e) <= 3600
    Completed:    tau_start(e) - tau_a >= 3600 AND tau_b - tau_end(e) > 3600
    """
    auditor = EpisodeAuditor()
    tau_a, tau_b = 0, 100000
    partitions = {"train": (tau_a, tau_b)}

    # Episode 1: Left-censored (tau_start = 1000, 1000 - 0 = 1000 < 3600)
    # Episode 2: Completed (tau_start = 50000, tau_end = 51000)
    # Episode 3: Right-censored (tau_start = 98000, tau_end = 99000, 100000 - 99000 = 1000 <= 3600)
    matched = [
        {"auth": {"src_comp": "C_LEFT", "tau": 1000}},
        {"auth": {"src_comp": "C_CLEAN", "tau": 50000}},
        {"auth": {"src_comp": "C_CLEAN", "tau": 51000}},
        {"auth": {"src_comp": "C_RIGHT", "tau": 98000}},
        {"auth": {"src_comp": "C_RIGHT", "tau": 99000}},
    ]

    episodes = auditor.build_episodes(matched, partitions, embargo_guards=[])
    assert len(auditor.left_censored) == 1
    assert auditor.left_censored[0]["src_comp"] == "C_LEFT"

    assert len(auditor.completed_episodes) == 1
    assert auditor.completed_episodes[0]["src_comp"] == "C_CLEAN"

    assert len(auditor.right_censored) == 1
    assert auditor.right_censored[0]["src_comp"] == "C_RIGHT"


def test_custom_fail2ban_simulation():
    """
    Verifies Fail2ban state machine:
    1. Rolling 60s findtime: failures older than 60s pruned.
    2. Maxretry=5 triggers ban for 60s.
    3. Events during active ban are blocked at firewall and do not increment queue.
    4. 3-class block attribution.
    """
    sim = CustomFail2banSimulator(maxretry=5, findtime=60, bantime=60)

    # 4 failures within 30s -> no block yet
    for i in range(4):
        res = sim.process_event({"line_idx": i+1, "src_comp": "C1", "tau": 10 + i * 5, "status": "Fail"})
        assert not res["blocked"]

    # 5th failure at tau=35 -> triggers block until tau = 35 + 60 = 95
    res5 = sim.process_event({"line_idx": 5, "src_comp": "C1", "tau": 35, "status": "Fail"})
    assert res5["blocked"]
    assert res5.get("ban_triggered")
    assert len(sim.block_events) == 1
    block_rec = sim.block_events[0]
    assert block_rec["ban_until"] == 95

    # Event at tau=50 during ban -> blocked as ban_active
    res_banned = sim.process_event({"line_idx": 6, "src_comp": "C1", "tau": 50, "status": "Fail"})
    assert res_banned["blocked"]
    assert res_banned["ban_active"]

    # Block attribution test: episode from tau=20 to tau=40
    episodes = [{"src_comp": "C1", "tau_start": 20, "tau_end": 40}]
    # Triggering failures were at 10, 15, 20, 25, 35 (3 in episode, 2 before) -> Mixed Block
    attr = sim.classify_block_attribution(block_rec, episodes)
    assert attr == "Mixed Block"
