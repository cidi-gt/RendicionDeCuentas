from .forms import CustomContactForm
from django.core.urlresolvers import reverse

def contact_form_context_processor(request):
    return {
        'form': CustomContactForm(request),
        'form_feedback': reverse("visualizaciones:contact_form")
    }

