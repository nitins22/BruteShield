# BruteShield — Student Authorship & Academic Defense Review Guide

**Purpose:** This guide prepares the student to review, understand, personalize, and confidently defend the final B.Tech CSE project submission in accordance with institutional academic integrity policies.

---

## 1. Information Requiring Student Input (`[STUDENT INPUT REQUIRED]`)

Before final submission, the student must replace all instances of `[STUDENT INPUT REQUIRED]` across all documents with authentic personal details:

| Placeholder Field | Description | Where It Appears |
|---|---|---|
| **Student Name(s)** | Full legal name as registered with the university | Cover pages, declarations, certificates, research paper author list, slide 1 |
| **University Roll / Enrollment No.** | Official university examination roll number | Cover pages, student declaration |
| **Department & Institution** | Department of Computer Science & Engineering, ABES Engineering College | Cover pages, letterheads |
| **Faculty Guide / Supervisor Name** | Full academic title, name, and designation (e.g., *Dr. / Prof. XYZ*) | Certificate page, acknowledgements, research paper advisor footnote |
| **Head of Department (HOD) Name** | Department Chair / HOD name and designation | Certificate template |
| **Project Coordinator Name** | Capstone / Major Project Committee Coordinator | Certificate template |
| **Date of Final Submission** | Actual date of presentation / submission | Declaration, certificate, report front matter |

> [!CAUTION]
> Never invent or fabricate faculty names, signatures, department stamps, or institutional certificates. If any approval is pending, leave the placeholder until formal signatures are obtained.

---

## 2. Mathematical Equations the Student Must Be Prepared to Derive / Explain

During viva voce examination, examiners frequently ask students to write or explain key mathematical formulas on a whiteboard. The student must understand these three core equations:

### Equation 1: Shannon Information Entropy
$$H(X) = -\sum_{i=1}^{n} p(x_i) \log_2 p(x_i)$$
- **What it is:** Measures the average information content / randomness of character distribution in bits per character.
- **How to explain:** If a password of length $L$ repeats the same character (`aaaa`), probability $p('a') = 1$, and $\log_2(1) = 0$, so entropy is $0$ bits. If all 95 printable ASCII characters are equally likely, $p = 1/95$, and $H \approx 6.57$ bits per character.
- **Where in code:** `bruteshield/security.py:12–35`.

### Equation 2: Isolation Forest Anomaly Score
$$s(x, n) = 2^{-\frac{E(h(x))}{c(n)}}$$
- **What it is:** Normalizes the average path length $h(x)$ across isolation trees against the average path length of an unsuccessful search in a binary search tree of size $n$, denoted $c(n)$:
  $$c(n) = 2\ln(n - 1) + 0.5772156649 - \frac{2(n - 1)}{n}$$
- **How to explain:** If $E(h(x)) \to 0$ (isolated very close to root), $s \to 1$ (strong anomaly). If $E(h(x)) \to n - 1$ (deep in the tree), $s \to 0$ (normal inlier). If $E(h(x)) \to c(n)$, $s \to 0.5$ (no clear anomaly).
- **Where in code:** `bruteshield/ml/engine.py:10–23` and `bruteshield/ml/lanl_pipeline.py:110–113`.

### Equation 3: AES-256-GCM Galois Field Multiplication (GHASH)
$$X_m = \sum_{i=1}^{m} C_i \cdot H^{m - i + 1} \pmod{P(x)}$$
- **What it is:** The polynomial authentication hash computed over ciphertext blocks $C_i$ using the hash subkey $H = E_K(0^{128})$ in the Galois field $\text{GF}(2^{128})$ with irreducible polynomial $P(x) = x^{128} + x^7 + x^2 + x + 1$.
- **How to explain:** Unlike unauthenticated encryption, GHASH generates a 128-bit authentication tag. If an attacker modifies even 1 bit of ciphertext in storage, GHASH recalculation mismatches the tag and Python raises an `InvalidTag` exception.
- **Where in code:** `bruteshield/security.py:141–168`.

