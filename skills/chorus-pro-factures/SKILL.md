---
name: chorus-pro-factures
description: Déposer une facture à un acheteur public français (État, collectivité, établissement public) sur Chorus Pro. Extrait les références de facturation du contrat ou du mail de l'acheteur (SIRET, code service, engagement juridique, n° de marché), prépare la facture dans l'outil de facturation, vérifie le Factur-X, remplit le dépôt dans Chorus Pro via le navigateur et contrôle la mise à disposition. À utiliser quand l'utilisateur dit « j'ai une facture à déposer sur Chorus », « on peut facturer [acheteur public] », ou partage un contrat, une convention ou un mail d'acheteur avec ses références de facturation.
---

# Déposer une facture sur Chorus Pro

Chorus Pro est le portail obligatoire pour facturer le secteur public en France. Le dépôt échoue
rarement pour une raison technique, presque toujours pour une référence mal placée : un SIREN à
la place du SIRET, un n° de procédure pris pour un n° de marché, un engagement noyé dans une phrase.
Ce skill sert à placer chaque référence au bon endroit, puis à laisser l'utilisateur appuyer sur envoyer.

## Checklist

- [ ] Références extraites du contrat ou du mail : SIRET acheteur (14 chiffres), code service, n° d'engagement, n° de marché, montant, échéance, conditions préalables, délai de paiement, régime de TVA.
- [ ] Conditions préalables au paiement remplies (réunion de lancement, état des dépenses certifié...). Sinon, le signaler avant de facturer.
- [ ] Facture déjà présente sur Chorus ? Recherche faite avant de déposer.
- [ ] Client créé ou retrouvé avec son SIRET à 14 chiffres.
- [ ] N° d'engagement seul dans le champ bon de commande.
- [ ] Facture en brouillon montrée à l'utilisateur, finalisée seulement après son accord.
- [ ] Structure fournisseur active dans Chorus pour le SIRET émetteur.
- [ ] Factur-X vérifié (`scripts/check_facturx.py`), sinon dépôt en « PDF non signé ».
- [ ] L'utilisateur clique lui-même sur l'envoi final.
- [ ] Suivi des flux « Intégré », puis facture « Mise à disposition du destinataire ».

## Garde-fous

- Aucune facture finalisée sans l'accord explicite de l'utilisateur. Aucun envoi sur Chorus sans son clic final.
- Ne jamais saisir d'identifiant ni de mot de passe : l'utilisateur se connecte lui-même à Chorus Pro et à son outil de facturation.
- Signaler toute condition préalable du contrat qui n'est pas remplie avant de préparer la facture.
- Ne jamais deviner une référence. Si le SIRET, le code service ou l'engagement manque, le demander à l'acheteur (le brouillon de mail est à l'utilisateur d'envoyer).

## Étape 1 : extraire les références de facturation

Le parcours est le même pour toute facture à un acheteur public. Seuls changent le document de
départ et les références qu'il porte :

| Opération | Document de départ | Références habituelles |
|---|---|---|
| Marché public | acte d'engagement, notification, mail de l'acheteur | n° de marché, n° d'engagement, code service |
| Commande hors marché | bon de commande | n° d'engagement (souvent le n° du bon de commande), code service |
| Subvention | convention, arrêté attributif | n° de convention, n° d'engagement si l'organisme en donne un |
| Prestation ponctuelle | devis accepté, mail de commande | ce que l'acheteur indique ; à défaut, le demander |
| Avoir | facture d'origine | mêmes références que la facture qu'il corrige |

Pour savoir si le code service et le n° d'engagement sont obligatoires, ne pas deviner : la fiche
du destinataire dans l'annuaire de Chorus Pro l'indique. La consulter dès cette étape.

Lire le document de départ et en tirer :

| Référence | Ce qu'il faut vérifier |
|---|---|
| SIRET du destinataire | 14 chiffres, pas le SIREN à 9 chiffres. Contrôler la clé (algorithme de Luhn) : une faute de frappe est fréquente. |
| Code service | Exigé ou non selon l'acheteur. Chorus l'indique à la recherche du destinataire. |
| N° d'engagement juridique | Souvent obligatoire pour l'État et nombre d'établissements publics. Il figure sur le bon de commande ou dans le mail de l'acheteur. |
| N° de marché | Seulement s'il y a un marché. Ne pas le confondre avec le n° de procédure : un acheteur peut écrire « procédure 26MAP04, marché 26MRL12 », et seul le second va dans le champ marché. |
| Montant et échéancier | Avance, acomptes, solde : facturer seulement la tranche due. |
| Conditions préalables | Réunion de lancement tenue, rapport remis, état des dépenses certifié par l'expert-comptable, service fait constaté... |
| Délai de paiement | En général 30 jours pour l'État et les collectivités ; vérifier le contrat. |
| Régime de TVA | Voir ci-dessous. |

