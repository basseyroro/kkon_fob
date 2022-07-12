from odoo import api, fields, models


class WBRequestRegistration(models.Model):
    _name = "wb.request.registration"
    _description = "E-Billing Request Registraiton List"

    name = fields.Selection([('sale','Sale'),
                             ('auto_account_approval','Account Approval')],
                            )
    sale_id = fields.Many2one("sale.order", "Sale")
    request = fields.Text("Request")
    response = fields.Text("Response")
    state = fields.Selection([('draft', 'Draft'),
                              ('invalid', 'Invalid'),
                              ('done','Done')], default='draft')

    def getProductList(self):
        return [{'id':prd.id, 'name':prd.name} for prd in self.env['product.product'].search([('sale_ok', '=', True)])]

    def getTaxList(self):
        return [{'id': prd.id, 'name': prd.name} for prd in
                self.env['account.tax'].search([('type_tax_use', '=', 'sale')])]

    def getUOMList(self):
        return [{'id': prd.id, 'name': prd.name} for prd in self.env['uom.uom'].search([])]
