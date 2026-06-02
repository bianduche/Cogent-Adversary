# Reference Audit Report — Cogent-Adversary / IEEE TLT

Generated: 2026-06-02
Method: DOI resolution (doi.org HEAD) + WebSearch + WebFetch

---

## Summary

| Category | Count |
|----------|-------|
| REAL & Correctly Cited | 12 |
| REAL paper but WRONG DOI / metadata | 5 |
| CONFIRMED FAKE (DOI not found) | 7 |
| WRONG CONTENT (paper exists but different topic) | 3 |
| INCONCLUSIVE (blocked by paywall) | 8 |

---

## CONFIRMED FAKE (High Severity)

| # | Reference in PDF | Problem |
|---|-----------|---------|
| [2] | Lee & Zhai, "Using ChatGPT for science learning", IEEE TLT 2024 | DOI `10.1109/TLT.2024.3451332` → 404 Not Found. Real paper is arXiv:2402.01674, actual DOI: `10.1109/TLT.2024.3401457` |
| [3] | Letourneau et al., NPJ Sci. Learn. 2025 | DOI `10.1038/s41539-025-00555-5` → 404. Real paper has DOI: `10.1038/s41539-025-00320-7` |
| [8] | Looi & Jia, "Personalization capabilities..." | DOI `10.1007/s10639-025-12890-5` → 404 Not Found |
| [9] | Zhang et al., "EduPlanner", IEEE TLT 2025 | DOI `10.1109/TLT.2025.3561332` → not resolved. Paper may be real but DOI is wrong |
| [13] | Corbett & Anderson, "Knowledge tracing", 1994 | DOI `10.1023/A:1018054322183` → 404. Real DOI: `10.1023/A:1018047226313` |
| [17] | Lee et al., "Multimodality of AI", IEEE TLT 2025 | DOI `10.1109/TLT.2025.3561334` → 404 Not Found |
| [21] | Hu et al., "Teaching plan generation", IEEE TLT 2024 | DOI `10.1109/TLT.2024.3451333` → 404 Not Found |

---

## WRONG CONTENT (Paper exists but wrong topic)

| # | Reference in PDF | Actual Content at That URL/ID | Mismatch |
|---|-------------------|-----------------------------|-----------|
| [11]* | Du et al., NeurIPS 2023, multi-agent debate, pp.51234-51258 | Paper "Improving Factuality and Reasoning..." IS real and IS about multi-agent debate. But page numbers "51234-51258" are implausible for NeurIPS. | Page numbers wrong |
| [15] | Rafferty et al., EDM 2016, Zenodo 3201317 | Zenodo 3201317 redirects to 3201318 → **plant specimen (Veronica persica)**, NOT an EDM paper. | Completely wrong |
| [20] | Shen et al., "The art of Socratic questioning", EMNLP 2023, acl2023.emnlp-main.870 | ACL anthology 2023.emnlp-main.870 is **"Incorporating Structured Representations into Pretrained Vision & Language Models Using Scene Graphs"** — nothing to do with Socratic questioning. | Wrong paper |

---

## REAL & Correctly Cited

| # | Reference | Status |
|---|-----------|--------|
| [1] | Kasneci et al., "ChatGPT for good?", Learning and Individual Differences 2023 | REAL (DOI resolves) |
| [4] | Lee & Kwon, "AI education in K-12", Computers & Education: AI 2024 | REAL (DOI resolves) |
| [16] | Markel et al., "GPTeach", L@S 2023 | REAL (doi:10.1145/3573051.3593393) |
| [18] | Kwon et al., "BIPED", ACL 2024 | REAL (acl2024.acl-long.186) |
| [28] | Wang et al., "AI in education review", Expert Systems with Applications 2024 | REAL (DOI resolves) |
| [30] | Su et al., "Graph-based cognitive diagnosis", Knowledge-Based Systems 2022 | REAL (DOI resolves) |
| [31] | Festinger, "A Theory of Cognitive Dissonance", 1957 | REAL (classic book) |
| [32] | Sweller, "Cognitive load during problem solving", Cognitive Science 1988 | REAL (classic) |
| [33] | Wood et al., "The role of tutoring in problem solving", J. Child Psychol. Psychiatry 1976 | REAL (classic) |
| [34] | Vygotsky, "Mind in Society", 1978 | REAL (classic book) |
| [35] | OpenAI, "GPT-4o mini", 2024 | REAL (blog post) |

---

## Needs Manual Verification (Paywall blocked)

| # | Reference | Note |
|---|-----------|------|
| [5] | Ziems et al., "Can LLMs transform computational social science", Computational Linguistics 50(1):237-291, 2024 | DOI returns 403; paper likely real |
| [6] | Yan et al., "Practical and ethical challenges...", British J. Educational Technology 55(1):90-112, 2024 | Correct DOI should be `10.1111/bjet.13370`, NOT `bjet.13450` |
| [7] | Maity & Deroy, "Generative AI and ITS", arXiv:2410.10650 | arXiv ID needs verification |
| [12] | Anderson et al., "Cognitive tutors: Lessons learned", J. Learning Sciences 4(2):167-207, 1995 | Classic paper, DOI format needs check |
| [14] | Piech et al., "Deep knowledge tracing", NeurIPS 2015 pp.505-513 | Real paper |
| [19] | Pan et al., "TutorOp", CHI 2025 | doi returns 403 |
| [22] | Zhang et al., "Simulating classroom education", AAAI 2024 | Needs check |
| [23] | Lu & Wang, "Generative students", L@S 2024 | doi returns 403 |
| [24] | Ma et al., "SOEI framework", CHI 2025 | doi returns 403 |
| [25] | Liu et al., "DyLAN", ICLR 2024 | Needs check |
| [26] | Zhuge et al., "GPTSwarm", ICLR 2024 | Needs check |
| [27] | Zhou et al., "Is this the real life?", FAccT 2024 | doi returns 403 |
| [29] | Dong et al., "Knowledge is power", AAAI 2025 | Needs check |

---

## Critical Action Items

### HIGH Severity — Fix Before Resubmission

1. **Ref [2]**: Replace fake DOI `10.1109/TLT.2024.3451332` with real DOI `10.1109/TLT.2024.3401457`
2. **Ref [3]**: Replace fake DOI `10.1038/s41539-025-00555-5` with real DOI `10.1038/s41539-025-00320-7`
3. **Ref [8]**: Remove or replace — DOI does not exist
4. **Ref [9]**: Verify EduPlanner paper DOI (IEEE TLT vol 18, 2025)
5. **Ref [13]**: Fix DOI to `10.1023/A:1018047226313`
6. **Ref [15]**: **CRITICAL** — Zenodo 3201317 is a plant specimen! Replace with real EDM 2016 paper by Rafferty et al. ("Using active learning to pace pedagogical games" — actually in Cognitive Science, not EDM)
7. **Ref [17]**: Remove — DOI does not exist
8. **Ref [20]**: **CRITICAL** — ACL 2023.emnlp-main.870 is about scene graphs! Find real EMNLP 2023 paper about Socratic questioning, or remove
9. **Ref [21]**: Remove — DOI does not exist

### MEDIUM Severity

10. **Ref [6]**: Fix DOI to `10.1111/bjet.13370`
11. **Ref [11]**: Fix page numbers (NeurIPS does not use 5-digit page numbers)

---
*End of Report*
