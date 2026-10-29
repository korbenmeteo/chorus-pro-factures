# chorus-pro-factures

A Claude skill for French companies that invoice the public sector through Chorus Pro, the
government's mandatory e-invoicing portal. [Version française](README.fr.md).

Filing on Chorus Pro rarely fails for technical reasons. It fails because a reference sits in the
wrong place: a 9-digit SIREN where the 14-digit SIRET belongs, a tender procedure number taken for
the contract number, a commitment number buried in a sentence. I filed invoices to French public
buyers with Claude this way, and this skill is what that session taught us, without any of our data.
It works the same for a public contract, a purchase order, a grant or a one-off service.

## What it does

1. **Extracts the billing references** from whatever started it (a public contract, a purchase order, a grant agreement or the buyer's email): buyer SIRET (checked with its Luhn key), service code, legal commitment number, contract number, instalments, preconditions for payment, payment term, VAT treatment.
2. **Prepares the invoice** in your invoicing tool. With a connector (Qonto MCP, for example) Claude drafts it; otherwise it tells you exactly which field gets which reference. Nothing is finalised without your yes.
3. **Checks the Factur-X XML** embedded in the PDF (`scripts/check_facturx.py`) before filing in Factur-X mode, where Chorus sends the invoice the moment you press "Continuer", with no review screen.
4. **Fills the Chorus Pro filing form** in the browser Claude drives, and stops before the final send: you click it.
5. **Checks the result**: the batch reaches "Intégré", the invoice reaches "Mise à disposition du destinataire".

## What it does not do

- Log in for you, or touch your credentials.
- Send an invoice. You press the last button.
- Decide your VAT treatment. It flags the usual cases (an out-of-scope grant, services taxed on receipt) and asks you to confirm with your accountant when in doubt.

## Requirements

- Claude with a browser it can drive (Claude in Chrome, or the Claude desktop app's browser), and you logged in to Chorus Pro.
- Optional: a connector to your invoicing tool.
- For the Factur-X check: Python 3.10+ and `pip install pypdf`.

## Install

```
/plugin marketplace add korbenmeteo/chorus-pro-factures
/plugin install chorus-pro-factures@chorus-pro-factures
```

Or copy `skills/chorus-pro-factures/` into `~/.claude/skills/`.

Check an invoice by hand:

```bash
python3 skills/chorus-pro-factures/scripts/check_facturx.py invoice.pdf \
  --siret-acheteur 00000006700017 --engagement 2100045678 --service DIR-FINANCES
```

## The traps it knows

- The buyer must carry its 14-digit SIRET, or the Factur-X names only a SIREN and Chorus cannot route it.
- The commitment number goes alone in the purchase order field, never "Commitment 2100045678 - Contract X".
- In Factur-X mode, "Continuer" sends the invoice. In plain PDF mode, it opens a form to complete.
- Reloading the filing tab after choosing the file loses the file.
- After a change of registered office, duplicate the supplier structure, then log out and back in before it shows up.
- Avoid "Saisir facture": it needs an online billing mandate and creates a second invoice beside your own.

## Tests

```bash
python3 -m unittest discover -s tests
```

All data in the skill and the tests is invented. The example SIRETs start with zeros and belong to no one.

## Author

Built by Ruben Hallali ([@RubenHallali](https://x.com/RubenHallali)). I am building my own
tooling in public; issues and pull requests are welcome.

## Licence

MIT
