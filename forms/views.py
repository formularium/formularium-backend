from django.http import HttpResponse

from forms.models import SignatureKey


def pgp_signature_key(request):
    """returns the pgp public signature key of the instance"""
    return HttpResponse(
        SignatureKey.objects.filter(active=True).get().public_key,
        content_type="text/plain",
    )


def home(request):
    """serve 200 at /"""
    return HttpResponse("Hey there!", content_type="text/plain")
