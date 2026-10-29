#!/usr/bin/env python3
"""Vérifie le XML Factur-X embarqué dans une facture PDF avant un dépôt sur Chorus Pro.

En mode « PDF/A-3 (Factur-X) », Chorus envoie la facture dès le clic sur « Continuer », sans relecture :
ce contrôle dit si le XML est assez propre pour ce mode, ou s'il faut déposer en « PDF non signé ».

Usage :
  python3 check_facturx.py facture.pdf [--siret-acheteur 14CHIFFRES] [--engagement N] [--service CODE]
  python3 check_facturx.py factur-x.xml ...      (le XML seul, sans pypdf)

Lire un PDF demande pypdf (pip install pypdf). Code de sortie : 0 si le Factur-X est utilisable, 1 sinon.
"""
import argparse
import re
import sys
import xml.etree.ElementTree as ET
from decimal import Decimal, InvalidOperation

NS = {
    'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
    'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
}
XML_NAMES = ('factur-x.xml', 'zugferd-invoice.xml', 'xrechnung.xml')
AGREEMENT = 'rsm:SupplyChainTradeTransaction/ram:ApplicableHeaderTradeAgreement'
SETTLEMENT = 'rsm:SupplyChainTradeTransaction/ram:ApplicableHeaderTradeSettlement'


def luhn(digits):
    """Clé de contrôle des SIREN et SIRET. Exception : les établissements de La Poste (SIREN 356000000)."""
    if digits.startswith('356000000'):
        return sum(int(c) for c in digits) % 5 == 0
    total = 0
    for i, c in enumerate(reversed(digits)):
        d = int(c) * (2 if i % 2 else 1)
        total += d - 9 if d > 9 else d
    return total % 10 == 0


def read_xml(path):
    if path.lower().endswith('.xml'):
        with open(path, 'rb') as f:
            return f.read()
    try:
        from pypdf import PdfReader
    except ImportError:
        sys.exit('pypdf est nécessaire pour lire un PDF : pip install pypdf')
    attachments = PdfReader(path).attachments
    for name in attachments:
        if name.lower() in XML_NAMES:
            return attachments[name][0]
    return None


def siret_of(party):
    """Le SIRET (schéma 0009) d'une partie, en identifiant global ou en identifiant légal."""
    if party is None:
        return None
    for el in party.findall('ram:GlobalID', NS) + party.findall('ram:SpecifiedLegalOrganization/ram:ID', NS):
        value = re.sub(r'\s', '', el.text or '')
        if el.get('schemeID') == '0009' or len(value) == 14:
            return value
    return None


def amount(root, tag):
    el = root.find(f'{SETTLEMENT}/ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:{tag}', NS)
    try:
        return Decimal(el.text.strip()) if el is not None and el.text else None
    except InvalidOperation:
        return None


def check(xml_bytes, siret=None, engagement=None, service=None):
    """Retourne une liste de (niveau, message). Niveaux : BLOQUANT, ATTENTION, OK."""
    out = []
    if xml_bytes is None:
        return [('BLOQUANT', "aucun XML Factur-X embarqué dans le PDF : déposer en « PDF non signé »")]
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        return [('BLOQUANT', f'XML illisible ({e})')]
    agreement = root.find(AGREEMENT, NS)
    if agreement is None:
        return [('BLOQUANT', "pas de bloc ApplicableHeaderTradeAgreement : ce n'est pas un Factur-X CII")]

    number = root.findtext('rsm:ExchangedDocument/ram:ID', default='', namespaces=NS).strip()
    out.append(('OK', f'facture n° {number}') if number else ('BLOQUANT', 'numéro de facture absent'))

    buyer = siret_of(agreement.find('ram:BuyerTradeParty', NS))
    if not buyer:
        out.append(('BLOQUANT', "SIRET de l'acheteur absent (seulement un SIREN ?) : Chorus ne saura pas à qui adresser la facture"))
    elif not re.fullmatch(r'\d{14}', buyer) or not luhn(buyer):
        out.append(('BLOQUANT', f"SIRET de l'acheteur invalide : {buyer}"))
    elif siret and buyer != re.sub(r'\s', '', siret):
        out.append(('BLOQUANT', f"SIRET de l'acheteur {buyer} différent de celui attendu {siret}"))
    else:
        out.append(('OK', f"SIRET de l'acheteur {buyer}"))

    seller = siret_of(agreement.find('ram:SellerTradeParty', NS))
    out.append(('OK', f'SIRET du fournisseur {seller}') if seller else
               ('ATTENTION', 'SIRET du fournisseur absent : vérifier que la structure Chorus correspond bien'))

    eng = agreement.findtext('ram:BuyerOrderReferencedDocument/ram:IssuerAssignedID', default='', namespaces=NS).strip()
    if not eng:
        out.append(('BLOQUANT' if engagement else 'ATTENTION', "n° d'engagement absent (champ bon de commande)"))
    elif not re.fullmatch(r'[A-Za-z0-9._/-]{1,50}', eng) or re.search(r'engag|march', eng, re.I):
        out.append(('BLOQUANT', f"n° d'engagement pas propre : « {eng} ». Le champ doit contenir le numéro seul"))
    elif engagement and eng != engagement.strip():
        out.append(('BLOQUANT', f"n° d'engagement {eng} différent de celui attendu {engagement}"))
    else:
        out.append(('OK', f"n° d'engagement {eng}"))

    svc = agreement.findtext('ram:BuyerReference', default='', namespaces=NS).strip()
    if service and svc != service.strip():
        out.append(('BLOQUANT', f'code service « {svc or "absent"} » différent de celui attendu {service}'))
    else:
        out.append(('OK', f'code service {svc}') if svc else ('ATTENTION', 'pas de code service : vérifier que cet acheteur ne l\'exige pas'))

    contract = agreement.findtext('ram:ContractReferencedDocument/ram:IssuerAssignedID', default='', namespaces=NS).strip()
    if contract:
        out.append(('OK', f'n° de marché {contract}'))

    base, tax, total = amount(root, 'TaxBasisTotalAmount'), amount(root, 'TaxTotalAmount'), amount(root, 'GrandTotalAmount')
    if base is None or tax is None or total is None:
        out.append(('BLOQUANT', 'montants HT, TVA ou TTC absents'))
    elif abs(base + tax - total) > Decimal('0.01'):
        out.append(('BLOQUANT', f'HT {base} + TVA {tax} ≠ TTC {total}'))
    else:
        out.append(('OK', f'montants HT {base}, TVA {tax}, TTC {total}'))

    for t in root.findall(f'{SETTLEMENT}/ram:ApplicableTradeTax', NS):
        cat = t.findtext('ram:CategoryCode', default='', namespaces=NS)
        if cat in ('O', 'E') and not (t.findtext('ram:ExemptionReason', namespaces=NS) or '').strip():
            out.append(('ATTENTION', f'TVA catégorie {cat} sans mention d\'exonération (ExemptionReason)'))
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('fichier')
    ap.add_argument('--siret-acheteur')
    ap.add_argument('--engagement')
    ap.add_argument('--service')
    a = ap.parse_args(argv)
    results = check(read_xml(a.fichier), a.siret_acheteur, a.engagement, a.service)
    for level, msg in results:
        print(f'{level:9} {msg}')
    blocking = any(level == 'BLOQUANT' for level, _ in results)
    print('\n' + ('Déposer en « PDF non signé » et compléter le formulaire Chorus.' if blocking else
                  'Factur-X utilisable. Rappel : en mode Factur-X, « Continuer » envoie la facture sans relecture.'))
    return 1 if blocking else 0


if __name__ == '__main__':
    sys.exit(main())
