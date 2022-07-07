# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Weblearns E-Billing Integration',
    'version' : '1.1',
    'summary': 'E-Billing Integration',
    'author': 'Weblearns',
    'sequence': 10,
    'description': "E-Billing Integration",
    'category': 'sale',
    'website': 'https://onlineweblearns.blogspot.com',
    'depends' : ['sale'],
    'data': [
        'view/sale_view.xml',
        'view/res_config_view.xml'
    ],
    'installable': True,
    'license': 'LGPL-3',
}
