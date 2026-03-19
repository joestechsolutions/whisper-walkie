# Code Signing Options for Whisper Walkie

## Why Code Signing Matters
Without signing, Windows shows a SmartScreen warning: "Windows protected your PC"
Users must click "More info" > "Run anyway" — this kills conversion for non-technical users.

## Options

### 1. Certum Open Source Code Signing Certificate (RECOMMENDED)
- **Cost:** ~$27/year (for verified open-source developers)
- **Provider:** Certum (Polish CA, globally trusted)
- **Requirements:** Proof of identity + proof of open-source project involvement
- **Process:** Register at certum.store, verify identity, link GitHub repo
- **Hardware:** Requires a cryptographic token (SimplySign cloud or physical card ~$20 one-time)
- **Link:** https://certum.store/open-source-code-signing-code.html

### 2. SignPath Foundation (Free for Open Source)
- **Cost:** Free for qualifying open-source projects
- **Provider:** SignPath (Austrian company)
- **Requirements:** Must apply and be accepted
- **Process:** CI/CD integration — signs artifacts in your GitHub Actions pipeline
- **Link:** https://signpath.org/

### 3. Commercial Certificate (Sectigo/Comodo)
- **Cost:** ~$215/year
- **Provider:** Sectigo via resellers (SignMyCode, CheapSSLWeb)
- **Requirements:** Business verification (EV requires extended validation)
- **Note:** OV certificates still trigger SmartScreen until you build reputation
- **EV certificates** ($350+/year) get immediate SmartScreen trust

## Recommendation
Start with **Certum Open Source** (~$27/year). It's the cheapest legitimate option
and perfectly suited for an MIT-licensed GitHub project. The SmartScreen warning
will gradually disappear as more users download and run the signed exe.

If you want ZERO SmartScreen warnings from day one, you'd need an EV certificate
($350+/year) which is overkill for a free tool at this stage.

## Without Signing (Current State)
The app works perfectly — users just need to click through the SmartScreen warning once.
For technical users (your initial audience), this is a non-issue. Consider signing
only when you want to reach non-technical users at scale.
