# Boundary and privacy

This file is a hard dependency. Every script that reads or writes the vault
refuses to run without it.

## Never, under any input

- Diagnose, or name a likely condition for a person
- Calculate, adjust or recommend a dose
- Triage downward — say care is not needed, or that something is not serious
- Prognose an individual
- Recommend, sequence, start, stop or modify treatment
- Answer whether an insurer will pay
- Correct a treating clinician

**May escalate. Never de-escalate.** Over-referring wastes an appointment;
under-referring can kill. No code path may say care is not needed.

## Privacy

1. The vault is local. Never synced, never committed, never moved into a repo.
2. Encrypted at rest with DPAPI bound to the current Windows user.
3. **Scripts print counts and IDs, never record content.** A script that would
   echo a medication name is a defect.
4. Search terms are de-identified before leaving. Personal detail appears only
   when the clinical question requires it.
5. No third-party service enters the loop.
6. Reports carry no identifiers and have a stated retention.
7. The emergency card is the one deliberate exception, because in an emergency
   this is what someone needs.
8. Deletion is real: removing an entry removes it, not just a view.

## What this skill is not

Information and preparation, never clinical judgement. Every conclusion that
depends on examining a person belongs to a clinician.
