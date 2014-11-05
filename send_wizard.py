#########################################################################
#                                                                       #
# Copyright (C) 2010-2011 Openlabs Technologies & Consulting (P) LTD    #
# Copyright (C) 2009  Sharoon Thomas                                    #
#                                                                       #
#This program is free software: you can redistribute it and/or modify   #
#it under the terms of the GNU General Public License as published by   #
#the Free Software Foundation, either version 3 of the License, or      #
#(at your option) any later version.                                    #
#                                                                       #
#This program is distributed in the hope that it will be useful,        #
#but WITHOUT ANY WARRANTY; without even the implied warranty of         #
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          #
#GNU General Public License for more details.                           #
#                                                                       #
#You should have received a copy of the GNU General Public License      #
#along with this program.  If not, see <http://www.gnu.org/licenses/>.  #
#########################################################################
import base64
import time

import netsvc
import logging
import tools
from tools.translate import _
from osv import osv, fields
from template import get_value


class poweremail_send_wizard(osv.osv_memory):
    _name = 'poweremail.send.wizard'
    _description = 'This is the wizard for sending mail'
    _rec_name = "subject"

    def _get_accounts(self, cr, uid, context=None):
        if context is None:
            context = {}

        template = self._get_template(cr, uid, context)
        if not template:
            return []

        #logger = netsvc.Logger()

        if template.enforce_from_account:
            return [(template.enforce_from_account.id, '%s (%s)' % (template.enforce_from_account.name, template.enforce_from_account.email_id))]
        else:
            accounts_id = self.pool.get('poweremail.core_accounts').search(cr,uid,[('company','=','no'),('user','=',uid)], context=context)
            if accounts_id:
                accounts = self.pool.get('poweremail.core_accounts').browse(cr,uid,accounts_id, context)
                return [(r.id,r.name + " (" + r.email_id + ")") for r in accounts]
            else:
                logging.getLogger(_("Power Email")).info(_("No personal email accounts are configured for you. \nEither ask admin to enforce an account for this template or get yourself a personal power email account."))
                #logger.notifyChannel(_("Power Email"), netsvc.LOG_ERROR, _("No personal email accounts are configured for you. \nEither ask admin to enforce an account for this template or get yourself a personal power email account."))
                raise osv.except_osv(_("Power Email"),_("No personal email accounts are configured for you. \nEither ask admin to enforce an account for this template or get yourself a personal power email account."))

    def get_value(self, cursor, user, template, message, context=None, id=None):
        """Gets the value of the message parsed with the content of object id (or the first 'src_rec_ids' if id is not given)"""
        if not message:
            return ''
        if not id:
            id = context['src_rec_ids'][0]
        return get_value(cursor, user, id, message, template, context)

    def _get_template(self, cr, uid, context=None):
        if context is None:
            context = {}
        if not 'template' in context and not 'template_id' in context:
            return None
        template_obj = self.pool.get('poweremail.templates')
        if 'template_id' in context.keys():
            template_ids = template_obj.search(cr, uid, [('id','=',context['template_id'])], context=context)
        elif 'template' in context.keys():
            # Old versions of poweremail used the name of the template. This caused
            # problems when the user changed the name of the template, but we keep the code
            # for compatibility with those versions.
            template_ids = template_obj.search(cr, uid, [('name','=',context['template'])], context=context)
        if not template_ids:
            return None

        template = template_obj.browse(cr, uid, template_ids[0], context)

        lang = self.get_value(cr, uid, template, template.lang, context)
        if lang:
            # Use translated template if necessary
            ctx = context.copy()
            ctx['lang'] = lang
            template = template_obj.browse(cr, uid, template.id, ctx)
        return template

    def _get_template_value(self, cr, uid, field, context=None):
        template = self._get_template(cr, uid, context)
        if not template:
            return False
        if len(context['src_rec_ids']) > 1: # Multiple Mail: Gets original template values for multiple email change
            return getattr(template, field)
        else: # Simple Mail: Gets computed template values
            return self.get_value(cr, uid, template, getattr(template, field), context)

    _columns = {
        'state':fields.selection([
                        ('single','Simple Mail Wizard Step 1'),
                        ('multi','Multiple Mail Wizard Step 1'),
                        ('send_type','Send Type'),
                        ('done','Wizard Complete')
                                  ],'Status',readonly=True),
        'ref_template':fields.many2one('poweremail.templates','Template',readonly=True),
        'rel_model':fields.many2one('ir.model','Model',readonly=True),
        'rel_model_ref':fields.integer('Referred Document',readonly=True),
        'from':fields.selection(_get_accounts,'From Account',select=True),
        'to':fields.char('To',size=250,required=True),
        'cc':fields.char('CC',size=250,),
        'bcc':fields.char('BCC',size=250,),
        'subject':fields.char('Subject',size=200),
        'body_text':fields.text('Body',),
        'body_html':fields.text('Body',),
        'report':fields.char('Report File Name',size=100,),
        'signature':fields.boolean('Attach my signature to mail'),
        #'filename':fields.text('File Name'),
        'requested':fields.integer('No of requested Mails',readonly=True),
        'generated':fields.integer('No of generated Mails',readonly=True),
        'full_success':fields.boolean('Complete Success',readonly=True),
        'attachment_ids': fields.many2many('ir.attachment','send_wizard_attachment_rel', 'wizard_id', 'attachment_id', 'Attachments'),
        'single_email': fields.boolean("Single email", help="Check it if you want to send a single email for several records (the optional attachment will be generated as a single file for all these records). If you don't check it, an email with its optional attachment will be send for each record."),
    }

    _defaults = {
        'state': lambda self,cr,uid,ctx: len(ctx['src_rec_ids']) > 1 and 'send_type' or 'single',
        'rel_model': lambda self,cr,uid,ctx: self.pool.get('ir.model').search(cr,uid,[('model','=',ctx['src_model'])],context=ctx)[0],
        'rel_model_ref': lambda self,cr,uid,ctx: ctx['active_id'],
        'to': lambda self,cr,uid,ctx: self._get_template_value(cr, uid, 'def_to', ctx),
        'cc': lambda self,cr,uid,ctx: self._get_template_value(cr, uid, 'def_cc', ctx),
        'bcc': lambda self,cr,uid,ctx: self._get_template_value(cr, uid, 'def_bcc', ctx),
        'subject':lambda self,cr,uid,ctx: self._get_template_value(cr, uid, 'def_subject', ctx),
        'body_text':lambda self,cr,uid,ctx: self._get_template_value(cr, uid, 'def_body_text', ctx),
        'body_html':lambda self,cr,uid,ctx: self._get_template_value(cr, uid, 'def_body_html', ctx),
        'report': lambda self,cr,uid,ctx: self._get_template_value(cr, uid, 'file_name', ctx),
        'signature': lambda self,cr,uid,ctx: self._get_template(cr, uid, ctx).use_sign,
        'ref_template':lambda self,cr,uid,ctx: self._get_template(cr, uid, ctx).id,
        'requested':lambda self,cr,uid,ctx: len(ctx['src_rec_ids']),
        'full_success': lambda *a: False,
        'single_email':lambda self,cr,uid,ctx: self._get_template_value(cr, uid, 'single_email', ctx),
    }

    #def fields_get(self, cr, uid, fields=None, context=None, read_access=True):
    #    result = super(poweremail_send_wizard, self).fields_get(cr, uid, fields, context, read_access)
    #    if 'attachment_ids' in result:
    #        result['attachment_ids']['domain'] = [('res_model','=','purchase.order'),('res_id','=',context['active_id'])]
    #    return result
    def fields_get(self, cr, uid, fields=None, context=None, write_access=True):
        result = super(poweremail_send_wizard, self).fields_get(cr, uid, fields, context, write_access)
        if 'attachment_ids' in result and 'src_model' in context:
            result['attachment_ids']['domain'] = [('res_model','=',context['src_model']),('res_id','=',context['active_id'])]
        return result

    def compute_second_step(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        wizard = self.browse(cr, uid, ids[0], context)
        if not wizard.single_email:
            return self.write(cr, uid, ids, {'state': 'multi'}, context)
        # We send a single email for several records. We compute the values from the first record
        ctx = context.copy()
        ctx['src_rec_ids'] = ctx['src_rec_ids'][:1]
        values = {
            'to': self._get_template_value(cr, uid, 'def_to', ctx),
            'cc': self._get_template_value(cr, uid, 'def_cc', ctx),
            'bcc': self._get_template_value(cr, uid, 'def_bcc', ctx),
            'subject': self._get_template_value(cr, uid, 'def_subject', ctx),
            'body_text': self._get_template_value(cr, uid, 'def_body_text', ctx),
            'body_html': self._get_template_value(cr, uid, 'def_body_html', ctx),
            'report': self._get_template_value(cr, uid, 'file_name', ctx),
            'signature': self._get_template(cr, uid, ctx).use_sign,
            'ref_template': self._get_template(cr, uid, ctx).id,
            'state': 'single',
        }
        return self.write(cr, uid, ids, values, context = context)

    def sav_to_drafts(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        mailid = self.save_to_mailbox(cr, uid, ids, context)
        if self.pool.get('poweremail.mailbox').write(cr, uid, mailid, {'folder':'drafts'}, context):
            return {'type':'ir.actions.act_window_close' }

    def send_mail(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        mailid = self.save_to_mailbox(cr, uid, ids, context)
        if self.pool.get('poweremail.mailbox').write(cr, uid, mailid, {'folder':'outbox'}, context):
            return {'type':'ir.actions.act_window_close' }

    def get_generated(self, cr, uid, ids=None, context=None):
        if ids is None:
            ids = []
        if context is None:
            context = {}
        #logger = netsvc.Logger()
        if context['src_rec_ids'] and len(context['src_rec_ids'])>1:
            #Means there are multiple items selected for email.
            mail_ids = self.save_to_mailbox(cr, uid, ids, context)
            if mail_ids:
                self.pool.get('poweremail.mailbox').write(cr, uid, mail_ids, {'folder':'outbox'}, context)
                #logger.notifyChannel(_("Power Email"), netsvc.LOG_INFO, _("Emails for multiple items saved in outbox."))
                logging.getLogger(_("Power Email")).info(_("Emails for multiple items saved in outbox."))
                self.write(cr, uid, ids, {
                    'generated':len(mail_ids),
                    'state':'done'
                }, context)
            else:
                raise osv.except_osv(_("Power Email"),_("Email sending failed for one or more objects."))
        return True

    def save_to_mailbox(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        def get_end_value(id, value):
            if len(context['src_rec_ids']) > 1: # Multiple Mail: Gets value from the template
                return self.get_value(cr, uid, template, value, context, id)
            else:
                return value

        mail_ids = []
        template = self._get_template(cr, uid, context)
        screen_vals = self.read(cr, uid, ids[0], [], context)
        if isinstance(screen_vals, list): # Solves a bug in v5.0.16
            screen_vals = screen_vals[0]
        report_record_ids = context['src_rec_ids'][:]
        if screen_vals['single_email'] and len(context['src_rec_ids']) > 1:
            # We send a single email for several records
            context['src_rec_ids'] = context['src_rec_ids'][:1]

        for id in context['src_rec_ids']:
            accounts = self.pool.get('poweremail.core_accounts').read(cr, uid, screen_vals['from'], context=context)
            vals = {
                'pem_from': tools.ustr(accounts['name']) + "<" + tools.ustr(accounts['email_id']) + ">",
                'pem_to': get_end_value(id, screen_vals['to']),
                'pem_cc': get_end_value(id, screen_vals['cc']),
                'pem_bcc': get_end_value(id, screen_vals['bcc']),
                'pem_subject': get_end_value(id, screen_vals['subject']),
                'pem_body_text': get_end_value(id, screen_vals['body_text']),
                'pem_body_html': get_end_value(id, screen_vals['body_html']),
                'pem_account_id': screen_vals['from'],
                'state':'na',
                'mail_type':'multipart/alternative' #Options:'multipart/mixed','multipart/alternative','text/plain','text/html'
            }
            if screen_vals['signature']:
                signature = self.pool.get('res.users').read(cr, uid, uid, ['signature'], context)['signature']
                if signature:
                    vals['pem_body_text'] = tools.ustr(vals['pem_body_text'] or '') + '\n--\n' + signature
                    vals['pem_body_html'] = tools.ustr(vals['pem_body_html'] or '') + signature

            attachment_ids = []

            #Create partly the mail and later update attachments
            mail_id = self.pool.get('poweremail.mailbox').create(cr, uid, vals, context)
            mail_ids.append(mail_id)
            if template.report_template:
                reportname = 'report.' + self.pool.get('ir.actions.report.xml').read(cr, uid, template.report_template.id, ['report_name'], context)['report_name']
                data = {}
                data['model'] = self.pool.get('ir.model').browse(cr, uid, screen_vals['rel_model'], context).model

                # Ensure report is rendered using template's language. If not found, user's launguage is used.
                ctx = context.copy()
                if template.lang:
                    ctx['lang'] = self.get_value(cr, uid, template, template.lang, context, id)
                    lang = self.get_value(cr, uid, template, template.lang, context, id)
                    if len(self.pool.get('res.lang').search(cr, uid, [('name','=',lang)], context = context)):
                        ctx['lang'] = lang
                if not ctx.get('lang', False) or ctx['lang'] == 'False':
                    ctx['lang'] = self.pool.get('res.users').read(cr, uid, uid, ['context_lang'], context)['context_lang']
                service = netsvc.LocalService(reportname)
                if screen_vals['single_email'] and len(report_record_ids) > 1:
                    # The optional attachment will be generated as a single file for all these records
                    (result, format) = service.create(cr, uid, report_record_ids, data, ctx)
                else:
                    (result, format) = service.create(cr, uid, [id], data, ctx)
                attachment_id = self.pool.get('ir.attachment').create(cr, uid, {
                    'name': _('%s (Email Attachment)') % tools.ustr(vals['pem_subject']),
                    'datas': base64.b64encode(result),
                    'datas_fname': tools.ustr(get_end_value(id, screen_vals['report']) or _('Report')) + "." + format,
                    'description': vals['pem_body_text'] or _("No Description"),
                    'res_model': 'poweremail.mailbox',
                    'res_id': mail_id
                }, context)
                attachment_ids.append( attachment_id )

            # Add document attachments
            for attachment_id in screen_vals.get('attachment_ids',[]):
                new_id = self.pool.get('ir.attachment').copy(cr, uid, attachment_id, {
                    'res_model': 'poweremail.mailbox',
                    'res_id': mail_id,
                }, context)
                attachment_ids.append( new_id )

            if attachment_ids:
                self.pool.get('poweremail.mailbox').write(cr, uid, mail_id, {
                    'pem_attachments_ids': [[6, 0, attachment_ids]],
                    'mail_type': 'multipart/mixed'
                }, context)

            # Create a partner event
            if template.partner_event and self._get_template_value(cr, uid, 'partner_event', context):
                name = vals['pem_subject']
                if isinstance(name, str):
                    name = unicode(name, 'utf-8')
                if len(name) > 64:
                    name = name[:61] + '...'

                model = res_id = False
                if template.report_template and self.pool.get('res.request.link').search(cr, uid, [('object','=',data['model'])], context=context):
                    model = data['model']
                    res_id = id
                elif attachment_ids and self.pool.get('res.request.link').search(cr, uid, [('object','=','ir.attachment')], context=context):
                    model = 'ir.attachment'
                    res_id = attachment_ids[0]

                cr.execute("SELECT state from ir_module_module where state='installed' and name = 'mail_gateway'")
                mail_gateway = cr.fetchall()
                if mail_gateway:
                    values = {
                        'history': True,
                        'name': name,
                        'date': time.strftime('%Y-%m-%d %H:%M:%S'),
                        'user_id': uid,
                        'email_from': vals['pem_from'] or None,
                        'email_to': vals['pem_to'] or None,
                        'email_cc': vals['pem_cc'] or None,
                        'email_bcc': vals['pem_bcc'] or None,
                        'message_id': mail_id,
                        'description': vals['pem_body_text'] and vals['pem_body_text'] or vals['pem_body_html'],
                        'partner_id': self.get_value(cr, uid, template, template.partner_event, context, id),
                        'model': model,
                        'res_id': res_id,
                    }
                    self.pool.get('mailgate.message').create(cr, uid, values, context)
        return mail_ids

poweremail_send_wizard()

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
