"""Contrôle Factur-X sur des factures fictives. Toutes les données sont inventées."""
import contextlib
import io
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / 'skills' / 'chorus-pro-factures' / 'scripts'))
import check_facturx as cf  # noqa: E402

BUYER, SELLER = '00000006700017', '00000005900014'


def invoice(buyer=BUYER, buyer_scheme='0009', engagement='2100045678', service='DIR-FINANCES',
            base='12000.00', tax='2400.00', total='14400.00', category='S', reason=''):
    reason_xml = f'<ram:ExemptionReason>{reason}</ram:ExemptionReason>' if reason else ''
    eng_xml = f'<ram:BuyerOrderReferencedDocument><ram:IssuerAssignedID>{engagement}</ram:IssuerAssignedID></ram:BuyerOrderReferencedDocument>' if engagement else ''
    svc_xml = f'<ram:BuyerReference>{service}</ram:BuyerReference>' if service else ''
    return f'''<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
  xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
 <rsm:ExchangedDocument><ram:ID>F-2026-0042</ram:ID></rsm:ExchangedDocument>
 <rsm:SupplyChainTradeTransaction>
  <ram:ApplicableHeaderTradeAgreement>
   {svc_xml}
   <ram:SellerTradeParty><ram:Name>Atelier Nuage SAS</ram:Name><ram:GlobalID schemeID="0009">{SELLER}</ram:GlobalID></ram:SellerTradeParty>
   <ram:BuyerTradeParty><ram:Name>Metropole de Valbrume</ram:Name>
     <ram:SpecifiedLegalOrganization><ram:ID schemeID="{buyer_scheme}">{buyer}</ram:ID></ram:SpecifiedLegalOrganization></ram:BuyerTradeParty>
   {eng_xml}
   <ram:ContractReferencedDocument><ram:IssuerAssignedID>26MRL12</ram:IssuerAssignedID></ram:ContractReferencedDocument>
  </ram:ApplicableHeaderTradeAgreement>
  <ram:ApplicableHeaderTradeSettlement>
   <ram:ApplicableTradeTax><ram:CategoryCode>{category}</ram:CategoryCode>{reason_xml}</ram:ApplicableTradeTax>
   <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
    <ram:TaxBasisTotalAmount>{base}</ram:TaxBasisTotalAmount><ram:TaxTotalAmount currencyID="EUR">{tax}</ram:TaxTotalAmount>
    <ram:GrandTotalAmount>{total}</ram:GrandTotalAmount><ram:DuePayableAmount>{total}</ram:DuePayableAmount>
   </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
  </ram:ApplicableHeaderTradeSettlement>
 </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>'''.encode()


def levels(xml, **kw):
    return [lvl for lvl, _ in cf.check(xml, **kw)]


def messages(xml, **kw):
    return ' | '.join(m for _, m in cf.check(xml, **kw))


class Luhn(unittest.TestCase):
    def test_fictitious_sirets_are_valid(self):
        self.assertTrue(cf.luhn(BUYER))
        self.assertTrue(cf.luhn(SELLER))

    def test_typo_is_caught(self):
        self.assertFalse(cf.luhn('00000006700018'))


class Check(unittest.TestCase):
    def test_clean_invoice(self):
        self.assertNotIn('BLOQUANT', levels(invoice(), siret=BUYER, engagement='2100045678', service='DIR-FINANCES'))
        self.assertIn('n° de marché 26MRL12', messages(invoice()))

    def test_siren_only_blocks(self):
        self.assertIn('BLOQUANT', levels(invoice(buyer='000000067', buyer_scheme='0002')))

    def test_bad_siret_key_blocks(self):
        self.assertIn('BLOQUANT', levels(invoice(buyer='00000006700018')))

    def test_engagement_in_a_sentence_blocks(self):
        xml = invoice(engagement='Engagement 2100045678 - Marche 26MRL12')
        self.assertIn('pas propre', messages(xml))
        self.assertIn('BLOQUANT', levels(xml))

    def test_missing_engagement_blocks_only_when_expected(self):
        self.assertNotIn('BLOQUANT', levels(invoice(engagement='')))
        self.assertIn('BLOQUANT', levels(invoice(engagement=''), engagement='2100045678'))

    def test_wrong_service_blocks(self):
        self.assertIn('BLOQUANT', levels(invoice(service='DIR-ACHATS'), service='DIR-FINANCES'))

    def test_totals_must_add_up(self):
        self.assertIn('BLOQUANT', levels(invoice(total='14000.00')))

    def test_out_of_scope_vat_needs_a_reason(self):
        self.assertIn('ATTENTION', levels(invoice(tax='0.00', total='12000.00', category='O')))
        self.assertNotIn('ATTENTION', levels(invoice(tax='0.00', total='12000.00', category='O',
                                                     reason='Subvention hors champ d application de la TVA')))

    def test_no_xml_blocks(self):
        self.assertEqual(levels(None), ['BLOQUANT'])


class Pdf(unittest.TestCase):
    """Le XML embarqué dans un vrai PDF, lu comme le ferait l'utilisateur."""

    def setUp(self):
        try:
            from pypdf import PdfWriter
        except ImportError:
            self.skipTest('pypdf non installé')
        self.tmp = tempfile.mkdtemp()
        self.writer = PdfWriter

    def make_pdf(self, xml, name='factur-x.xml'):
        w = self.writer()
        w.add_blank_page(width=595, height=842)
        if xml is not None:
            w.add_attachment(name, xml)
        p = os.path.join(self.tmp, 'facture.pdf')
        with open(p, 'wb') as f:
            w.write(f)
        return p

    def run_main(self, *args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = cf.main(list(args))
        return code, buf.getvalue()

    def test_clean_pdf_exits_0(self):
        code, out = self.run_main(self.make_pdf(invoice()), '--siret-acheteur', '000 000 067 00017', '--engagement', '2100045678')
        self.assertEqual(code, 0, out)
        self.assertIn('« Continuer » envoie la facture sans relecture', out)

    def test_pdf_without_xml_exits_1(self):
        code, out = self.run_main(self.make_pdf(None))
        self.assertEqual(code, 1)
        self.assertIn('PDF non signé', out)


if __name__ == '__main__':
    unittest.main()