**TVA.** Une subvention sans contrepartie directe est hors du champ d'application de la TVA : TVA à 0, avec une mention explicite sur la facture (par exemple « Subvention hors champ d'application de la TVA »). Une prestation de services relève en général de la TVA exigible à l'encaissement ; si l'entreprise a opté pour les débits, la facture porte « Option pour le paiement de la taxe d'après les débits ». En cas de doute, demander à l'utilisateur de confirmer avec son expert-comptable plutôt que trancher.

Résumer les références dans un petit tableau et le faire valider avant d'aller plus loin.

## Étape 2 : préparer la facture

Avec un connecteur de facturation (par exemple Qonto MCP), suivre cet ordre. Avec un autre outil ou un PDF fait à la main, guider l'utilisateur sur les mêmes points.

1. **Chercher le client avant d'en créer un.** Un doublon de client crée des factures mal rattachées.
2. **Le client porte le SIRET à 14 chiffres.** Sans lui, le Factur-X n'identifie l'acheteur que par son SIREN, et Chorus ne sait pas à quelle structure adresser la facture.
3. **Le n° d'engagement va seul dans le champ bon de commande** (`purchase_order` chez Qonto) : `2100045678`, jamais `Engagement 2100045678 - Marché 26MRL12`. C'est ce champ que Chorus lit comme engagement. Le n° de marché, le code service et l'objet vont dans l'en-tête ou les notes.
4. **Libellés** : objet de la prestation, de la commande ou de la convention, tranche facturée, période.
5. **Créer en brouillon**, montrer la facture (client, références, lignes, TVA, total, échéance) et **finaliser seulement après accord**.

## Étape 3 : vérifier la structure fournisseur dans Chorus

- Le SIRET émetteur de la facture doit correspondre à une structure **active** dans Chorus (Gestion des structures).
- Après un transfert de siège ou un changement de SIRET, utiliser « Dupliquer une structure » : la nouvelle structure est créée et l'ancienne désactivée. Le mandat de facturation n'est pas repris.
- Une structure nouvellement créée n'apparaît dans l'espace facturation qu'après une **déconnexion puis une reconnexion**.

## Étape 4 : déposer sur Chorus Pro

L'utilisateur est connecté dans le navigateur que Claude pilote.

1. **Rechercher d'abord** : Factures émises, Rechercher, « Toutes structures ». Si la facture est déjà là, s'arrêter.
2. **Factures émises, Déposer facture.** L'utilisateur sélectionne lui-même le PDF sur son ordinateur : Claude ne peut pas choisir un fichier local.
3. **Ne plus recharger cet onglet ni y naviguer** une fois le fichier choisi : la sélection serait perdue. Toute vérification se fait dans un autre onglet.
4. **Cadre de facturation** : A1 (dépôt par un fournisseur) dans le cas standard.
5. **Choisir le format** :
   - **« PDF/A-3 (Factur-X) », syntaxe CII FACTURX**, seulement si le XML embarqué est propre. Le vérifier avant :
     ```bash
     python3 scripts/check_facturx.py facture.pdf --siret-acheteur 00000006700017 --engagement 2100045678 --service DIR-FINANCES
     ```
     **Attention** : dans ce mode, « Continuer » **envoie** la facture directement, sans écran de relecture. Le dire à l'utilisateur et lui laisser le clic.
   - **Sinon « PDF non signé »**. « Continuer » ouvre un formulaire. Chorus en lit parfois le contenu tout seul, parfois rien. Remplir ou vérifier : destinataire (recherche par SIRET, puis clic sur le résultat), code service (recherche, puis sélection), n° de facture, date, n° d'engagement, n° de marché, type de TVA, mode de règlement, montants HT, TVA et net à payer. Contrôler qu'aucune alerte n'est affichée, puis **s'arrêter** : l'utilisateur clique sur « Valider et envoyer ».
6. **Astuce technique** : les listes déroulantes (format, cadre, structure) se règlent de façon fiable par JavaScript sur les `select` dont l'identifiant commence par `GDP_DepotFacture_`, en déclenchant un événement `change` après avoir fixé la valeur. Les champs destinataire et service sont des recherches à saisie : taper le SIRET ou le code, attendre la liste, cliquer sur le résultat.

