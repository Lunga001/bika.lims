# This file is part of Bika LIMS
#
# Copyright 2011-2016 by it's authors.
# Some rights reserved. See LICENSE.txt, AUTHORS.txt.

from Products.CMFCore.utils import getToolByName
from bika.lims.browser import BrowserView
from Products.Five.browser.pagetemplatefile import ViewPageTemplateFile
from bika.lims import bikaMessageFactory as _
from bika.lims.content.client import IClient
from bika.lims.utils import t
from bika.lims.utils import formatDateQuery, formatDateParms, \
        formatPortalCatalogDateQuery, logged_in_client
from plone import api
from plone.app.layout.globals.interfaces import IViewView
from zope.interface import implements


class Report(BrowserView):
    implements(IViewView)
    template = ViewPageTemplateFile(
        "templates/productivity_analysesperservice.pt")

    def __init__(self, context, request, report=None):
        BrowserView.__init__(self, context, request)
        self.report = report
        self.context = context
        self.request = request

    def __call__(self):
        # get all the data into datalines

        sc = api.portal.get_tool('bika_setup_catalog')
        bc = api.portal.get_tool('bika_analysis_catalog')
        self.report_content = {}
        parms = []
        headings = {}
        headings['header'] = _("Analyses per analysis service")
        headings['subheader'] = _(
            "Number of analyses requested per analysis service")

        query = {'portal_type': 'Analysis'}
        client_title = None
        if 'ClientUID' in self.request.form:
            client_uid = self.request.form['ClientUID']
            query['getClientUID'] = client_uid
            client = api.content.find(object_provides=IClient,UID=client_uid)
            client = client[0] if client else False
            client_title = client.Title
        else:
            client = logged_in_client(self.context)
            if client:
                client_title = client.Title()
                query['getClientUID'] = client.UID()

        if client_title:
            parms.append(
                {'title': _('Client'), 'value': client_title, 'type': 'text'})

        date_query = formatDateQuery(self.context, 'Requested')
        if date_query:
            query['created'] = date_query
            requested = formatDateParms(self.context, 'Requested')
            parms.append(
                {'title': _('Requested'), 'value': requested, 'type': 'text'})

        date_query = formatDateQuery(self.context, 'Published')
        if date_query:
            query['getDatePublished'] = date_query
            published = formatDateParms(self.context, 'Published')
            parms.append(
                {'title': _('Published'), 'value': published, 'type': 'text'})

        workflow = getToolByName(self.context, 'portal_workflow')
        if 'bika_analysis_workflow' in self.request.form:
            query['review_state'] = self.request.form['bika_analysis_workflow']
            review_state = workflow.getTitleForStateOnType(
                self.request.form['bika_analysis_workflow'], 'Analysis')
            parms.append(
                {'title': _('Status'), 'value': review_state, 'type': 'text'})

        if 'bika_cancellation_workflow' in self.request.form:
            query['cancellation_state'] = self.request.form[
                'bika_cancellation_workflow']
            cancellation_state = workflow.getTitleForStateOnType(
                self.request.form['bika_cancellation_workflow'], 'Analysis')
            parms.append({'title': _('Active'), 'value': cancellation_state,
                          'type': 'text'})

        if 'bika_worksheetanalysis_workflow' in self.request.form:
            query['worksheetanalysis_review_state'] = self.request.form[
                'bika_worksheetanalysis_workflow']
            ws_review_state = workflow.getTitleForStateOnType(
                self.request.form['bika_worksheetanalysis_workflow'], 'Analysis')
            parms.append(
                {'title': _('Assigned to worksheet'), 'value': ws_review_state,
                 'type': 'text'})

        # and now lets do the actual report lines
        formats = {'columns': 4,
                   'col_heads': [_('Analysis service'),
                                 _('Number of analyses'),
                                 _('Category'),
                                 _('Category Subtotal'),],
                   'class': '',
        }

        datalines = []
        count_all = 0
        for cat in sc(portal_type="AnalysisCategory",
                      sort_on='sortable_title'):
            dataline = [{'value': cat.Title,
                         'class': 'category_heading',
                         'colspan': 4}, ]
            datalines.append(dataline)

            brains =  sc(portal_type="AnalysisService",
                              getCategoryUID=cat.UID,
                              sort_on='sortable_title')

            sub_total = 0
            count = 0
            for service in brains:
                query['getServiceUID'] = service.UID
                analyses = bc(query)
                count_analyses = len(analyses)
                sub_total += count_analyses

                dataline = []
                dataitem = {'value': service.Title}
                dataline.append(dataitem)

                dataitem = {'value': count_analyses}
                dataline.append(dataitem)

                dataitem = {'value': cat.Title}
                dataline.append(dataitem)

                dataitem = {'value': sub_total}
                dataline.append(dataitem)

                datalines.append(dataline)

                count += 1
                if len(brains) == count:
                    for i in datalines[-count:]:
                        i[-1]['value'] = sub_total
                count_all += count_analyses

        # footer data
        footlines = []
        footline = []
        footitem = {'value': _('Total'),
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

        title = t(headings['header'])
        dates_requested = None
        dates_published = None

        if self.request.get('output_format', '') == 'CSV':
            import csv
            import datetime
            import StringIO

            ## Write the report header rows
            header_output = StringIO.StringIO()
            writer = csv.writer(header_output)
            writer.writerow(['Report', 'Analyses per Service'])
            if 'ClientUID' in self.request.form:
                writer.writerow(['Client', client_title])
            writer.writerow([])

            ## Write the parameters used to create the report
            writer.writerow(['Report parameters:'])
            writer.writerow([])
            date_query = formatDateQuery(self.context, 'Requested')
            if date_query:
                dates_rec = formatPortalCatalogDateQuery(date_query['query'])
                writer.writerow(
                        ['Dates Requested', dates_rec[0], dates_rec[1]])
            date_query = formatDateQuery(self.context, 'Published')
            if date_query:
                dates_pub = formatPortalCatalogDateQuery(date_query['query'])
                writer.writerow(
                        ['Dates Published', dates_pub[0], dates_pub[1]])
            if 'bika_analysis_workflow' in self.request.form:
                review_state = workflow.getTitleForStateOnType(
                    self.request.form['bika_analysis_workflow'], 'Analysis')
                writer.writerow(['Analysis States', review_state])
            if 'bika_cancellation_workflow' in self.request.form:
                cancellation_state = workflow.getTitleForStateOnType(
                    self.request.form['bika_cancellation_workflow'], 'Analysis')
                writer.writerow(['Analysis Active Status', cancellation_state])
            if 'bika_worksheetanalysis_workflow' in self.request.form:
                ws_review_state = \
                    workflow.getTitleForStateOnType(
                        self.request.form['bika_worksheetanalysis_workflow'],
                        'Analysis')
                writer.writerow(['Analysis Worksheet assigned status',
                                 ws_review_state])
            writer.writerow([])

            ## Write any totals or report statistics
            writer.writerow(['Total number of analyses:', len(datalines)])
            writer.writerow([])

            ## Write individual rows to a DictWriter on body_output
            fieldnames = ['Analysis Service',
                          'Analyses',
                          'Category',
                          'Category Subtotal']
            body_output = StringIO.StringIO()
            dw = csv.DictWriter(body_output, extrasaction='ignore',
                                fieldnames=fieldnames)
            dw.writerow(dict((fn, fn) for fn in fieldnames))
            for row in datalines:
                if len(row) == 1:
                    # category heading thingy
                    continue
                dw.writerow({
                    'Analysis Service': row[0]['value'],
                    'Analyses': row[1]['value'],
                    'Category': row[2]['value'],
                    'Category Subtotal': row[3]['value'],
                })
            report_data = header_output.getvalue() + \
                          body_output.getvalue()
            header_output.close()
            body_output.close()

            date = datetime.datetime.now().strftime("%Y%m%d%H%M")
            setheader = self.request.RESPONSE.setHeader
            setheader('Content-Type', 'text/csv')
            setheader(
                "Content-Disposition",
                "attachment;filename=\"analysesperservice_%s.csv\"" % date)
            self.request.RESPONSE.write(report_data)
        else:
            return {'report_title': title,
                    'report_data': self.template()}
