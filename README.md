# AI Ransomware Symptom Learning and Response System

This project builds a symptom-based AI ransomware response system.

The system does not execute real ransomware. It learns ransomware-like symptoms from datasets and safe simulations, then recommends suitable defensive actions.

## Core idea

Instead of only detecting "ransomware or benign", the system learns symptoms such as:

- file write burst
- file rename burst
- high entropy write
- mass file modification
- suspicious extension change
- ransom note creation
- backup disable attempt
- shadow copy deletion attempt
- C2 beaconing
- suspicious DNS
- packed binary
- crypto API usage
- anti-analysis behavior

When new behavior is observed, the system compares its symptoms with learned labels and recommends defensive responses.

If behavior is unknown but high-risk, the system enters Protective Lockdown Mode:

- emergency backup
- temporary file protection
- endpoint isolation recommendation
- evidence collection
- analyst review queue
- retraining queue

## Safety

No real ransomware is executed. All demos use controlled folders:

- data/live_watch
- data/protected_docs
- data/emergency_backup
- data/quarantine
- data/unknown_cases
