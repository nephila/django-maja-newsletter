"""Views for emencia.django.newsletter Mailing List"""
from django.template import RequestContext
from django.shortcuts import get_object_or_404
from django.shortcuts import render_to_response

from emencia.django.newsletter import settings as emencia_settings
from emencia.django.newsletter.utils.tokens import untokenize
from emencia.django.newsletter.models import Newsletter
from emencia.django.newsletter.models import MailingList
from emencia.django.newsletter.models import ContactMailingStatus


def view_mailinglist_unsubscribe(request, slug, uidb36, token):
    """Unsubscribe a contact to one or all mailing lists"""
    newsletter = get_object_or_404(Newsletter, slug=slug)
    contact = untokenize(uidb36, token)
    if emencia_settings.UNSUBSCRIBE_ALL:
        mailing_lists = MailingList.objects.all()
        contact.subscriber = False
        contact.save()
    else:
        mailing_lists = [newsletter.mailing_list]

    unsubscribed = 0
    already_unsubscribed = False

    if request.POST.get('email'):
        for mailing_list in mailing_lists:
            already_unsubscribed = contact in mailing_list.unsubscribers.all()

            if not already_unsubscribed:
                mailing_list.unsubscribers.add(contact)
                mailing_list.save()
            unsubscribed += 1

    if unsubscribed > 0:
        already_unsubscribed = True
        ContactMailingStatus.objects.create(newsletter=newsletter, contact=contact,
                                            status=ContactMailingStatus.UNSUBSCRIPTION)

    return render_to_response('newsletter/mailing_list_unsubscribe.html',
                              {'email': contact.email,'unsubscribed_count':unsubscribed,
                               'already_unsubscribed': already_unsubscribed},
                              context_instance=RequestContext(request))


def view_mailinglist_subscribe(request, form_class, mailing_list_id=None):
    """
    A simple view that shows a form for subscription
    for a mailing list(s).
    """
    subscribed = False
    mailing_list = None
    if mailing_list_id:
        mailing_list = get_object_or_404(MailingList, id=mailing_list_id)

    if request.POST and not subscribed:
        form = form_class(request.POST)
        if form.is_valid():
            form.save(mailing_list)
            subscribed = True
    else:
        form = form_class()

    return render_to_response('newsletter/mailing_list_subscribe.html',
                              {'subscribed': subscribed,
                               'mailing_list': mailing_list,
                               'form': form},
                              context_instance=RequestContext(request))
