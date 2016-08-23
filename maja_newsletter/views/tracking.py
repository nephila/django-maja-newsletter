"""Views for maja_newsletter Tracking"""
import base64
from urllib import urlencode
from urlparse import urlparse
from urlparse import urlunparse
# For Python < 2.6
from maja_newsletter.utils import DJANGO_1_7

try:
    from urlparse import parse_qs
except ImportError:
    from cgi import parse_qs

from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.template import RequestContext
from django.utils.encoding import smart_str
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required

from maja_newsletter.models import Link
from maja_newsletter.models import Newsletter
from maja_newsletter.utils.tokens import untokenize
from maja_newsletter.models import ContactMailingStatus
from maja_newsletter.settings import USE_UTM_TAGS
from maja_newsletter.settings import TRACKING_IMAGE


def view_newsletter_tracking(request, slug, uidb36, token, format):
    """Track the opening of the newsletter by requesting a blank img"""
    newsletter = get_object_or_404(Newsletter, slug=slug)
    contact = untokenize(uidb36, token)
    ContactMailingStatus.objects.create(newsletter=newsletter,
                                        contact=contact,
                                        status=ContactMailingStatus.OPENED)
    if DJANGO_1_7:
        return HttpResponse(base64.b64decode(TRACKING_IMAGE),
                            mimetype='image/%s' % format)
    else:
        return HttpResponse(base64.b64decode(TRACKING_IMAGE),
                            content_type='image/%s' % format)


def view_newsletter_tracking_link(request, slug, uidb36, token, link_id):
    """Track the opening of a link on the website"""
    newsletter = get_object_or_404(Newsletter, slug=slug)
    contact = untokenize(uidb36, token)
    link = get_object_or_404(Link, pk=link_id)
    ContactMailingStatus.objects.create(newsletter=newsletter,
                                        contact=contact,
                                        status=ContactMailingStatus.LINK_OPENED,
                                        link=link)
    if not USE_UTM_TAGS:
        return HttpResponseRedirect(link.url)

    url_parts = urlparse(link.url)
    query_dict = parse_qs(url_parts.query)
    query_dict.update({'utm_source': 'newsletter_%s' % newsletter.pk,
                       'utm_medium': 'mail',
                       'utm_campaign': smart_str(newsletter.title)})
    url = urlunparse((url_parts.scheme, url_parts.netloc, url_parts.path,
                      url_parts.params, urlencode(query_dict), url_parts.fragment))
    return HttpResponseRedirect(url)


@login_required
def view_newsletter_historic(request, slug):
    """Display the historic of a newsletter"""
    opts = Newsletter._meta
    newsletter = get_object_or_404(Newsletter, slug=slug)

    context = {'title': _('Historic of %s') % newsletter.__unicode__(),
               'original': newsletter,
               'opts': opts,
               'cl': {'opts': opts},
               'object_id': newsletter.pk,
               'app_label': opts.app_label}
    if DJANGO_1_7:
        return render_to_response('newsletter/newsletter_historic.html',
                                  context, context_instance=RequestContext(request))
    else:
        return render_to_response('newsletter/newsletter_historic.html',
                                  RequestContext(request, context))
