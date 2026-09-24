# ADR 0004: Verification categories and safety boundary

**Status:** Accepted

## Context
A photograph cannot prove a medicine is genuine or counterfeit. The product must not imply otherwise.

## Decision
Results use only these categories, each with the evidence behind it:
- **Information verified**
- **Potential warning signs**
- **Could not verify**
- **Expiry warning**

Every result includes a disclaimer that it does not prove authenticity. Rules:
- No "fake" or "real" labels based on images alone.
- Extracted text and AI interpretation are stored and displayed separately.
- The system explains instructions already printed on trusted packaging or leaflets. It never invents or alters dosage.
- Unclear input yields "Could not verify" plus a pointer to a pharmacist or official source.
- Consequential actions (e.g. submitting a report) require explicit user confirmation.

## Consequences
- Uncertainty is a first-class output, not an error state.
- Extraction output must be schema-validated; fields the model cannot read are null, not guessed.
