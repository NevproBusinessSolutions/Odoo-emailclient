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

{
    "name" : "Poweremail",
    "version" : "1.0",
    "author" : "Nevpro Business Solutions Pvt. Ltd",
    "website" : "http://www.nevpro.co.in",
    "category" : "Added functionality",
    "depends" : [
        'base',
    ],
    "description": """
The Existing Module of PowerMail Created by "Openlabs Technologies & Consulting (P) LTD" for Version 5.0 trunk has been Modified by "Nevpro Business Solutions Pvt Ltd" for OpenERP 7.0

Power Email - extends the most Power ful open source ERP with email 
which powers the world today.

Features:

1. Multiple Email Accounts
2. Company & Personal Email accounts
3. Security
4. Email Folders (Inbox.Outbox.Drafts etc)
5. Sending of Mails via SMTP (SMTP SSL also supported)
6. Reception of Mails (IMAP & POP3) With SSL & Folders for IMAP supported
7. Simple one point Template designer which automatically updates system. 
    No extra config req.
8. Automatic Email feature on workflow stages

NOTE: This Version was for trunk, we have modified it to make this module supportable for OpenERP 7.0.
(it was using netsvc library, that is deprecated now, We are using logging instead of netsvc, and we changed all the netsvc instance with logging instance.)
    """,
    "init_xml": [
        'scheduler_data.xml'
    ],
    "update_xml": [
        'security/security.xml',
        'security/ir.model.access.csv',
        'workflow.xml',
        'core_view.xml',
        'template_view.xml',
        'send_wizard.xml',
        'mailbox_view.xml',
        'serveraction_view.xml',
    ],
    "installable": True,
    "active": False,
}
