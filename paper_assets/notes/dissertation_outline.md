# Dissertation Outline (12,000 words target)

1. Abstract (250)
2. Introduction (900-1200)
   - Problem, motivation, contributions
3. Background / Related Work (1800-2200)
   - Smart grids / ICS security basics
   - DDoS/flooding concepts, auth abuse
   - Defensive strategies (rate limiting, anomaly blocking)
4. System Design (1200-1600)
   - Unity simulation, WebGL delivery
   - Django ASGI + Channels + Redis
   - Nginx front + JWT auth
5. Methodology (1800-2200)
   - Experiment harness (Step 7)
   - Metrics (Step 6)
   - Threat model + scenarios (baseline, jwt mixed, login storm)
6. Implementation (1200-1600)
   - Throttles (DRF scopes)
   - Edge limits (Nginx zones)
   - Abuse blocklist middleware
7. Results (1800-2200)
   - Use results_summary.xlsx tables
   - Use generated charts + Grafana screenshots
8. Discussion (800-1200)
   - Tradeoffs: UX vs strict limiting
   - Where defenses work, where they fail
9. Conclusion & Future Work (600-900)
10. References
11. Appendices
   - Config snapshots, run folders, scripts list

Figures/Tables: use paper_assets/WRITEUP_PACK.md as checklist.
