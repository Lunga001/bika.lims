# -*- coding: utf-8 -*-
from zope import schema

from bika.lims import messagefactory as _
from bika.lims.interfaces.samplepoint import ISamplePoint
from bika.lims.interfaces.sampletype import ISampleType
from plone.app.vocabularies.catalog import CatalogSource
from plone.supermodel import model
from z3c.relationfield import RelationChoice

class ISample(model.Schema):
    """Represents the original sample.
    """

    sample_type = RelationChoice(
        title=_(u"Sample Type"),
        source=CatalogSource(object_provides=ISampleType.__identifier__),
        required=True,
    )

    sample_point = RelationChoice(
        title=_(u"Sample Point"),
        source=CatalogSource(object_provides=ISamplePoint.__identifier__),
        required=False,
    )

    client_sample_id = schema.TextLine(
        title=_(u"Client Sample ID"),
        description=_(u"The ID assigned to the sample by the client"),
        required=False,
    )

    date_sampled = schema.Datetime(
        title=_(u"Date Sampled"),
        required=False,
    )
