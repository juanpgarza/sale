##############################################################################
# For copyright and license notices, see __manifest__.py file in module root
# directory
##############################################################################
from odoo import models, _
from odoo.tools import float_is_zero
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        msg = (
            'Si utiliza un tipo de venta con política de facturación '
            '"Antes de la entrega",entonces cada línea de venta '
            'debe facturarse y pagarse antes de poder confirmar la orden de venta.')
        if any(
            self.sudo().filtered(
                lambda x: x.sale_id.type_id.invoice_policy in ['prepaid', 'prepaid_block_delivery']
                and not x._check_sale_paid())):
            raise UserError(_(msg))
        return super().button_validate()

    def action_assign(self):
        msg = (
            'Si utiliza un tipo de venta con política de facturación '
            '"Antes de la entrega",entonces cada línea de venta '
            'debe facturarse y pagarse antes de poder confirmar la orden de venta.')
        prepaid_unpaid = self.sudo().filtered(
            lambda x: x.sale_id.type_id.invoice_policy ==
            'prepaid' and not x._check_sale_paid())
        if prepaid_unpaid and self._context.get('prepaid_raise'):
            raise UserError(_(msg))
        elif prepaid_unpaid and not self._context.get('prepaid_raise'):
            self -= prepaid_unpaid
            # do not call super if not self because it raise an error
            if not self:
                return True
        return super(StockPicking, self).action_assign()

    def _check_sale_paid(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        invoice_status = self.sale_id.mapped('order_line.invoice_lines.move_id').filtered(lambda x: x.move_type == 'out_invoice' and x.state != 'cancel').mapped('payment_state')
        paid_status = ['paid', 'in_payment', 'reversed']
        if (set(invoice_status) - set(paid_status)) or any(
            not float_is_zero(line.qty_to_invoice, precision_digits=precision) for line in self.sale_id.order_line
        ):
            return False
        return True
