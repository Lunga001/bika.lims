# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from Products.CMFCore.utils import getToolByName
from bika.lims.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from bika.lims import bikaMessageFactory as _
from bika.lims.utils import t
from bika.lims.utils import formatDateQuery, formatDateParms, logged_in_client
from plone.app.layout.globals.interfaces import IViewView
from zope.interface import implements


class Report(BrowserView):
    implements(IViewView)
    template = ViewPageTemplateFile("templates/report_out.pt")

    def __init__(self, context, request, report=None):
        self.report = report
        BrowserView.__init__(self, context, request)

    def __call__(self):
        # get all the data into datalines

        pc = getToolByName(self.context, 'portal_catalog')
        rc = getToolByName(self.context, 'reference_catalog')
        self.report_content = {}
        parms = []
        headings = {}
        headings['header'] = _("Attachments")
        headings['subheader'] = _(
            "The attachments linked to analysis requests and analyses")

        count_all = 0
        query = {'portal_type': 'Attachment'}
        if 'ClientUID' in self.request.form:
            client_uid = self.request.form['ClientUID']
            query['getClientUID'] = client_uid
            client = rc.lookupObject(client_uid)
            client_title = client.Title()
        else:
            client = logged_in_client(self.context)
            if client:
                client_title = client.Title()
                query['getClientUID'] = client.UID()
            else:
                client_title = 'All'
        parms.append(
            {'title': _('Client'),
             'value': client_title,
             'type': 'text'})

        date_query = formatDateQuery(self.context, 'Loaded')
        if date_query:
            query['getDateLoaded'] = date_query
            loaded = formatDateParms(self.context, 'Loaded')
            parms.append(
                {'title': _('Loaded'),
                 'value': loaded,
                 'type': 'text'})

        # and now lets do the actual report lines
        formats = {'columns': 6,
                   'col_heads': [_('Request'),
                                 _('File'),
                                 _('Attachment type'),
                                 _('Content type'),
                                 _('Size'),
                                 _('Loaded'),
                   ],
                   'class': '',
        }

        datalines = []
        attachments = pc(query)
        for a_proxy in attachments:
            attachment = a_proxy.getObject()
            attachment_file = attachment.getAttachmentFile()
            icon = attachment_file.icon
            filename = attachment_file.filename
            filesize = attachment_file.get_size()
            filesize = filesize / 1024
            sizeunit = "Kb"
            if filesize > 1024:
                filesize = filesize / 1024
                sizeunit = "Mb"
            dateloaded = attachment.getDateLoaded()
            dataline = []
            dataitem = {'value': attachment.getTextTitle()}
            dataline.append(dataitem)
            dataitem = {'value': filename,
                        'img_before': icon}
            dataline.append(dataitem)
            dataitem = {
            'value': attachment.getAttachmentType().Title() if attachment.getAttachmentType() else ''}
            dataline.append(dataitem)
            dataitem = {
            'value': self.context.lookupMime(attachment_file.getContentType())}
            dataline.append(dataitem)
            dataitem = {'value': '%s%s' % (filesize, sizeunit)}
            dataline.append(dataitem)
            dataitem = {'value': self.ulocalized_time(dateloaded)}
            dataline.append(dataitem)

            datalines.append(dataline)

            count_all += 1

        # footer data
        footlines = []
        footline = []
        footitem = {'value': _('Total'),
                    'colspan': 5,
                    'class': 'total_label'}
        footline.append(footitem)
        footitem = {'value': count_all}
        footline.append(footitem)
        footlines.append(footline)

        self.report_content = {
            'headings': headings,
            'parms': parms,
            'formats': formats,
            'datalines': datalines,
            'footings': footlines}

        if self.request.get('output_format', '') == 'CSV':
            import csv
            import StringIO
            import datetime

            fieldnames = [
                _('Request'),
                _('File'),
                _('Attachment type'),
                _('Content type'),
                _('Size'),
                _('Loaded'),
            ]
            ## Write the report header rows
            header_output = StringIO.StringIO()
            writer = csv.writer(header_output)
            writer.writerow(['Report', 'Attachments'])
            if 'ClientUID' in self.request.form:
                writer.writerow(['Client', client_title])
            writer.writerow([])

            ## Write the parameters used to create the report
            writer.writerow(['Report parameters:'])
            writer.writerow([])
            date_query = formatDateQuery(self.context, 'Loaded')
            if date_query:
                string_dates = []
                for i in date_query['query']:
                    string_dates.append(
                            datetime.datetime.strptime(
                                i, '%Y-%m-%d %H:%M').strftime('%Y-%m-%d'))
                dates_requested = ' - '.join(string_dates)
                writer.writerow(['Date Loaded', dates_requested])
            writer.writerow([])

            ## Write any totals or report statistics
            writer.writerow(['Total number of analyses:', len(datalines)])
            writer.writerow([])

            ## Write individual rows to a DictWriter on body_output
            body_output = StringIO.StringIO()
            dw = csv.DictWriter(body_output, extrasaction='ignore',
                                fieldnames=fieldnames)
            dw.writerow(dict((fn, fn) for fn in fieldnames))
            for row in datalines:
                dw.writerow({'Request': row[0]['value'],
                             'File': row[1]['value'],
                             'Attachment type': row[2]['value'],
                             'Content type': row[3]['value'],
                             'Size': row[4]['value'],
                             'Loaded': row[5]['value']})
            report_data = header_output.getvalue() + \
                          body_output.getvalue()
            header_output.close()
            body_output.close()
            date = datetime.datetime.now().strftime("%Y%m%d%H%M")
            setheader = self.request.RESPONSE.setHeader
            setheader('Content-Type', 'text/csv')
            setheader("Content-Disposition",
                      "attachment;filename=\"analysesattachments_%s.csv\"" % date)
            self.request.RESPONSE.write(report_data)
        else:
            return {'report_title': t(headings['header']),
                    'report_data': self.template()}