---

## 3. Results the Student Must Be Prepared to Defend

Examiners scrutinize anomalous-looking numbers in research tables. The student must defend these specific results:

### Result A: Why is LANL Experiment A Precision so low ($0.0014$)?
- **The Defense:**
  > *"Our evaluation partition contained 30,137 evaluation windows, of which only 4 windows contained red-team attack events (an extreme imbalance ratio of 1 to 7,500). Even with an excellent False Positive Rate of only 7%, 2,134 false alarms were generated. By definition, Precision is $\frac{3}{3 + 2134} = 0.0014$. This proves why high ROC-AUC ($0.8026$) can be deceptive in security monitoring, and why BruteShield uses graduated friction (CAPTCHA challenges) rather than immediate irreversible lockouts."*

### Result B: Why did One-Class SVM achieve higher ROC-AUC ($0.9382$) than Isolation Forest ($0.8026$)?
- **The Defense:**
  > *"One-Class SVM with an RBF kernel fits a tight non-linear hypersphere around the dense cluster of normal authentication traffic. In our empirical slice, normal Active Directory traffic was highly clustered around low attempt rates and low username diversity. One-Class SVM separated this core distribution cleanly, generating only 436 false positives (FPR 1.45%) compared to Isolation Forest's 2,134 false positives (FPR 7.08%). However, Isolation Forest achieved superior recall (75% vs. 50%), catching 3 of the 4 red-team windows."*

### Result C: Why did you not evaluate the full 58 days of LANL?
- **The Defense:**
  > *"The full 58-day LANL dataset is over 120 gigabytes compressed and contains over 1 billion events, which exceeded our allocated university laboratory compute and storage quotas. We strictly evaluated the Days 0 to 2.31 empirical slice ($21.26\text{M}$ records) under the approved research protocol. Rather than fabricating unverified 58-day numbers, we transparently reported the exact empirical coverage observed."*

---

## 4. Institutional AI-Use & Academic Disclosure Checklist

Many universities (including AKTU and affiliated institutions) now require formal disclosure of Generative AI assistance in project reports.

The student must review the following:

- [ ] **Check University Guidelines:** Check whether your college requires an "AI Assistance Disclosure Form" attached to the project report.
- [ ] **State the Scope of AI Assistance Honestly:**
  - *"Generative AI was utilized as an engineering assistant for drafting report layouts, formatting LaTeX equations, structuring viva voce questions, and generating diagram definitions."*
  - *"All core application source code, automated unit tests, cryptographic implementations, and empirical benchmark evaluations were executed, inspected, and verified within the repository environment by the project team."*
- [ ] **Read and Understand the Code:** Do not submit code you cannot explain line-by-line. Review `app.py`, `bruteshield/security.py`, and `bruteshield/ml/engine.py`.
- [ ] **Run the Automated Tests Live:** Before the viva, run `pytest tests/ -v` and make sure you can explain what each of the 75 tests asserts.
- [ ] **Check Diagram Numbering and Captions:** Ensure all 11 diagrams in `docs/final-submission/diagrams/` match the text citations in the report and research paper.

---

## 5. Technical Statements Requiring Student Verification

Review and confirm the following factual statements before submitting:

1. **Model Serialization:** Confirm that `trained_model.pkl` is serialized with Scikit-Learn 1.9.1 / Joblib and loads cleanly at server startup.
2. **Database Mode:** Confirm that SQLite executes in Write-Ahead Logging mode (`PRAGMA journal_mode=WAL;`).
3. **Password Masking:** Confirm that the honeypot table does not contain plaintext passwords by running:
   ```bash
   python -c "import sqlite3; conn=sqlite3.connect('logs/bruteshield.db'); print(conn.execute('SELECT * FROM honeypot_logs LIMIT 5').fetchall())"
   ```
4. **Offline Canvas Visualizations:** Confirm that the SOC Dashboard opens and displays canvas charts without requiring an active internet connection.
