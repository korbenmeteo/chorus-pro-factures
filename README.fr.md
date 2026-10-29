# chorus-pro-factures

Un skill Claude pour les entreprises françaises qui facturent le secteur public via Chorus Pro.
[English version](README.md).

Un dépôt sur Chorus Pro échoue rarement pour une raison technique. Il échoue parce qu'une référence
est au mauvais endroit : un SIREN à 9 chiffres là où il faut le SIRET à 14, un n° de procédure pris
pour le n° de marché, un n° d'engagement noyé dans une phrase. J'ai déposé des factures à des
acheteurs publics avec Claude de cette façon, et ce skill reprend ce que cette session nous a
appris, sans aucune de nos données. Il marche de la même façon pour un marché public, un bon de
commande, une subvention ou une prestation ponctuelle.

## Ce qu'il fait

1. **Extrait les références de facturation** du document de départ (marché, bon de commande, convention ou mail de l'acheteur) : SIRET (avec contrôle de la clé), code service, n° d'engagement juridique, n° de marché, échéancier, conditions préalables au paiement, délai de paiement, régime de TVA.
2. **Prépare la facture** dans l'outil de facturation. Avec un connecteur (Qonto MCP par exemple), Claude crée le brouillon ; sinon, il indique quel champ reçoit quelle référence. Rien n'est finalisé sans ton accord.
3. **Vérifie le XML Factur-X** embarqué dans le PDF (`scripts/check_facturx.py`) avant un dépôt en mode Factur-X, où Chorus envoie la facture dès le clic sur « Continuer », sans relecture.
4. **Remplit le formulaire de dépôt** dans le navigateur piloté par Claude et s'arrête avant l'envoi : c'est toi qui cliques.
5. **Contrôle le résultat** : lot « Intégré », facture « Mise à disposition du destinataire ».

## Ce qu'il ne fait pas

- Se connecter à ta place ou manipuler tes identifiants.
- Envoyer une facture : le dernier clic t'appartient.
- Trancher ton régime de TVA. Il signale les cas courants (subvention hors champ, prestation de services à l'encaissement) et renvoie à l'expert-comptable en cas de doute.

## Prérequis

- Claude avec un navigateur qu'il pilote (Claude in Chrome, ou le navigateur de l'app Claude), et ta session Chorus Pro ouverte.
- En option : un connecteur vers ton outil de facturation.
- Pour le contrôle Factur-X : Python 3.10+ et `pip install pypdf`.

## Installation

```
/plugin marketplace add korbenmeteo/chorus-pro-factures
/plugin install chorus-pro-factures@chorus-pro-factures
```

Ou copier `skills/chorus-pro-factures/` dans `~/.claude/skills/`.

## Auteur

Ruben Hallali ([@RubenHallali](https://x.com/RubenHallali)). Je construis mes outils en public ;
issues et pull requests bienvenues.

## Licence

MIT