## Étape 5 : vérifier

- **Suivi des flux** : le lot passe à « Intégré ». Un rejet donne un motif : le lire, corriger, redéposer.
- **Factures émises, Rechercher** : l'état passe de « Déposée » à « Mise à disposition du destinataire ».
- Noter dans l'outil de facturation la date de dépôt et l'identifiant Chorus, pour les relances.

## Exemples fictifs

Toutes les données ci-dessous sont inventées (les SIRET commencent par des zéros et n'appartiennent à personne).
Le premier cas, un marché, est déroulé en entier ; les deux suivants montrent seulement ce qui change.

Mail reçu de l'acheteur :

> Bonjour, suite à la notification du marché, voici les éléments pour votre facture d'avance de 30 %.
> Procédure 26MAP04, marché n° 26MRL12. Engagement juridique : 2100045678.
> Destinataire : Métropole de Valbrume, SIRET 000 000 067 00017, service DIR-FINANCES.
> Paiement à 30 jours, après la réunion de lancement du 4 novembre.

Références extraites :

| Référence | Valeur |
|---|---|
| Fournisseur | Atelier Nuage SAS, SIRET 00000005900014 |
| Destinataire | Métropole de Valbrume, SIRET 00000006700017 (clé valide) |
| Code service | DIR-FINANCES |
| Engagement juridique | 2100045678 |
| N° de marché | 26MRL12 (26MAP04 est la procédure, il ne va nulle part) |
| Montant | avance de 30 % sur 40 000 € HT, soit 12 000 € HT, TVA 20 % 2 400 €, 14 400 € TTC |
| Condition préalable | réunion de lancement du 4 novembre : facturer après |
| Délai | 30 jours |
| TVA | prestation de services, TVA à l'encaissement |

Facture préparée : client Métropole de Valbrume avec SIRET 00000006700017, bon de commande `2100045678`, en-tête « Marché 26MRL12, service DIR-FINANCES, avance de 30 % ». Brouillon montré, finalisé le 5 novembre après accord.

Contrôle Factur-X : SIRET acheteur, engagement et code service conformes, donc dépôt en PDF/A-3 (Factur-X). Avant de cliquer sur « Continuer », l'utilisateur est prévenu que la facture part immédiatement. Le lendemain, le lot est « Intégré » et la facture « Mise à disposition du destinataire ».

**Une commande hors marché.** Le service culturel de la Métropole de Valbrume envoie un bon de commande n° BC-2026-0815 pour un atelier à 1 800 € HT. L'annuaire Chorus indique « engagement obligatoire » : le n° du bon de commande va seul dans le champ bon de commande, et il n'y a pas de n° de marché à renseigner.

**Une subvention.** L'Agence régionale d'innovation de Valbrume (établissement public, SIRET 00000007500010) verse 50 000 € en deux tranches, la seconde sur état des dépenses certifié par l'expert-comptable. La facture de la première tranche porte TVA 0 et la mention « Subvention hors champ d'application de la TVA », avec le n° de convention dans l'en-tête. La seconde attend l'état certifié.

## Pièges

- **SIREN au lieu du SIRET** sur le client : Chorus ne trouve pas le destinataire du Factur-X.
- **N° de procédure pris pour le n° de marché.** Relire la phrase de l'acheteur.
- **Référence obligatoire supposée au lieu d'être vérifiée.** L'annuaire de Chorus dit, pour chaque destinataire, si le code service et l'engagement sont exigés.
- **Engagement noyé dans une phrase** (« Engagement 2100045678 - Marché 26MRL12 ») : Chorus ne le reconnaît pas.
- **Factur-X : « Continuer » envoie tout de suite.** Pas d'écran de relecture.
- **Recharger l'onglet de dépôt** après avoir choisi le fichier : la sélection est perdue.
- **Structure fournisseur inactive** après un changement de SIRET : dupliquer la structure, puis se déconnecter et se reconnecter.
- **« Saisir facture » (saisie web)** : à éviter. Ce mode exige un mandat de facturation signé en ligne sur la structure, et il crée une seconde facture à côté de celle de l'outil de facturation.
- **Conditions préalables oubliées** : une facture déposée trop tôt est rejetée ou laissée en attente, et le délai de paiement ne court pas.
- **Dépôt en double** : toujours rechercher avant de déposer, « Toutes structures » comprises.
