from odoo import fields, models, api
import requests
import json


class Sales(models.Model):
    _inherit = "sale.order"

    is_new_customer = fields.Boolean("Is New Customer?", copy=False)
    is_integration_done = fields.Boolean("Is Integration Done?", copy=False)
    request_data = fields.Text("E-billing Request", copy=False)
    response_data = fields.Text("E-billing Response", copy=False)

    def action_confirm(self):
        rtn = super(Sales, self).action_confirm()
        if self.is_new_customer:
            self.postEBillingInvoice()
        return rtn

    def postEBillingInvoice(self):
        wb_token = self.env['ir.config_parameter'].sudo().get_param(
            'wb_ebilling_integration.wb_ebilling_token') or ''
        wb_url = self.env['ir.config_parameter'].sudo().get_param(
            'wb_ebilling_integration.wb_ebilling_url') or ''
        if wb_token and wb_url:
            payload = {
                "erpid": "{}".format(self.partner_id.id),
                "order_erpid": "{}".format(self.id),
                "firstname": "",
                "lastname": "{}".format(self.partner_id.name),
                "username": "{}".format(self.env.user.partner_id.name),
                "company": "{}".format(self.company_id.name),
                "address": "{} {}".format(self.partner_id.street, self.partner_id.street2),
                "city": "{}".format(self.partner_id.city),
                "state": "{}".format(self.partner_id.state_id.name if self.partner_id.state_id else ''),
                "email": "{}".format(self.partner_id.email),
                "phone": "{}".format(self.partner_id.phone),
                "mobile": "{}".format(self.partner_id.mobile),
                "pck": "",
                "ip": "",
                "company_id": "{}".format(self.company_id.id),
                "orderno": "{}".format(self.name),
                "salesperson": "{}".format(self.user_id.partner_id.name),
                "salesemail": "{}".format(self.user_id.partner_id.email),
                "orderdate": "{}".format(self.date_order or ''),
                "tot_amt": "{}".format(self.amount_total),
            }
            indx = 1
            for line in self.order_line:
                payload.update({"item{}".format(indx): "{}".format(line.name),
                                "item{}_cost".format(indx): "{}".format(line.price_total),
                                "item{}_qty".format(indx): "{}".format(line.product_uom_qty)})
                indx += 1
            headers = {
                'Authorization': 'Bearer {}'.format(wb_token),
                'Content-Type': 'application/json'
            }
            self.request_data = "{}".format(json.dumps(payload))
            rst = requests.request("POST", wb_url, headers=headers, data="{}".format(json.dumps(payload)))
            self.response_data = "{}".format(rst.text)
            self.is_integration_done = False
            if rst.text:
                response_data = json.loads(rst.text)
                if response_data.get("STATUS", 0) == 1 and "Success:" in response_data.get("MSG", ""):
                    self.is_integration_done = True


class ResConfig(models.TransientModel):
    _inherit = "res.config.settings"

    wb_ebilling_token = fields.Char("E-Billing Token")
    wb_ebilling_url = fields.Char("E-Billing URL")

    def set_values(self):
        super(ResConfig, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('wb_ebilling_integration.wb_ebilling_token', self.wb_ebilling_token)
        self.env['ir.config_parameter'].sudo().set_param('wb_ebilling_integration.wb_ebilling_url', self.wb_ebilling_url)

    @api.model
    def get_values(self):
        values = super(ResConfig, self).get_values()
        values['wb_ebilling_token'] = self.env['ir.config_parameter'].sudo().get_param('wb_ebilling_integration.wb_ebilling_token') or ''
        values['wb_ebilling_url'] = self.env['ir.config_parameter'].sudo().get_param('wb_ebilling_integration.wb_ebilling_url') or ''
        return values
