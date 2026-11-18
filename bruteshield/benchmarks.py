"""
BruteShield Benchmark Data Provider
-----------------------------------
Provides structured, verified evaluation metrics for:
1. Synthetic Benchmark (Phase 1 evaluation: 300 normal IPs, 190 attacker IPs)
2. LANL Real-World Benchmark (Phase 2B evaluation: 21.2M empirical slice, Exp A & Exp B)

Maintains strict separation between operational telemetry and research benchmarks.
"""

SYNTHETIC_BENCHMARK = {
    "title": "Synthetic Evaluation Benchmark (Phase 1 Baseline)",
    "description": "Simulated multi-vector attack scenarios against 300 normal users and 190 simulated attackers.",
    "dataset_type": "Synthetic Simulated Telemetry",
    "sample_counts": {
        "normal_ips": 300,
        "attacker_ips": 190,
        "total_test_ips": 490
    },
    "metrics_comparison": {
        "accuracy": {"ml": 0.965, "rule": 0.835},
        "precision": {"ml": 0.948, "rule": 0.991},
        "recall": {"ml": 0.963, "rule": 0.579},
        "f1_score": {"ml": 0.956, "rule": 0.731},
        "avg_block_attempt": {"ml": 3.6, "rule": 5.0}
    },
    "confusion_matrices": {
        "ml": {"tp": 183, "fn": 7, "fp": 10, "tn": 290},
        "rule": {"tp": 110, "fn": 80, "fp": 1, "tn": 299}
    },
    "attacker_types": [
        {"type": "Fast Brute-Force", "ml_catch_pct": 100.0, "rule_catch_pct": 100.0, "risk": "High Volume"},
        {"type": "Credential Stuffing (multi-user)", "ml_catch_pct": 100.0, "rule_catch_pct": 100.0, "risk": "Distributed"},
        {"type": "Low-and-Slow (12-60s gaps)", "ml_catch_pct": 100.0, "rule_catch_pct": 0.0, "risk": "Stealth Evasion"},
        {"type": "Stealthy (3-4 attempts only)", "ml_catch_pct": 77.0, "rule_catch_pct": 0.0, "risk": "Sub-Threshold"}
    ],
    "normal_false_positives": [
        {"type": "Direct Successful Login", "ml_fp_pct": 0.0, "rule_fp_pct": 0.0},
        {"type": "1-3 Typos Followed by Success", "ml_fp_pct": 0.0, "rule_fp_pct": 0.0},
        {"type": "Forgotten Password (3-8 bad tries)", "ml_fp_pct": 25.0, "rule_fp_pct": 2.0},
        {"type": "Double-Click Rapid Submissions", "ml_fp_pct": 0.0, "rule_fp_pct": 0.0}
    ]
}

LANL_BENCHMARK = {
    "title": "LANL Enterprise Authentication Benchmark (Phase 2B)",
    "description": "Evaluation on Los Alamos National Laboratory Comprehensive Multi-Source Cyber-Security Events (cyber1).",
    "dataset_type": "Empirical Enterprise Active Directory Telemetry (Kerberos / NTLM)",
    "citation": "Alexander D. Kent, LANL (2015), DOI: 10.17021/1179829",
    "approvals": "HSRRB Approval LANL 14-07 X; Public Release Approval LA-UR-15-23810",
    "rights_waiver": "To the extent possible under law, Los Alamos National Laboratory has waived all copyright and related or neighboring rights.",
    "coverage_disclosure": "Days 0 to 2.31 Empirical Slice. 21,255,459 retained authentication events. 10 exact-second red-team matches in slice (739 outside time slice). NOT an interactive web login dataset.",
    "ingestion_audit": {
        "raw_lines_parsed": 37686637,
        "logoff_records_excluded": 16050924,
        "retained_auth_events": 21255459,
        "missing_fields": 0
    },
    "redteam_audit": {
        "total_records_in_artifact": 749,
        "exact_matches_in_slice": 10,
        "match_percentage": 1.34,
        "unmatched_records_out_of_slice": 739,
        "hopcroft_karp_difference": 0
    },
    "experiment_a": {
        "name": "Experiment A: Temporal Generalization",
        "description": "Models trained on partition [0, 3542400) and evaluated on chronologically separated test windows.",
        "models": [
            {
                "model": "One-Class SVM",
                "tp": 2, "fp": 436, "fn": 2, "tn": 29697,
                "precision": 0.0046, "recall": 0.5000, "f1": 0.0090,
                "fpr": 0.0145, "ap": 0.0036, "roc_auc": 0.9382,
                "notes": "Best overall ROC-AUC; lowest false positive rate (1.45%)"
            },
            {
                "model": "Isolation Forest",
                "tp": 3, "fp": 2134, "fn": 1, "tn": 27999,
                "precision": 0.0014, "recall": 0.7500, "f1": 0.0028,
                "fpr": 0.0708, "ap": 0.0023, "roc_auc": 0.8026,
                "notes": "Highest recall (75%); catches 3 of 4 test red-team windows"
            },
            {
                "model": "Random Forest",
                "tp": 1, "fp": 3166, "fn": 3, "tn": 26967,
                "precision": 0.0003, "recall": 0.2500, "f1": 0.0006,
                "fpr": 0.1051, "ap": 0.0008, "roc_auc": 0.8967,
                "notes": "Supervised baseline trained with partition-local ambiguity embargo"
            }
        ]
    },
    "experiment_b": {
        "name": "Experiment B: Unseen-Identity Generalization",
        "description": "Evaluated on source identities never observed during training. Test identities contain solely negative baseline activity.",
        "models": [
            {
                "model": "Isolation Forest",
                "tp": 0, "fp": 597, "fn": 0, "tn": 5983,
                "precision": 0.0, "recall": 0.0, "f1": 0.0,
                "fpr": 0.0907, "ap": None, "roc_auc": None,
                "notes": "ROC-AUC undefined (N/A) for single-class test set per strict protocol"
            },
            {
                "model": "One-Class SVM",
                "tp": 0, "fp": 808, "fn": 0, "tn": 5772,
                "precision": 0.0, "recall": 0.0, "f1": 0.0,
                "fpr": 0.1228, "ap": None, "roc_auc": None,
                "notes": "ROC-AUC undefined (N/A) for single-class test set per strict protocol"
            },
            {
                "model": "Random Forest",
                "tp": 0, "fp": 762, "fn": 0, "tn": 5818,
                "precision": 0.0, "recall": 0.0, "f1": 0.0,
                "fpr": 0.1158, "ap": None, "roc_auc": None,
                "notes": "ROC-AUC undefined (N/A) for single-class test set per strict protocol"
            }
        ]
    },
    "fail2ban_comparison": {
        "total_blocks_triggered": 8921,
        "background_only_blocks": 8921,
        "episode_associated_blocks": 0,
        "episode_coverage_pct": 0.0,
        "low_and_slow_ml_catch_pct": 100.0,
        "low_and_slow_fail2ban_catch_pct": 0.0,
        "finding": "Standard threshold-based counters fail completely on distributed/slow attacks that evade fixed 5-failure windows."
    }
}

def get_benchmarks_data():
    return {
        "synthetic": SYNTHETIC_BENCHMARK,
        "lanl": LANL_BENCHMARK
    }
