"""Utils for newsletter"""
from BeautifulSoup import BeautifulSoup
import premailer

from django.contrib.sites.models import Site
from django.core.urlresolvers import reverse
from django.utils.encoding import smart_text

from maja_newsletter.models import Link
from maja_newsletter.settings import USE_PRETTIFY, USE_PREMAILER


def body_insertion(content, insertion, end=False):
    """Insert an HTML content into the body HTML node"""
    if not content.startswith('<body'):
        content = u'<body>%s</body>' % smart_text(content)
    soup = BeautifulSoup(content)
    insertion = BeautifulSoup(insertion)

    if end:
        soup.append(insertion)
    else:
        soup.body.insert(0, insertion)

    if USE_PRETTIFY:
        text = soup.prettify()
    else:
        text = soup.renderContents()
    text = smart_text(text)

    if USE_PREMAILER:
        site = Site.objects.get_current()
        return premailer.transform(smart_text(text), base_url='http://%s' % site.domain)
    else:
        return text


def track_links(content, context):
    """Convert all links in the template for the user
    to track his navigation"""
    if not context.get('uidb36'):
        return content

    soup = BeautifulSoup(content)
    for link_markup in soup('a'):
        if link_markup.get('href') and \
               'no-track' not in link_markup.get('rel', ''):
            link_href = link_markup['href']
            if link_href.startswith("http"):
                link_title = link_markup.get('title', link_href)
                link, created = Link.objects.get_or_create(url=link_href,
                                                           defaults={'title': link_title})
                link_markup['href'] = 'http://%s%s' % (context['domain'], reverse('newsletter_newsletter_tracking_link',
                                                                                  args=[context['newsletter'].slug,
                                                                                        context['uidb36'], context['token'],
                                                                                        link.pk]))
    if USE_PRETTIFY:
        return soup.prettify()
    else:
        return soup.renderContents()
