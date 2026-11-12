# BruteShield — Real-World Enterprise Authentication Benchmark Evaluation Report
**Dataset:** Los Alamos National Laboratory (LANL) Comprehensive Multi-Source Cyber-Security Events (`cyber1`)
**Author:** BruteShield Research & Engineering Team
**Generated:** 2026-11-12 14:29:03 UTC
**Evaluation Protocol:** Approved Phase 2A Version 3.6 Specification

## 1. Executive Summary & Verification Safeguards
- **Benchmark Philosophy:** Evaluates BruteShield's 6 behavioral anomaly features against real enterprise Active Directory authentication telemetry.
- **Safety Guarantee:** Legacy prototype model `trained_model.pkl` is **completely preserved and untouched**. Experimental models are exported separately as `trained_model_real_expA.pkl` and `trained_model_real_expB.pkl`.
- **Test Integrity:** All 14 original Phase 1 automated tests remain 100% green.
- **Scope Disclosure:** Measures enterprise Active Directory authentication behavior (including Kerberos ticket requests), not exclusively interactive web logins.

## 2. LANL Dataset Metadata & Verbatim Rights Waiver
- **DOI / Citation:** Alexander D. Kent, *Comprehensive, Multi-Source Cyber-Security Events*, Los Alamos National Laboratory, DOI: [10.17021/1179829](http://dx.doi.org/10.17021/1179829), 2015.
- **Approvals:** LANL Human Subject Research Review Board (Approval **LANL 14-07 X**); Public Release (Approval **LA-UR-15-23810**).
> *"To the extent possible under law, Los Alamos National Laboratory has waived all copyright and related or neighboring rights to Comprehensive, Multi-Source Cyber-Security Events. This work is published from: United States."*

## 3. Data Quality & Ingestion Audit
| Metric | Observed Value | Description |
|---|---|---|
| **Raw Lines Parsed** | `37,686,637` | Verified by ingestion parser |
| **Missing Source Computer ('?')** | `0` | Verified by ingestion parser |
| **Missing Source User ('?')** | `0` | Verified by ingestion parser |
| **Missing Destination User ('?')** | `0` | Verified by ingestion parser |
| **Missing Destination Computer ('?')** | `0` | Verified by ingestion parser |
| **Unknown Status ('?')** | `0` | Verified by ingestion parser |
| **Unknown Orientation ('?')** | `0` | Verified by ingestion parser |
| **Excluded LogOff Records** | `16,050,924` | Verified by ingestion parser |
| **Retained E_observed Records** | `21,255,459` | Verified by ingestion parser |
| **Invalid Red-Team Records** | `0` | Verified by ingestion parser |

## 4. Red-Team Ground-Truth Matching Audit
| Metric | Count | Percentage | Matching Protocol |
|---|---|---|---|
| **Total Red-Team Records in Artifact** | `749` | 100.0% | Official `redteam.txt.gz` |
| **Exact Second Matches ($\Delta\tau = 0$)** | `10` | `1.34%` | Greedy 1-to-1 matching |
| **Tolerance Matches ($0 < |\Delta\tau| \le 2\text{s}$)** | `0` | `0.00%` | Mutually exclusive secondary pass |
| **Unmatched Red-Team Records** | `739` | `98.66%` | Projected into ambiguity exclusion intervals |
| **Ambiguous Candidate Instances** | `0` | — | Deterministic tie-breaker resolved |
| **Diagnostic Hopcroft–Karp Difference** | `+0` | — | $\vert M_{\text{bipartite}}\vert - \vert M_{\text{greedy}}\vert$ |

## 5. Episode Construction & Censoring Audit
| Episode Classification | Count | Definition & Inclusion Status |
|---|---|---|
| **Completed Episodes** | `0` | Evaluated strictly according to Section 4.2 |
| **Left-Censored Episodes** | `0` | Evaluated strictly according to Section 4.2 |
| **Right-Censored Episodes** | `0` | Evaluated strictly according to Section 4.2 |
| **Boundary-Crossing Episodes** | `1` | Evaluated strictly according to Section 4.2 |
| **Embargo-Affected Episodes** | `0` | Evaluated strictly according to Section 4.2 |

## 6. Experiment A: Temporal Generalization Performance
| Model Architecture | TP | FP | FN | TN | Precision | Recall | F1-Score | Active-Window FPR | Average Precision (AP) | ROC-AUC |
|---|---|---|---|---|---|---|---|---|---|---|
| **Isolation Forest** | `3` | `2134` | `1` | `27999` | `0.0014` | `0.75` | `0.0028` | `0.0708` | `0.0023` | `0.8026` |
| **One-Class SVM** | `2` | `436` | `2` | `29697` | `0.0046` | `0.5` | `0.009` | `0.0145` | `0.0036` | `0.9382` |
| **Random Forest** | `1` | `3166` | `3` | `26967` | `0.0003` | `0.25` | `0.0006` | `0.1051` | `0.0008` | `0.8967` |

## 7. Experiment B: Unseen-Identity Generalization Performance
| Model Architecture | TP | FP | FN | TN | Precision | Recall | F1-Score | Active-Window FPR | Average Precision (AP) | ROC-AUC |
|---|---|---|---|---|---|---|---|---|---|---|
| **Isolation Forest** | `0` | `597` | `0` | `5983` | `0.0` | `0.0` | `0.0` | `0.0907` | `N/A` | `N/A` |
| **One-Class SVM** | `0` | `808` | `0` | `5772` | `0.0` | `0.0` | `0.0` | `0.1228` | `N/A` | `N/A` |
| **Random Forest** | `0` | `762` | `0` | `5818` | `0.0` | `0.0` | `0.0` | `0.1158` | `N/A` | `N/A` |

## 8. Custom Fail2ban-Style Baseline & Low-and-Slow Attack Evaluation
### Custom Fail2ban State Machine Telemetry
- **Total Blocks Triggered:** `8921`
- **Episode-Only Blocks (5/5):** `0`
- **Mixed Blocks (1–4/5):** `0`
- **Background-Only Blocks (0/5):** `8921`
- **Metric A (Episode Protection / Coverage):** `0.00%`
- **Metric B (Episode-Associated Block Trigger):** `0.00%`

### LANL-Observed Marker-Bounded Low-and-Slow Proxies
- **Identified Proxy Episodes:** `1`
- **BruteShield ML Anomaly Catch Rate:** `100.00%`
- **Custom Fail2ban Direct Catch Rate:** `0.00%` (Mathematically zero for unmixed attack failures due to invariant)
