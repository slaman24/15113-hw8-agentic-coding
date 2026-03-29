1. [FAIL] Acceptance criterion 7 (security of login + score history) is only partially met. Password hashing is good, but score secrecy relies on a custom XOR stream with a key stored alongside encrypted data, so anyone with file access can recover scores. This conflicts with the “secure / not easily discoverable” requirement in [SPEC.md](SPEC.md#L93).  
   Evidence: key and ciphertext paths are co-located in [.quiz_data] via constants in [quiz_app.py](quiz_app.py#L20), [quiz_app.py](quiz_app.py#L22), [quiz_app.py](quiz_app.py#L23); key creation/loading in [quiz_app.py](quiz_app.py#L137); encryption method in [quiz_app.py](quiz_app.py#L148); history save/load in [quiz_app.py](quiz_app.py#L158), [quiz_app.py](quiz_app.py#L171).

2. [FAIL] Missing error handling for unreadable question bank file (permissions, I/O failure). The loader catches JSON parse errors but not OSError around file open/read, so the app can crash instead of showing a friendly message.  
   Evidence: file read and exception handling in [quiz_app.py](quiz_app.py#L73) to [quiz_app.py](quiz_app.py#L78).  
   Spec reference: error handling expectations in [SPEC.md](SPEC.md#L59).

3. [PASS] Acceptance criterion 1 is implemented: empty question bank prints a friendly message and exits with status code 1.  
   Evidence: empty checks and SystemExit(1) in [quiz_app.py](quiz_app.py#L80), [quiz_app.py](quiz_app.py#L82), [quiz_app.py](quiz_app.py#L102), [quiz_app.py](quiz_app.py#L104).  
   Spec reference: [SPEC.md](SPEC.md#L87).

4. [PASS] Acceptance criterion 2 is implemented: user selects question count, difficulty, and category filters at round start.  
   Evidence: round config flow in [quiz_app.py](quiz_app.py#L252); question count prompt in [quiz_app.py](quiz_app.py#L426); difficulty prompt in [quiz_app.py](quiz_app.py#L437); category prompt in [quiz_app.py](quiz_app.py#L445); filtering in [quiz_app.py](quiz_app.py#L278).  
   Spec reference: [SPEC.md](SPEC.md#L88).

5. [PASS] Acceptance criterion 3 is implemented: q/Q quit flow with confirmation and Ctrl+C handling are present across input prompts.  
   Evidence: q handling and confirmation in [quiz_app.py](quiz_app.py#L517), [quiz_app.py](quiz_app.py#L527); Ctrl+C handling in [quiz_app.py](quiz_app.py#L513), [quiz_app.py](quiz_app.py#L531).  
   Spec reference: [SPEC.md](SPEC.md#L89).

6. [PASS] Acceptance criterion 4 is implemented: robust input validation and case-insensitive matching for relevant answers.  
   Evidence: multiple choice validation in [quiz_app.py](quiz_app.py#L356); true/false validation in [quiz_app.py](quiz_app.py#L377); short-answer blank retry in [quiz_app.py](quiz_app.py#L396); normalized comparisons via lower() in [quiz_app.py](quiz_app.py#L370), [quiz_app.py](quiz_app.py#L390), [quiz_app.py](quiz_app.py#L402).  
   Spec reference: [SPEC.md](SPEC.md#L90).

7. [PASS] Acceptance criterion 5 is implemented: feedback is optional and influences next question selection while respecting chosen filters.  
   Evidence: optional feedback capture in [quiz_app.py](quiz_app.py#L404); feedback persistence by question/category/difficulty in [quiz_app.py](quiz_app.py#L414); weighted selection using stored feedback in [quiz_app.py](quiz_app.py#L327); filtered pool created before selection in [quiz_app.py](quiz_app.py#L258), [quiz_app.py](quiz_app.py#L278).  
   Spec reference: [SPEC.md](SPEC.md#L91).

8. [PASS] Acceptance criterion 6 is implemented: difficulty-based points plus increasing streak bonus are correctly applied.  
   Evidence: base points map in [quiz_app.py](quiz_app.py#L25); scoring calculation in [quiz_app.py](quiz_app.py#L301).  
   Spec reference: [SPEC.md](SPEC.md#L92).

9. [PASS] Acceptance criterion 8 is implemented: final score, high score, and congratulatory message on new high score are shown and persisted.  
   Evidence: score/high-score output and congratulation in [quiz_app.py](quiz_app.py#L311), [quiz_app.py](quiz_app.py#L313), [quiz_app.py](quiz_app.py#L315); persistence in [quiz_app.py](quiz_app.py#L321).  
   Spec reference: [SPEC.md](SPEC.md#L94).

10. [WARN] Password entry is visible on-screen (plain input), which is a usability and shoulder-surfing security concern for a login flow.  
    Evidence: password prompt uses input via prompt_input in [quiz_app.py](quiz_app.py#L495), [quiz_app.py](quiz_app.py#L512).

11. [WARN] Invalid question objects are silently dropped, and if all are invalid the user gets a generic “empty question bank” message, which can mislead debugging and content maintenance.  
    Evidence: silent continue for malformed records in [quiz_app.py](quiz_app.py#L86) to [quiz_app.py](quiz_app.py#L100); generic empty message in [quiz_app.py](quiz_app.py#L102).

12. [WARN] Code quality: unused import adds noise and suggests missing cleanup.  
    Evidence: unused sys import in [quiz_app.py](quiz_app.py#L10).

Assumptions and scope:

1. This review is static (code/spec inspection); I did not run interactive end-to-end terminal sessions in this pass.
2. Security assessment is based on local-file attacker model implied by the spec’s “not easily discoverable” wording.
