import logging
import json
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


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
    active = fields.Boolean("Active", default=True)

    def wbRequestRegisration(self, vals={}):
        _logger.info("wbRequestRegisration Request {} {}".format(self, vals))
        response = {'status':0, 'msg':''}
        create_vals = {'request':'{}'.format(vals), 'state':'invalid'}
        if not vals or type(vals) != type({}):
            response['msg'] = 'No payload found / Invalid Payload.'
            return response
        list_api = ['sale', 'auto_account_approval']

        if vals.get("name") not in list_api:
            response['msg'] = "Invalid api request."
        if type(vals.get("request")) != type({}):
            response['msg'] = "Invalid request."

        if vals.get("name") == "sale":
            rtn_status, rtn_msg = self.wbSaleRequest(vals)
            response['msg'] = rtn_msg
            create_vals['name'] = 'sale'
            if rtn_status:
                create_vals['state'] = 'draft'
                response['status'] = 1
                create_vals['request'] = json.dumps(vals)
        else:
            response['msg'] = 'Invalid name request.'
        create_vals['response'] = '{}'.format(response)
        self.create(create_vals)
        _logger.info("wbRequestRegisration Response {} ".format(response))
        return response

    def wbSaleRequest(self, vals):

        # payload = {'customerid':123, 'ebilling_orderid':'EbillinIDNumber', 'ebilling_ref':'EbillingRefNumber',
        #            'date':'2022-02-16 16:32:48', 'lines':[{'description':'description', 'qty':1, 'price':10.20,
        #                                                    'uom':'erp_uom_id', 'tax':'erp_tax_id',
        #                                                    'product_id':'erp_product_id'}]}

        partner_obj = self.env['res.partner']
        product_obj = self.env['product.product']
        uom_obj = self.env['uom.uom']
        sale_obj = self.env['sale.order']
        saleline_obj = self.env['sale.order.line']
        tax_obj = self.env['account.tax']

        data = ['name','customerid', 'ebilling_ref', 'lines', 'date']
        sub_lines = ['description', 'qty', 'price', 'uom', 'tax', 'product_id']

        if vals.get("request", {}):
            return False, "Invalid request payload."

        for data_key in data:
            if data_key not in vals:
                return False, "Invalid/Missing {} key.".format(data_key)
            if not vals.get(data_key):
                return False, "Empty {} key.".format(data_key)

        if vals.get("customerid"):
            partner = partner_obj.sudo().search([('id', '=', vals.get("customerid"))])
            if not partner.exists():
                return False, "Invalid {} key value.".format(data_key)

        if type(vals.get("lines")) != type([]):
            return False, "Invalid lines key format."

        for sng_line in vals.get("lines", []):
            for sng_key in sng_line:
                if sng_key not in sub_lines:
                    return False, "Invalid/Missing lines.{} key.".format(sng_key)
                if not sng_line.get(sng_key):
                    return False, "Empty line.{} key.".format(sng_key)

        for sng_line in vals.get("lines", []):
            if type(sng_line.get("product_id")) != type(1):
                return False, "Invalid datatype line.product_id key."
            if type(sng_line.get("uom")) != type(1):
                return False, "Invalid datatype line.uom key."
            if type(sng_line.get("tax")) != type(1):
                return False, "Invalid datatype line.tax key."

            if 'uom_obj' in sng_line:
                uom_id = uom_obj.search([('id', '=', sng_line.get("uom"))])
                if not uom_id:
                    return False, "UOM {} not found.".format(sng_line.get("uom"))

            if 'product_id' in sng_line:
                product_id = product_obj.search([('id', '=', sng_line.get("product_id"))])
                if not product_id:
                    return False, "Product {} not found.".format(sng_line.get("product_id"))

            if 'tax' in sng_line:
                tax_id = tax_obj.search([('id', '=', sng_line.get("tax"))])
                if not tax_id:
                    return False, "Tax {} not found.".format(sng_line.get("tax"))
        return True, "Registered successfully."

    def getProductList(self):
        return [{'id':prd.id, 'name':prd.name} for prd in
                self.env['product.product'].search([('sale_ok', '=', True)])]

    def getTaxList(self):
        return [{'id': prd.id, 'name': prd.name} for prd in
                self.env['account.tax'].search([('type_tax_use', '=', 'sale')])]

    def getUOMList(self):
        return [{'id': prd.id, 'name': prd.name} for prd in self.env['uom.uom'].search([])]

    def autoPostPendingEntries(self, special_status=False):
        if special_status:
            self_rec = self
        else:
            self_rec = self.search([('state','=','draft')], order='id', limit=50)
        for rec in self_rec.filtered(lambda lm: lm.state == 'draft'):
            if rec.name == "sale":
                rec.autoPostSaleOrder()

    def autoPostSaleOrder(self):
        sale_obj = self.env['sale.order']
        saleline_obj = self.env['sale.order.line']
        field_obj = self.env['ir.model.fields']

        sale_field_list = field_obj.sudo().search([('model_id.model', '=', 'sale.order')]).mapped("name")
        default_sale_values = sale_obj.sudo().default_get(sale_field_list)

        saleline_field_list = field_obj.sudo().search([('model_id.model', '=', 'sale.order.line')]).mapped("name")

        payload = json.loads(self.request)
        default_sale_values['partner_id'] = payload.get("customerid")
        default_sale_values['date_order'] = payload.get("date")
        sale_lines = []
        for line in payload.get("lines", []):
            context = {'partner_id':payload.get("customerid"),
                        'quantity':payload.get("customerid"),
                        'pricelist':default_sale_values.get("pricelist_id"),
                        'default_product_id': line.get("product_id"),
                        'product_id': line.get("product_id"),
                        # 'uom': line.get("uom"),
                        'company_id': default_sale_values.get("company_id")}
            default_saleline_values = saleline_obj.sudo().with_context(context).default_get(saleline_field_list)
            default_saleline_values['product_id'] = line.get("product_id")
            default_saleline_values['price_unit'] = line.get("price")
            # default_saleline_values['product_uom'] = line.get("uom")
            default_saleline_values['product_uom_qty'] = line.get("product_id")
            sale_lines.append([0, 0, default_saleline_values])
        default_sale_values['order_line'] = sale_lines
        default_sale_values['client_order_ref'] = payload.get("ebilling_ref")
        sale_id = sale_obj.create(default_sale_values)
        sale_id.message_post(
            body=_('Order successfully created by {}'.format(self.create_uid.display_name)),
        )
        self.write({"sale_id": sale_id.id, "state": "done"})
